#!/usr/bin/env python3
"""
Phase 2b trigger observer (TASK-058).

Aggregates `provenance.escalations` from every committed `meta.yml` at
HEAD and emits:

  - JSON report on stdout (build-artifact friendly).
  - Markdown summary on stderr (release-notes friendly).
  - Exit 0 unconditionally — this script *observes*, it does not gate.
    The gate logic lives in `scripts/release_snapshot.py` (TASK-059).

The script walks files via `git ls-files` so only committed metadata
counts; transient working-tree edits do not move the trigger.

Usage:

    python scripts/check_phase2b_trigger.py
    python scripts/check_phase2b_trigger.py --repo-root /path/to/repo

The contract for `provenance.escalations` and the category enum are
documented in `docs/layout.md`. The schema is at
`src/circuitsmith/schema/meta.schema.json`.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Categories the §5.3 canonical-slot table can retire by a *single rule
# addition*. Other categories are topology / rendering problems that
# Phase 2b's AI placer cannot help with — counting them in the trigger
# would burn cycles without changing outcomes.
ADDRESSABLE_CATEGORY = "no-canonical-rule"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2b trigger observer")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="repository root (default: CWD)",
    )
    args = parser.parse_args(argv)

    meta_paths = _committed_meta_paths(args.repo_root)
    report = _aggregate(meta_paths)

    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True))
    sys.stdout.write("\n")

    sys.stderr.write(_markdown_summary(report))
    return 0


def _committed_meta_paths(repo_root: Path) -> list[Path]:
    """List every committed `*.meta.yml` (via `git ls-files`)."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "*.meta.yml"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        sys.stderr.write(f"check_phase2b_trigger: `git ls-files` failed: {exc}\n")
        raise SystemExit(2) from None
    return [repo_root / line for line in out.stdout.splitlines() if line.strip()]


def _aggregate(meta_paths: list[Path]) -> dict[str, Any]:
    from ruamel.yaml import YAML
    yaml = YAML(typ="safe")

    by_category: defaultdict[str, int] = defaultdict(int)
    circuits_with_escalations: set[str] = set()
    total = 0

    for path in meta_paths:
        try:
            with open(path) as fh:
                doc = yaml.load(fh)
        except Exception as exc:
            sys.stderr.write(f"check_phase2b_trigger: cannot parse {path}: {exc}\n")
            raise SystemExit(2) from None
        if not isinstance(doc, dict):
            sys.stderr.write(
                f"check_phase2b_trigger: {path} is not a YAML mapping\n"
            )
            raise SystemExit(2)
        provenance = doc.get("provenance", {})
        if not isinstance(provenance, dict):
            sys.stderr.write(
                f"check_phase2b_trigger: {path} has non-mapping provenance block\n"
            )
            raise SystemExit(2)
        escalations = provenance.get("escalations", [])
        if not isinstance(escalations, list):
            sys.stderr.write(
                f"check_phase2b_trigger: {path}.provenance.escalations is not a list\n"
            )
            raise SystemExit(2)
        for entry in escalations:
            if not isinstance(entry, dict) or "category" not in entry:
                sys.stderr.write(
                    f"check_phase2b_trigger: {path} has malformed escalation: {entry!r}\n"
                )
                raise SystemExit(2)
            by_category[entry["category"]] += 1
            total += 1
            circuits_with_escalations.add(path.name)

    non_addressable_count = sum(
        count for cat, count in by_category.items() if cat != ADDRESSABLE_CATEGORY
    )
    no_rule_count = by_category.get(ADDRESSABLE_CATEGORY, 0)

    return {
        "total_escalations": total,
        "by_category": dict(by_category),
        "non_addressable_count": non_addressable_count,
        "no_rule_count": no_rule_count,
        "circuits_with_escalations": sorted(circuits_with_escalations),
    }


def _markdown_summary(report: dict[str, Any]) -> str:
    total = report["total_escalations"]
    if total == 0:
        return (
            "## Phase 2b trigger — clean\n\n"
            "No `provenance.escalations` entries across committed `meta.yml` files. "
            "Phase 2b remains contingent.\n"
        )
    lines = [
        "## Phase 2b trigger — escalations present",
        "",
        f"- Total escalations: **{total}**",
        f"- Addressable (`no-canonical-rule`): **{report['no_rule_count']}**",
        f"- Non-addressable (topology / rendering): **{report['non_addressable_count']}**",
        "",
        "Counts by category:",
        "",
    ]
    for cat in sorted(report["by_category"]):
        lines.append(f"- `{cat}`: {report['by_category'][cat]}")
    lines.append("")
    lines.append("Affected circuits:")
    for circuit in report["circuits_with_escalations"]:
        lines.append(f"- `{circuit}`")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
