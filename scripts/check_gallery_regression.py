#!/usr/bin/env python3
"""
Check tutorial + gallery rendered artefacts for drift (TASK-101).

For every `<name>.circuit.yml` under `docs/users/tutorial/` and
`docs/users/examples/`, this script re-runs the renderer and diffs
the output against the committed `<name>.svg`. If any committed
artefact (SVG, .layout.yml, .meta.yml, .erc-report.md) drifts, the
script exits non-zero with a `diff -u` of the changed file(s).

Two operating modes:

  --check       (default) — read-only diff. Exit 0 if every
                committed artefact matches the regenerated output.
  --rebaseline  — write the regenerated artefacts in place of the
                committed ones. Use when the drift is intentional
                (renderer bump, deliberate circuit edit) and review
                the resulting diff before committing.

Circuits without a committed SVG are *skipped* with a one-line
note. The EPIC-012 gallery's `circuit.yml` entries that are blocked
on IDEA-008 / IDEA-009 ship without an SVG and stay skipped until
their kernel / component-profile prerequisites land.

The script never exercises the AI placer — it always passes
`--no-ai` semantics, matching CI's deterministic-render policy per
ADR-0002.
"""
from __future__ import annotations

import argparse
import difflib
import sys
import tempfile
from pathlib import Path

from circuitsmith.renderer import RenderError, render

SCRIPT_REPO_ROOT = Path(__file__).resolve().parent.parent
# REPO_ROOT picks the *invocation* cwd when it contains the expected
# `docs/users/` shape (so tests can stage a temp gallery and run the
# script against it), falling back to the script-anchored path for
# normal runs from anywhere. The script never escapes the chosen root.
_CWD = Path.cwd()
if (_CWD / "docs" / "users").exists():
    REPO_ROOT = _CWD
else:
    REPO_ROOT = SCRIPT_REPO_ROOT
TUTORIAL_DIR = REPO_ROOT / "docs" / "users" / "tutorial"
EXAMPLES_DIR = REPO_ROOT / "docs" / "users" / "examples"

# Per-circuit artefact suffix conventions used by the tutorial /
# gallery. The tutorial step files share a base name with their
# circuit (`01-minimal-circuit.circuit.yml` →
# `01-minimal-circuit.svg`); the gallery uses `circuit.yml` →
# `<dirname>.svg` (`voltage-divider/circuit.yml` →
# `voltage-divider/voltage-divider.svg`). Both are handled.


def _gather_circuits() -> list[Path]:
    paths: list[Path] = []
    if TUTORIAL_DIR.exists():
        paths.extend(sorted(TUTORIAL_DIR.glob("*.circuit.yml")))
    if EXAMPLES_DIR.exists():
        for child in sorted(EXAMPLES_DIR.iterdir()):
            if not child.is_dir():
                continue
            circuit = child / "circuit.yml"
            if circuit.exists():
                paths.append(circuit)
    return paths


def _artefact_paths(circuit_path: Path) -> dict[str, Path]:
    """Return the {kind: path} mapping for a circuit's artefacts.

    Tutorial form (`<base>.circuit.yml`):
        <base>.svg, <base>.layout.yml, <base>.meta.yml,
        <base>.erc-report.md
    Gallery form (`<dir>/circuit.yml`):
        <dir>/<dirname>.svg, <dir>/layout.yml, <dir>/meta.yml,
        <dir>/erc-report.md
    """
    if circuit_path.name == "circuit.yml":
        # Gallery form.
        d = circuit_path.parent
        stem = d.name
        return {
            "svg":    d / f"{stem}.svg",
            "layout": d / "layout.yml",
            "meta":   d / "meta.yml",
            "erc":    d / "erc-report.md",
        }
    # Tutorial form: drop the `.circuit.yml` suffix.
    base_name = circuit_path.name[: -len(".circuit.yml")]
    d = circuit_path.parent
    return {
        "svg":    d / f"{base_name}.svg",
        "layout": d / f"{base_name}.layout.yml",
        "meta":   d / f"{base_name}.meta.yml",
        "erc":    d / f"{base_name}.erc-report.md",
    }


def _diff(label: str, expected: str, actual: str) -> str:
    return "".join(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=f"committed:{label}",
            tofile=f"regenerated:{label}",
            n=3,
        )
    )


