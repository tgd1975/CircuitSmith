#!/usr/bin/env python3
"""
Regenerate circuit artefacts for the pre-commit hook (TASK-038).

When a `.circuit.yml` or a component profile is staged, this script
re-runs the full pipeline for each affected target and writes the
four canonical artefacts back to `docs/builders/wiring/<target>/`:

  - `main-circuit.svg` — schematic
  - `main-circuit.layout.yml` — placement (preserved across runs)
  - `main-circuit.meta.yml` — provenance + rubric
  - `erc-report.md` — ERC findings catalog
  - `bom.md` / `bom.csv` — bill of materials
  - `main-circuit.net` — KiCad netlist

After regeneration, the script `git add`s any artefact that changed so
the commit picks them up. Reports the targets it touched on stdout and
exits non-zero if the pipeline halts (ERC error, rubric failure, …) —
the hook surfaces that as a commit abort.

A short-circuit cache makes the no-op case under 5 s on the shipped
circuits: each target's `main-circuit.meta.yml` carries a
`provenance.fingerprint` line that hashes the circuit body plus every
component profile that contributed to the registry. A match means the
inputs are byte-identical to the previous run and the artefacts on
disk are current; the renderer is skipped.

CLI:

  scripts/regenerate_circuit_artefacts.py [--targets esp32 nrf52840]

The pre-commit hook calls this script with no arguments; the optional
`--targets` flag is for manual invocation against a subset.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML

from circuitsmith.export.bom_exporter import export as export_bom
from circuitsmith.export.netlist_exporter import export as export_netlist
from circuitsmith.netgraph import NetGraph
from circuitsmith.renderer import RenderError, render
from circuitsmith.schema.registry import load_profiles

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
WIRING_DIR = REPO_ROOT / "docs" / "builders" / "wiring"
COMPONENTS_DIR = REPO_ROOT / "src" / "circuitsmith" / "components"
TARGETS = ("esp32", "nrf52840")
FINGERPRINT_PREFIX = "fingerprint:"


def _compute_fingerprint(circuit_path: Path) -> str:
    """Hash the circuit source plus every component profile file.

    Any edit to a profile (e.g. adding a new variant) flips the
    fingerprint for every circuit, forcing regen — even if the
    circuit's own YAML did not change.
    """
    h = hashlib.sha256()
    h.update(circuit_path.read_bytes())
    for profile_file in sorted(COMPONENTS_DIR.rglob("*.py")):
        h.update(b"\x00")
        h.update(profile_file.name.encode("utf-8"))
        h.update(b"\x00")
        h.update(profile_file.read_bytes())
    return h.hexdigest()[:16]


def _read_existing_fingerprint(meta_path: Path) -> str | None:
    if not meta_path.exists():
        return None
    for line in meta_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(FINGERPRINT_PREFIX):
            return line[len(FINGERPRINT_PREFIX) :].strip()
    return None


def _write_fingerprint(meta_path: Path, fingerprint: str) -> None:
    """Append `fingerprint: <hash>` under `provenance:` in the meta yaml.

    The meta sidecar is emitted by the renderer without this field; we
    add it after the fact rather than threading a new arg through the
    pipeline. The line is recognisable to `_read_existing_fingerprint`
    on the next run.
    """
    text = meta_path.read_text(encoding="utf-8")
    line = f"  {FINGERPRINT_PREFIX} {fingerprint}\n"
    if FINGERPRINT_PREFIX in text:
        # Replace the existing line.
        out_lines = []
        for raw in text.splitlines(keepends=True):
            if FINGERPRINT_PREFIX in raw and raw.lstrip().startswith(FINGERPRINT_PREFIX):
                out_lines.append(line)
            else:
                out_lines.append(raw)
        meta_path.write_text("".join(out_lines), encoding="utf-8")
        return
    if "provenance:" in text:
        # Insert the new line as the last entry under `provenance:`.
        if not text.endswith("\n"):
            text += "\n"
        meta_path.write_text(text + line, encoding="utf-8")
        return
    meta_path.write_text(text + f"provenance:\n{line}", encoding="utf-8")


def regenerate_target(target: str) -> tuple[bool, list[Path], str | None]:
    """Regenerate one target. Returns (skipped, written_paths, error)."""
    circuit_path = DATA_DIR / f"{target}.circuit.yml"
    if not circuit_path.exists():
        return False, [], f"target {target}: no circuit at {circuit_path}"

    wiring_dir = WIRING_DIR / target
    svg_path = wiring_dir / "main-circuit.svg"
    layout_path = wiring_dir / "main-circuit.layout.yml"
    meta_path = wiring_dir / "main-circuit.meta.yml"
    erc_path = wiring_dir / "erc-report.md"

    fingerprint = _compute_fingerprint(circuit_path)
    if _read_existing_fingerprint(meta_path) == fingerprint:
        return True, [], None

    try:
        render(
            circuit_path=circuit_path,
            layout_path=layout_path if layout_path.exists() else None,
            out_svg=svg_path,
            out_layout=layout_path,
            out_meta=meta_path,
            out_erc_report=erc_path,
        )
    except RenderError as exc:
        return False, [], f"target {target}: {exc.stage} — {exc.summary}"

    yaml = YAML(typ="safe")
    circuit = yaml.load(circuit_path.read_text(encoding="utf-8"))
    profiles = load_profiles()

    bom_md, bom_csv = export_bom(circuit, profiles)
    (wiring_dir / "bom.md").write_text(bom_md, encoding="utf-8")
    (wiring_dir / "bom.csv").write_text(bom_csv, encoding="utf-8")

    graph = NetGraph.from_yaml_dict(circuit)
    netlist = export_netlist(circuit, graph, profiles, circuit_path)
    (wiring_dir / "main-circuit.net").write_text(netlist, encoding="utf-8")

    _write_fingerprint(meta_path, fingerprint)

    written = [
        svg_path,
        layout_path,
        meta_path,
        erc_path,
        wiring_dir / "bom.md",
        wiring_dir / "bom.csv",
        wiring_dir / "main-circuit.net",
    ]
    return False, written, None


def _git_add(paths: list[Path]) -> None:
    if not paths:
        return
    rels = [str(p.relative_to(REPO_ROOT)) for p in paths]
    subprocess.run(["git", "add", "--"] + rels, check=True, cwd=REPO_ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate circuit artefacts for the pre-commit hook (TASK-038).",
    )
    parser.add_argument(
        "--targets",
        nargs="*",
        default=list(TARGETS),
        help="Restrict to a subset of shipped targets.",
    )
    parser.add_argument(
        "--no-stage",
        action="store_true",
        help="Do not git-add regenerated artefacts (manual-run convenience).",
    )
    args = parser.parse_args(argv)

    any_fail = False
    for target in args.targets:
        skipped, written, error = regenerate_target(target)
        if error is not None:
            sys.stderr.write(f"FAIL {target}: {error}\n")
            any_fail = True
            continue
        if skipped:
            sys.stdout.write(f"skip {target} (fingerprint match)\n")
            continue
        sys.stdout.write(f"regen {target}: {len(written)} artefact(s)\n")
        if not args.no_stage:
            _git_add(written)

    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
