#!/usr/bin/env python3
"""
ERC-report staleness + error-gate for CI (TASK-029).

For each shipped target, re-runs the renderer's ERC stage and compares
the produced erc-report.md against the committed copy under
`docs/builders/wiring/<target>/erc-report.md`. Fails the build if:

  1. The committed report is stale (does not match the freshly-rendered
     report byte-for-byte after a date-line normalisation).
  2. The ERC stage produces any ERROR-level finding on either target.

The script is invoked both from CI (.github/workflows/ci.yml) and from
scripts/pre-commit. It exits 0 on success, non-zero on any failure.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

from circuitsmith.erc_engine import run as run_erc
from circuitsmith.erc_report import render_report
from circuitsmith.netgraph import NetGraph
from circuitsmith.schema.registry import load_profiles

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
WIRING_DIR = REPO_ROOT / "docs" / "builders" / "wiring"
TARGETS = ("esp32", "nrf52840")

# The header carries today's date; normalise both sides so a staleness
# check passes when the only diff is the auto-stamp.
_DATE_LINE_RE = re.compile(r"^(# ERC Report — .* — )\d{4}-\d{2}-\d{2}$", re.MULTILINE)


def _normalise_dates(text: str) -> str:
    return _DATE_LINE_RE.sub(r"\1<DATE>", text)


def check_target(target: str) -> list[str]:
    """Return a list of error strings; empty list = pass."""
    errors: list[str] = []
    circuit_path = DATA_DIR / f"{target}.circuit.yml"
    report_path = WIRING_DIR / target / "erc-report.md"

    if not circuit_path.exists():
        return [f"target {target}: no circuit at {circuit_path}"]
    if not report_path.exists():
        return [f"target {target}: no committed erc-report at {report_path}"]

    yaml = YAML(typ="safe")
    circuit = yaml.load(circuit_path.read_text(encoding="utf-8"))
    graph = NetGraph.from_yaml_dict(circuit)
    profiles = load_profiles()

    findings = run_erc(graph, circuit, profiles=profiles)

    # Gate 2: ERROR-level findings fail CI regardless of report freshness.
    err_findings = [f for f in findings if f.severity == "error"]
    for f in err_findings:
        errors.append(
            f"target {target}: ERC error [{f.check}] on {f.ref}.{f.pin} "
            f"net={f.net!r}: {f.message}"
        )

    # Gate 1: staleness — the committed report must match the freshly
    # produced one (modulo the date-stamp line).
    fresh = render_report(
        findings,
        title=str(circuit.get("meta", {}).get("title", target)),
        target=target,
    )
    committed = report_path.read_text(encoding="utf-8")
    if _normalise_dates(fresh) != _normalise_dates(committed):
        errors.append(
            f"target {target}: erc-report.md is stale. "
            f"Re-run `python -m circuitsmith.renderer --circuit {circuit_path} "
            f"--out {report_path.parent}/main-circuit.svg "
            f"--out-erc-report {report_path}` and re-commit."
        )
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="ERC report staleness + error gate")
    parser.add_argument("--target", action="append", default=None,
                        help="restrict to a single target (default: all shipped)")
    args = parser.parse_args(argv)
    targets = args.target or TARGETS

    all_errors: list[str] = []
    for tgt in targets:
        all_errors.extend(check_target(tgt))
    if all_errors:
        sys.stderr.write("ERC report staleness / error gate FAILED:\n")
        for line in all_errors:
            sys.stderr.write(f"  - {line}\n")
        return 1
    sys.stderr.write(f"ERC report gate OK for targets: {', '.join(targets)}.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
