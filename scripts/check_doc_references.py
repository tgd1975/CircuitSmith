#!/usr/bin/env python3
"""
Doc cross-reference gate (TASK-105, EPIC-013).

Validates the cross-references in the repo's Markdown against the
filesystem and the task / idea / ADR indexes. Five reference classes:

  1. **Relative links** (default) — every ``[text](path)`` whose target is
     local resolves to a file (anchors stripped, code fences skipped).
     Deterministic and the source of most link rot.
  2. **TASK / EPIC / IDEA refs** (``--check-ids``) — every ``TASK-NNN`` /
     ``EPIC-NNN`` / ``IDEA-NNN`` named in prose resolves to a file under
     ``docs/developers/tasks/`` or ``docs/developers/ideas/``.
  3. **Code-path mentions** (``--check-paths``) — backtick repo paths
     (``src/``, ``scripts/``, ``tests/``, ``docs/``, ``.claude/``) resolve.
  4. **External URLs** (``--check-external``) — http(s) liveness (network).
  5. **ADR refs** (``--check-ids``) — every ``ADR-NNNN`` resolves to
     ``docs/developers/adr/NNNN-*.md``.

Only class 1 runs by default — it has no legitimate false-positive source
once code fences, external URLs, and cross-repo targets are excluded, so it
is safe as a hard CI gate. Classes 2/3/5 reference the wider world (the
installed ``awesome-task-system`` package's upstream task IDs, the foreign
AwesomeStudioPedal dossier IDs, predecessor script paths) and are
opt-in to keep CI deterministic.

Documented class-1 exclusions:
  - **Code fences** — links inside ```` ``` ```` blocks are illustrative
    output, not navigation.
  - **External / mailto** targets — class 4's job.
  - **Cross-repo targets** — a link resolving outside the repo root
    (``../AwesomeStudioPedal/…``) can't be validated here.
  - **Lifecycle-folder drift** — a link to ``tasks/open/task-053-….md`` is
    valid if TASK-053 exists in *any* lifecycle folder. Housekeep moves
    task/idea/epic files between open/active/closed/paused without
    rewriting inbound links; the file existing by ID is what matters.
  - **Vendored skills** — ``.claude/skills/`` is the installed
    ``awesome-task-system`` package (and its upstream IDs/links); only the
    project's own ``.claude/skills/circuit/`` is in scope.

Fast (well under five seconds); CI runs it on every PR
(``.github/workflows/ci.yml``, job ``check-docs-refs``). Exit 0 when every
checked reference resolves; 1 otherwise.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_EXCLUDED_DIRS = {".venv", "node_modules", ".git"}
_ARCHIVED_IDEAS = "docs/developers/ideas/archived/"
_SKILLS = ".claude/skills/"
# Frozen-record trees: task/idea/ADR files and underscore working docs are
# point-in-time records whose links are not maintained as the tree evolves
# (housekeep moves files; ADRs are immutable). The gate covers the *living*
# narrative docs, where stale links are real drift worth failing CI over.
_RECORD_PREFIXES = (
    "docs/developers/tasks/",
    "docs/developers/ideas/",
    "docs/developers/adr/",
)

# [text](target) and ![alt](target); target up to whitespace or ).
_LINK_RE = re.compile(r"!?\[(?P<text>[^\]]*)\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
_FENCE_RE = re.compile(r"^\s*```")
# Backtick-wrapped concrete repo path.
_BACKTICK_PATH_RE = re.compile(
    r"`(?P<path>(?:src|scripts|tests|docs|\.claude)/[\w./-]+"
    r"\.(?:py|json|md|toml|ya?ml|sh|cfg|txt|svg|csv|net))`"
)
_ID_RE = re.compile(r"\b(?P<kind>TASK|EPIC|IDEA)-(?P<num>\d{2,4})\b")
# A link target that points at a task/idea/epic file (any lifecycle folder).
_TASK_LIKE_RE = re.compile(r"(?:^|/)(?P<kind>task|epic|idea)-(?P<num>\d+)-[^/]*\.md$")
_ADR_RE = re.compile(r"\bADR-(?P<num>\d{3,4})\b")
_EXTERNAL = ("http://", "https://", "mailto:")
_GLOB_CHARS = set("*?<>{}")
# Predecessor artefacts that live in AwesomeStudioPedal, not here.
_PREDECESSOR_PATHS = {"scripts/generate-schematic.py", "data/config.json"}


def _vendored_skill(rel: str) -> bool:
    """A skill from the installed awesome-task-system package (not ours)."""
    return rel.startswith(_SKILLS) and not rel.startswith(_SKILLS + "circuit/")


def _md_files(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("*.md"):
        rel = p.relative_to(root)
        relposix = rel.as_posix()
        if any(part in _EXCLUDED_DIRS for part in rel.parts):
            continue
        if _vendored_skill(relposix):
            continue
        if p.name.startswith("_") or relposix.startswith(_RECORD_PREFIXES):
            continue
        out.append(p)
    return sorted(out)


def _resolves_by_id(path_part: str, ids: dict[str, set[int]]) -> bool:
    """True if a task/idea/epic link resolves by ID in any lifecycle folder."""
    m = _TASK_LIKE_RE.search(path_part)
    if not m:
        return False
    kind = {"task": "TASK", "epic": "EPIC", "idea": "IDEA"}[m.group("kind")]
    return int(m.group("num")) in ids.get(kind, set())


def _id_index(root: Path) -> dict[str, set[int]]:
    index: dict[str, set[int]] = {"TASK": set(), "EPIC": set(), "IDEA": set()}
    patterns = {
        "TASK": (root / "docs/developers/tasks", re.compile(r"task-(\d+)")),
        "EPIC": (root / "docs/developers/tasks", re.compile(r"epic-(\d+)")),
        "IDEA": (root / "docs/developers/ideas", re.compile(r"idea-(\d+)")),
    }
    for kind, (base, rx) in patterns.items():
        if not base.is_dir():
            continue
        for md in base.rglob("*.md"):
            m = rx.search(md.name)
            if m:
                index[kind].add(int(m.group(1)))
    return index


def _adr_index(root: Path) -> set[int]:
    base = root / "docs/developers/adr"
    if not base.is_dir():
        return set()
    out: set[int] = set()
    for md in base.glob("*.md"):
        m = re.match(r"(\d+)-", md.name)
        if m:
            out.add(int(m.group(1)))
    return out


def _external_text_spans(line: str) -> list[tuple[int, int]]:
    return [m.span("text") for m in _LINK_RE.finditer(line) if m.group("target").startswith(_EXTERNAL)]


def _in_span(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= pos < end for start, end in spans)


def _within_root(resolved: Path, root: Path) -> bool:
    try:
        resolved.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def check(
    root: Path,
    *,
    check_ids: bool = False,
    check_paths: bool = False,
    check_external: bool = False,
) -> list[str]:
    """Return a sorted list of human-readable failure lines."""
    ids = _id_index(root)  # always built: also normalises lifecycle-folder link drift
    adrs = _adr_index(root) if check_ids else set()
    failures: list[str] = []
    external_targets: dict[str, tuple[str, int]] = {}

    for md in _md_files(root):
        rel = md.relative_to(root).as_posix()
        skip_ids = rel.startswith(_ARCHIVED_IDEAS) or rel.startswith(_SKILLS)
        in_fence = False
        for lineno, raw in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if _FENCE_RE.match(raw):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            ext_spans = _external_text_spans(raw)

            # Class 1 — relative links (default).
            for m in _LINK_RE.finditer(raw):
                target = m.group("target")
                if target.startswith(_EXTERNAL):
                    external_targets.setdefault(target, (rel, lineno))
                    continue
                if target.startswith("#"):
                    continue
                path_part = target.split("#", 1)[0]
                if not path_part or any(c in path_part for c in _GLOB_CHARS):
                    continue
                resolved = root / path_part.lstrip("/") if path_part.startswith("/") else md.parent / path_part
                if not _within_root(resolved, root):
                    continue
                if not resolved.exists() and not _resolves_by_id(path_part, ids):
                    failures.append(f"{rel}:{lineno}: broken link -> {target}")

            # Class 3 — backtick code paths (opt-in).
            if check_paths:
                for m in _BACKTICK_PATH_RE.finditer(raw):
                    p = m.group("path")
                    if any(c in p for c in _GLOB_CHARS) or p in _PREDECESSOR_PATHS:
                        continue
                    if not (root / p).exists():
                        failures.append(f"{rel}:{lineno}: broken code-path -> {p}")

            # Classes 2 & 5 — ID / ADR refs (opt-in).
            if check_ids and not skip_ids:
                for m in _ID_RE.finditer(raw):
                    if _in_span(m.start(), ext_spans):
                        continue
                    kind, num = m.group("kind"), int(m.group("num"))
                    if num not in ids[kind]:
                        failures.append(f"{rel}:{lineno}: unresolved ref -> {kind}-{m.group('num')}")
                for m in _ADR_RE.finditer(raw):
                    if _in_span(m.start(), ext_spans):
                        continue
                    if int(m.group("num")) not in adrs:
                        failures.append(f"{rel}:{lineno}: unresolved ref -> ADR-{m.group('num')}")

    if check_external:
        failures.extend(_check_external(external_targets))

    return sorted(set(failures))


def _check_external(targets: dict[str, tuple[str, int]]) -> list[str]:
    import urllib.error
    import urllib.request

    out: list[str] = []
    for url, (rel, lineno) in sorted(targets.items()):
        if url.startswith("mailto:"):
            continue
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "circuitsmith-docref"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
                if resp.status >= 400:
                    out.append(f"{rel}:{lineno}: dead URL ({resp.status}) -> {url}")
        except (urllib.error.URLError, ValueError, TimeoutError) as exc:
            out.append(f"{rel}:{lineno}: unreachable URL ({exc}) -> {url}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Markdown cross-references against the "
        "filesystem and the task/idea/ADR indexes (TASK-105).",
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repo root to check")
    parser.add_argument("--check-ids", action="store_true", help="also resolve TASK/EPIC/IDEA/ADR refs")
    parser.add_argument("--check-paths", action="store_true", help="also resolve backtick code paths")
    parser.add_argument(
        "--check-external",
        action="store_true",
        help="also check external http(s) URL liveness (needs network; off by default)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()

    failures = check(
        root,
        check_ids=args.check_ids,
        check_paths=args.check_paths,
        check_external=args.check_external,
    )
    if not failures:
        sys.stderr.write("doc-reference gate OK: every checked reference resolves.\n")
        return 0

    sys.stderr.write(f"doc-reference gate FAILED ({len(failures)} broken reference(s)):\n")
    for line in failures:
        sys.stderr.write(f"  - {line}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
