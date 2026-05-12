---
id: TASK-042
title: Finalise all .claude/skills/circuit/docs/ files
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: circuit-skill-packaging
order: 4
prerequisites: [TASK-016, TASK-030, TASK-035, TASK-038, TASK-041]
---

## Description

Close out the skill's `docs/` directory:

- Update `docs/index.md` with skill invocation examples drawn from the
  Phase 6 transcripts (TASK-041).
- Fill any cross-reference gaps left by earlier doc tasks
  (TASK-007, TASK-016, TASK-030, TASK-035).
- Verify every linked document exists (no rot).
- Ensure the `docs/` directory is fully self-contained for the
  standalone-repo extraction (TASK-043+) — no project-specific paths
  outside the `docs/` files referenced as "this project's CI" or
  similar.

## Acceptance Criteria

- [ ] `docs/index.md` has at least three worked invocation examples drawn from the Phase 6 transcripts.
- [ ] Every internal `docs/` link resolves (verified with a link checker).
- [ ] No `docs/*.md` file references paths outside `.claude/skills/circuit/` (portability contract).
- [ ] A new contributor reading only `docs/index.md` can install the skill, render a circuit, and find their way to the rest of the documentation.

## Test Plan

Run a Markdown link checker (`markdown-link-check` or equivalent) against `docs/`; visual smoke-read of `docs/index.md` from a fresh-eyes perspective.

## Prerequisites

- **TASK-016** — circuit-yaml and layout docs must exist.
- **TASK-030** — erc-checks doc must exist.
- **TASK-035** — index.md BOM/netlist sections must exist.
- **TASK-038** — markdown-integration sections must exist.
- **TASK-041** — Phase 6 transcripts provide invocation examples.

## Notes

This task is the gate between Phase 6 and Phase 7 — the docs must be
self-contained before the standalone-repo extraction can proceed.
