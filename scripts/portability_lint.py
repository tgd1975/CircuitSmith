#!/usr/bin/env python3
"""Portability lint for ``.claude/skills/circuit/``.

Enforces the portability contract from
``docs/developers/ideas/archived/idea-001.skill-packaging.md`` and
ADR-0007 (`docs/developers/adr/0007-skill-directory-is-the-library.md`):
files inside the skill directory must be path-agnostic so the
Phase 7 extraction (EPIC-006 / TASK-043..045) stays mechanical
rather than turning into a port.

Usage:
    python scripts/portability_lint.py <skill_dir>

Exits 0 if clean. Exits 1 with a list of findings if not. On an empty
or missing ``<skill_dir>`` the script is a no-op (exits 0) — the lint
is meant to be in place *before* skill code arrives, not after.

Allow-list (escape hatch for genuine exceptions):
    A file named ``.portability-allow.txt`` at the root of
    ``<skill_dir>`` can carry exceptions, one per line, in the form::

        <relative-path>:<pattern-substring>:<reason>

    The reason is free text and exists to make the exception
    auditable. Lines starting with ``#`` are comments. An exception
    matches a finding when its ``<relative-path>`` equals the
    finding's path AND its ``<pattern-substring>`` appears in the
    finding's message text.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

# Files the lint inspects. Binaries and other formats are skipped.
TEXT_EXTENSIONS = {
    ".py", ".md", ".json", ".yml", ".yaml", ".toml", ".txt",
    ".sh", ".bash", ".zsh", ".ts", ".js", ".mjs", ".cjs",
}

# Pattern table. Each entry: (regex, message, docs_exception)
#
#   - regex: compiled pattern searched per-line.
#   - message: human-readable description embedded in findings.
#   - docs_exception: when True, skip matches in files whose relative
#     path under ``<skill_dir>`` starts with ``docs/``. Used for
#     sibling-project names that are fine to mention in narrative docs
#     but not in code.
PATTERNS: list[tuple[re.Pattern[str], str, bool]] = [
    (re.compile(r"/home/[a-zA-Z0-9_-]+"),
     "absolute path (Linux/macOS home)", False),
    (re.compile(r"\bC:\\\\[^\s\"']+"),
     "absolute path (Windows)", False),
    (re.compile(r"~/Dokumente"),
     "user-home path", False),
    (re.compile(r"^\s*from\s+scripts\."),
     "import of project-side `scripts.` module", False),
    (re.compile(r"^\s*from\s+data\."),
     "import of project-side `data.` module", False),
    (re.compile(r"\bimport\s+scripts\."),
     "import of project-side `scripts.` module", False),
    (re.compile(r"docs/builders/"),
     "project-specific data path `docs/builders/`", False),
    (re.compile(r"(?<![a-zA-Z0-9_/-])data/[a-zA-Z]"),
     "project-specific data path `data/...`", False),
    (re.compile(r"\bCircuitSmith\b"),
     "host-project name `CircuitSmith`", False),
    (re.compile(r"\bAwesomeStudioPedal\b"),
     "sibling project name `AwesomeStudioPedal` (allowed under docs/)", True),
    (re.compile(r"\bPartsLedger\b"),
     "sibling project name `PartsLedger` (allowed under docs/)", True),
]


def load_allow(allow_file: Path) -> list[tuple[str, str]]:
    """Read the allow-list file and return a list of (path, pattern) tuples.

    Missing files yield an empty list; malformed lines are skipped.
    """
    if not allow_file.exists():
        return []
    out: list[tuple[str, str]] = []
    for raw in allow_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":", 2)
        if len(parts) < 2:
            continue
        rel_path = parts[0].strip()
        pattern_sub = parts[1].strip()
        if rel_path and pattern_sub:
            out.append((rel_path, pattern_sub))
    return out


def is_allowed(rel_path: str, finding: str,
               allow: list[tuple[str, str]]) -> bool:
    for ap, sub in allow:
        if ap == rel_path and sub in finding:
            return True
    return False


def walk_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        if p.name.startswith("."):
            continue
        if p.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        yield p


def lint(root: Path) -> list[str]:
    if not root.exists() or not root.is_dir():
        return []
    allow = load_allow(root / ".portability-allow.txt")
    findings: list[str] = []
    for path in walk_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for rx, msg, docs_exception in PATTERNS:
                if docs_exception and rel.startswith("docs/"):
                    continue
                if rx.search(line):
                    finding = f"{rel}:{lineno}: {msg}"
                    if not is_allowed(rel, finding, allow):
                        findings.append(finding)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint the circuit-skill directory for portability "
                    "contract violations.",
    )
    parser.add_argument(
        "skill_dir",
        help="path to the skill directory to lint "
             "(e.g. .claude/skills/circuit)",
    )
    args = parser.parse_args()
    root = Path(args.skill_dir).resolve()
    findings = lint(root)
    if findings:
        sys.stderr.write(
            f"portability-lint: {len(findings)} finding(s) in {root}:\n"
        )
        for f in findings:
            sys.stderr.write(f"  {f}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
