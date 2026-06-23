#!/usr/bin/env python3
"""
Test-plan staleness gate (TASK-091, EPIC-011).

Keeps the deliberate test plan under ``docs/developers/testing/`` honest
against the actual test surface. Two failure modes, both exit non-zero:

  1. **Missing from plan** — a ``tests/**/test_*.py`` file exists with no
     reference anywhere in the plan. Fix: add it to the relevant chapter
     and the matrix.
  2. **Dangling reference** — the plan names a ``tests/`` or
     ``scripts/tests/`` file that no longer exists. Fix: remove or
     repoint the reference.

References are read from fenced ``pytest`` code blocks in the plan's
``*.md`` files — the unambiguous form chosen in TASK-091 over parsing the
human-facing matrix table (regex over markdown tables is a maintenance
burden). Every chapter lists its covering files in such a block; this
script is the guard that the union stays complete.

CI-only by design: walking every test file is too slow for the
pre-commit budget (well under a second per file, per COMMIT_POLICY.md).
Invoked from ``.github/workflows/ci.yml``.

Exit 0 on a complete, non-dangling plan; 1 otherwise.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# A plan reference we hold to the "must exist" contract: a repo-relative
# path under tests/ or scripts/tests/ ending in .py.
_TEST_PATH_RE = re.compile(r"^(?:tests|scripts/tests)/[\w./-]+\.py$")
# Opening fence of a referenced-tests block: ```pytest (info string).
_PYTEST_FENCE_RE = re.compile(r"^```pytest\s*$")
_ANY_FENCE_RE = re.compile(r"^```")


def _test_files(root: Path) -> set[str]:
    """Every product test file, as repo-relative posix paths."""
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        return set()
    return {
        p.relative_to(root).as_posix()
        for p in tests_dir.rglob("test_*.py")
    }


def _referenced_paths(root: Path) -> set[str]:
    """Test-file paths named inside ```pytest fences across the plan."""
    plan_dir = root / "docs" / "developers" / "testing"
    referenced: set[str] = set()
    if not plan_dir.is_dir():
        return referenced
    for md in sorted(plan_dir.glob("*.md")):
        in_block = False
        for raw in md.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not in_block:
                if _PYTEST_FENCE_RE.match(line):
                    in_block = True
                continue
            # inside a pytest block
            if _ANY_FENCE_RE.match(line):
                in_block = False
                continue
            if line:
                referenced.add(line)
    return referenced


def check(root: Path) -> tuple[list[str], list[str]]:
    """Return (missing_from_plan, dangling_references)."""
    test_files = _test_files(root)
    referenced = _referenced_paths(root)

    missing = sorted(test_files - referenced)
    dangling = sorted(
        r for r in referenced
        if _TEST_PATH_RE.match(r) and not (root / r).exists()
    )
    return missing, dangling


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Flag test files missing from the plan, or plan "
        "references to test files that no longer exist (TASK-091).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repo root to check (default: the script's repo root)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()

    missing, dangling = check(root)
    if not missing and not dangling:
        sys.stderr.write(
            "test-plan staleness gate OK: every tests/ file is in the "
            "plan and every plan reference resolves.\n"
        )
        return 0

    sys.stderr.write("test-plan staleness gate FAILED:\n")
    for path in missing:
        sys.stderr.write(
            f"  - missing from plan: {path}\n"
            "      add an entry to the matrix and the relevant chapter's "
            "```pytest block in docs/developers/testing/.\n"
        )
    for path in dangling:
        sys.stderr.write(
            f"  - dangling reference: {path}\n"
            "      the plan names this file but it does not exist; remove "
            "or repoint the reference.\n"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
