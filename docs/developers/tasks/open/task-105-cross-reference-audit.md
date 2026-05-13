---
id: TASK-105
title: Cross-reference audit — internal links, TASK/EPIC/IDEA refs, code-path mentions
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Medium
human-in-loop: Clarification
epic: post-epic-006-doc-audit
order: 4
prerequisites: [TASK-104]
---

## Description

After the voice rewrite, the document set is uniform but the
*links* may still be broken. This task walks every cross-reference
in the repo's `.md` files and either verifies or fixes each one.

Reference classes to check:

- **Relative markdown links** — `[text](relative/path.md)` and
  anchor links (`#heading-slug`). Broken targets are the most
  common rot.
- **`TASK-NNN` / `EPIC-NNN` / `IDEA-NNN` references in prose** —
  every ID mentioned in prose should resolve to a file that exists
  in `docs/developers/tasks/{open,active,closed,paused}/` or
  `docs/developers/ideas/{open,archived}/`.
- **Code-path mentions** — every `src/circuitsmith/foo/bar.py`
  reference should resolve to a file that exists at that path.
  Same for `scripts/X.py` and `.claude/skills/X/SKILL.md`.
- **External URLs** — GitHub repo URLs, the PartsLedger reference,
  any other URLs. Validate they still resolve. Don't auto-fix
  these; flag them for the maintainer.
- **ADR references** — `adr/NNNN-slug.md` paths.

Implementation approach: extend `scripts/check_doc_references.py`
if it exists, or create it. The script:

- Walks every `.md` file.
- Extracts references by regex (links, ID refs, path refs).
- Validates each one against the filesystem / index.
- Reports failures with file:line context.

Wire the script into CI as a gate. The check is fast (< 5 seconds
total) so it can run on every PR.

## Acceptance Criteria

- [ ] `scripts/check_doc_references.py` exists (or is extended) and
      catches all five reference classes.
- [ ] Every reference in the repo currently resolves (the script
      exits 0 on the post-rewrite state).
- [ ] Script runs in CI on every PR.
- [ ] `.claude/settings.json` allow rule added.
- [ ] `scripts/README.md` updated.

## Test Plan

**Host tests**:

- `tests/test_check_doc_references.py`:
  - Construct a temp doc tree with one broken relative link.
    Expect exit non-zero with the broken link in stderr.
  - Construct a temp tree with a phantom `TASK-999` reference.
    Expect exit non-zero.
  - Construct a temp tree where every reference resolves. Expect
    exit 0.

Manual verification:

1. Run the script against the current repo state; exit 0 after
   TASK-104 closes.
2. Introduce a deliberately broken link in a throwaway file;
   confirm the script flags it.

## Prerequisites

- **TASK-104** — voice rewrite must close first so we audit
  references in the canonical text, not in the about-to-be-rewritten
  text.

## Documentation

- `scripts/README.md` — add the new script row.
- `docs/developers/CI_PIPELINE.md` — add the new gate.

## Notes

- External URL validation should be opt-in (a `--check-external`
  flag), not default. The default `pytest`-time + CI-time run
  should not depend on network reachability — flaky on no-internet
  CI runners.
- The script could grow into a general "doc reference linter" over
  time. Keep the initial scope tight (the five reference classes
  above) and add classes as drift patterns appear.
- Coordinate with TASK-091 (test-plan staleness check) and TASK-101
  (gallery regression diff) on CI job naming. Suggested:
  `check-docs-refs`.