def _normalise_meta(text: str) -> str:
    """Strip the `sources:` block from meta.yml before diffing.

    The renderer records the input `circuit:` and output `layout:`
    paths verbatim in the meta sidecar. Those paths reflect the
    runner's invocation, not the circuit content, so drift in
    that block is not interesting for regression checking — every
    test temp dir would otherwise produce a false positive.

    The block is a contiguous run of indented lines after a top-level
    `sources:` key; we drop it and keep the rest of the file.
    """
    out: list[str] = []
    in_sources = False
    for line in text.splitlines(keepends=True):
        if in_sources:
            # End of block: a non-blank line that does not start with
            # whitespace.
            if line.strip() and line[0] not in (" ", "\t"):
                in_sources = False
            else:
                continue
        if not in_sources and line.rstrip("\n") == "sources:":
            in_sources = True
            continue
        out.append(line)
    return "".join(out)


def _check_one(circuit_path: Path, rebaseline: bool) -> tuple[bool, str]:
    """Render circuit and compare against committed artefacts.

    Returns (ok, message). On rebaseline the regenerated artefacts
    overwrite the committed ones; the function returns (True, '…')
    after the write.

    The renderer records its input paths verbatim into `meta.yml`,
    so we invoke with relative paths from `REPO_ROOT` (matching how
    a user types them on the command line). Output paths use the
    relative form too, so a temp-dir output writes `out/...` paths
    we then strip before diffing.
    """
    paths = _artefact_paths(circuit_path)
    rel_circuit = circuit_path.relative_to(REPO_ROOT)

    if not paths["svg"].exists():
        return True, f"skip {rel_circuit} (no committed SVG)"

    with tempfile.TemporaryDirectory(prefix="cs-gallery-check-", dir=REPO_ROOT) as tmpdir:
        tmp = Path(tmpdir)
        # Output paths inside the temp dir, but with names that mirror
        # the committed artefact layout so `meta.yml`'s `sources:` lines
        # reference the committed paths verbatim. We redirect the output
        # to the temp dir by passing an absolute path; the renderer's
        # meta-sources only echo `circuit:` and `layout:` (input paths),
        # not the output paths, so the temp directory does not leak into
        # the diffed content.
        out_paths = {
            "svg":    tmp / "out.svg",
            "layout": tmp / "out.layout.yml",
            "meta":   tmp / "out.meta.yml",
            "erc":    tmp / "out.erc-report.md",
        }
        try:
            render(
                circuit_path=rel_circuit,
                layout_path=paths["layout"].relative_to(REPO_ROOT) if paths["layout"].exists() else None,
                out_svg=out_paths["svg"],
                out_layout=out_paths["layout"],
                out_meta=out_paths["meta"],
                out_erc_report=out_paths["erc"],
            )
        except RenderError as exc:
            return False, f"FAIL {rel_circuit}: renderer aborted at {exc.stage} — {exc.summary}"

        diffs: list[str] = []
        for kind, dst in paths.items():
            regen = out_paths[kind]
            if not regen.exists():
                continue
            regen_bytes = regen.read_bytes()
            if rebaseline:
                dst.write_bytes(regen_bytes)
                continue
            if not dst.exists():
                diffs.append(f"missing committed {kind}: {dst.relative_to(REPO_ROOT)}")
                continue
            committed_bytes = dst.read_bytes()
            if committed_bytes == regen_bytes:
                continue
            # Try text diff; fall back to a byte-mismatch summary.
            try:
                committed = committed_bytes.decode("utf-8")
                regenerated = regen_bytes.decode("utf-8")
            except UnicodeDecodeError:
                diffs.append(
                    f"{dst.relative_to(REPO_ROOT)}: binary mismatch "
                    f"(committed {len(committed_bytes)} B, regenerated {len(regen_bytes)} B)"
                )
                continue
            if kind == "meta":
                # See `_normalise_meta`: the `sources:` block records
                # invocation paths that drift per-runner without
                # changing the circuit content.
                committed = _normalise_meta(committed)
                regenerated = _normalise_meta(regenerated)
                if committed == regenerated:
                    continue
            diffs.append(_diff(str(dst.relative_to(REPO_ROOT)), committed, regenerated))

        if rebaseline:
            return True, f"rebase {rel_circuit}"
        if diffs:
            joined = "\n".join(d for d in diffs if d.strip())
            return False, f"FAIL {rel_circuit}:\n{joined}"
        return True, f"ok {rel_circuit}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check tutorial + gallery rendered artefacts for drift (TASK-101).",
    )
    parser.add_argument(
        "--rebaseline",
        action="store_true",
        help="Overwrite committed artefacts with regenerated output. Review the diff before committing.",
    )
    args = parser.parse_args(argv)

    circuits = _gather_circuits()
    if not circuits:
        sys.stdout.write("no circuits found under docs/users/{tutorial,examples}/\n")
        return 0

    any_fail = False
    for circuit_path in circuits:
        ok, msg = _check_one(circuit_path, args.rebaseline)
        if ok:
            sys.stdout.write(msg + "\n")
        else:
            sys.stderr.write(msg + "\n")
            any_fail = True

    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
