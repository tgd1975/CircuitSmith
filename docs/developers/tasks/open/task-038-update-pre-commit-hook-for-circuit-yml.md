---
id: TASK-038
title: Update pre-commit hook to trigger on .circuit.yml changes
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Medium
human-in-loop: No
epic: circuit-markdown-integration
order: 3
prerequisites: [TASK-036]
---

## Description

Update the pre-commit hook to fire the renderer on any `.circuit.yml`
change in the staged set. The hook regenerates the corresponding SVG,
`erc-report.md`, `bom.md`, and `main-circuit.net`, and stages the
updated artefacts so the commit includes them.

This replaces the legacy `.py`-trigger from the pre-cutover era (which
TASK-015 already removed). The new trigger is `.circuit.yml` plus any
file under `.claude/skills/circuit/components/`.

## Acceptance Criteria

- [ ] Editing `data/esp32.circuit.yml` and staging it auto-regenerates and stages all four output artefacts.
- [ ] Editing a component profile (`components/passives.py`, etc.) also triggers regeneration for any circuit using that profile.
- [ ] The hook is fast enough not to be skipped — under 5 seconds on the shipped circuits (regenerate skipped if `meta.yml.fingerprint` matches the input hash).
- [ ] The hook is bypassable via the documented project mechanism (`CS_COMMIT_BYPASS`).

## Test Plan

Add `tests/test_precommit_hook.py` (or shell-based integration test) covering: `.circuit.yml` edit triggers regeneration, component-profile edit triggers regeneration, no-change commit does not run the renderer, bypass-env-var skips the hook.

## Prerequisites

- **TASK-036** — the renderer must be wired into the build mechanism this hook invokes.

## Notes

This closes out EPIC-005. The CLAUDE.md project-level commit protocol
(`/commit` skill + `scripts/commit-pathspec.sh`) is upstream of this
hook and is not affected.
