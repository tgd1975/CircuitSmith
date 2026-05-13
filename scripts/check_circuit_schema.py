#!/usr/bin/env python3
"""
Schema-validation gate for ``.circuit.yml`` files (TASK-052 / EPIC-008).

Two modes:

- **pre-commit mode** (default): inspect ``git diff --cached`` for staged
  ``.circuit.yml`` paths and validate each one. Exit 0 with no output when
  nothing is staged. Exit 1 on any validation failure with structured
  per-finding lines.
- **CI / batch mode** (``--all``): validate every ``*.circuit.yml`` under
  ``data/`` (plus any explicit paths passed as positional args). Useful
  in CI to catch the case where the local hook was bypassed.

The validator itself is ``circuitsmith.schema.validate_file`` — the same
function the renderer calls at run time. This script is the early-cheap
gate; the renderer's own check is defence-in-depth for code paths that
did not go through a commit.

Output format per failure (one line per finding):

    <file>:<json-pointer>: <message>

where ``<json-pointer>`` is the location field from the validator's
``Finding``. The format is line-oriented so editors that auto-jump to
``file:line: msg`` patterns can be wired up if desired (they cannot map
the JSON pointer to a line number, but they can at least open the
file).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from circuitsmith.schema import validate_file

REPO_ROOT = Path(__file__).resolve().parent.parent


def _staged_circuit_yml() -> list[Path]:
    """Return staged ``.circuit.yml`` paths from ``git diff --cached``.

    ``--diff-filter=ACM`` matches the convention used elsewhere in
    ``scripts/pre-commit`` (Added / Copied / Modified — skip deletes).
    Returns an empty list if not in a git work tree, so the script is
    safe to call from inert sandbox environments.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.endswith(".circuit.yml"):
            paths.append(REPO_ROOT / line)
    return paths


def _all_circuit_yml() -> list[Path]:
    """Return every committed ``.circuit.yml`` under ``data/`` and ``tests/``."""
    return sorted(
        list((REPO_ROOT / "data").glob("*.circuit.yml"))
        + list((REPO_ROOT / "tests" / "fixtures").rglob("*.circuit.yml"))
    )


def validate_paths(paths: list[Path]) -> list[str]:
    """Return a list of formatted error lines (empty == all valid).

    Each entry is ``<file>:<json-pointer>: <message>``. Files that don't
    exist on disk are reported as a single line each; YAML parse errors
    bubble up as a single line with the parser message.
    """
    errors: list[str] = []
    for path in paths:
        rel = path.relative_to(REPO_ROOT) if path.is_absolute() else path
        if not path.exists():
            errors.append(f"{rel}: <file>: file is staged but missing from working tree")
            continue
        try:
            findings = validate_file(path)
        except Exception as exc:  # noqa: BLE001 — YAML or registry error
            errors.append(f"{rel}: <parse>: {exc.__class__.__name__}: {exc}")
            continue
        for finding in findings:
            if finding.severity != "error":
                continue
            location = finding.location or "<root>"
            errors.append(f"{rel}:{location}: {finding.message}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else "validate .circuit.yml"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Explicit paths to validate (overrides staged / --all detection).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate every committed .circuit.yml under data/ and tests/fixtures/.",
    )
    args = parser.parse_args(argv)

    if args.paths:
        targets = [p if p.is_absolute() else REPO_ROOT / p for p in args.paths]
    elif args.all:
        targets = _all_circuit_yml()
    else:
        targets = _staged_circuit_yml()

    if not targets:
        # No staged .circuit.yml — pre-commit short-circuits silently.
        return 0

    errors = validate_paths(targets)
    if errors:
        sys.stderr.write("Schema validation failed for staged .circuit.yml file(s):\n")
        for line in errors:
            sys.stderr.write(f"  {line}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
