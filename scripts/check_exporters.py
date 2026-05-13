#!/usr/bin/env python3
"""
Exporter staleness guard for CI (TASK-035).

For each shipped target, re-runs the BOM and netlist exporters and
compares the produced artefacts against the committed copies under
`docs/builders/wiring/<target>/`. Fails the build if any of the three
artefacts is stale:

  - `bom.md`           — Markdown BOM table.
  - `bom.csv`          — KiCad importer-friendly CSV.
  - `main-circuit.net` — KiCad 7.x intermediate netlist.

Companion to `check_erc_reports.py` (TASK-029); the two scripts run
side-by-side in CI so a regenerator drift is caught at PR time.

The netlist's `(date ...)` field is normalised before diffing — it
reflects the source `.circuit.yml`'s git last-modified date, which is
already deterministic across machines, but normalising defends against
the rare case where a contributor has the .circuit.yml uncommitted
locally and the script falls back to filesystem mtime.

Exits 0 on success, non-zero on any drift.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

from circuitsmith.export.bom_exporter import export as export_bom
from circuitsmith.export.netlist_exporter import export as export_netlist
from circuitsmith.netgraph import NetGraph
from circuitsmith.schema.registry import load_profiles

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
WIRING_DIR = REPO_ROOT / "docs" / "builders" / "wiring"
TARGETS = ("esp32", "nrf52840")

# Normalise the netlist's `(date "YYYY-MM-DD")` line — it depends on the
# source's git-mtime, which is normally stable but can drift if a
# contributor renders against an uncommitted .circuit.yml.
_NET_DATE_RE = re.compile(r'^(\s*\(date ")\d{4}-\d{2}-\d{2}("\))$', re.MULTILINE)


def _normalise_net_date(text: str) -> str:
    return _NET_DATE_RE.sub(r"\1<DATE>\2", text)


def check_target(target: str) -> list[str]:
    """Return a list of error strings; empty list = pass."""
    errors: list[str] = []
    circuit_path = DATA_DIR / f"{target}.circuit.yml"
    wiring_dir = WIRING_DIR / target

    if not circuit_path.exists():
        return [f"target {target}: no circuit at {circuit_path}"]

    yaml = YAML(typ="safe")
    circuit = yaml.load(circuit_path.read_text(encoding="utf-8"))
    profiles = load_profiles()

    # BOM (Markdown + CSV) — does not consume NetGraph.
    fresh_bom_md, fresh_bom_csv = export_bom(circuit, profiles)
    errors.extend(_diff(wiring_dir / "bom.md", fresh_bom_md, target, "bom.md"))
    errors.extend(_diff(wiring_dir / "bom.csv", fresh_bom_csv, target, "bom.csv"))

    # Netlist — walks NetGraph.
    graph = NetGraph.from_yaml_dict(circuit)
    fresh_net = export_netlist(circuit, graph, profiles, circuit_path)
    errors.extend(_diff(
        wiring_dir / "main-circuit.net",
        fresh_net,
        target,
        "main-circuit.net",
        normaliser=_normalise_net_date,
    ))
    return errors


def _diff(
    committed_path: Path,
    fresh: str,
    target: str,
    artefact: str,
    *,
    normaliser=None,
) -> list[str]:
    if not committed_path.exists():
        return [f"target {target}: no committed {artefact} at {committed_path}"]
    committed = committed_path.read_text(encoding="utf-8")
    if normaliser is not None:
        if normaliser(fresh) != normaliser(committed):
            return [_drift_message(target, artefact)]
        return []
    if fresh != committed:
        return [_drift_message(target, artefact)]
    return []


def _drift_message(target: str, artefact: str) -> str:
    return (
        f"target {target}: {artefact} is stale. "
        f"Re-run `python -m circuitsmith.export` (or the renderer "
        f"once the pipeline integration lands) for `{target}` and re-commit."
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="BOM + netlist staleness gate")
    parser.add_argument("--target", action="append", default=None,
                        help="restrict to a single target (default: all shipped)")
    args = parser.parse_args(argv)
    targets = args.target or TARGETS

    all_errors: list[str] = []
    for tgt in targets:
        all_errors.extend(check_target(tgt))
    if all_errors:
        sys.stderr.write("Exporter staleness gate FAILED:\n")
        for line in all_errors:
            sys.stderr.write(f"  - {line}\n")
        return 1
    sys.stderr.write(f"Exporter staleness gate OK for targets: {', '.join(targets)}.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
