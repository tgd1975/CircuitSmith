---
id: TASK-021
title: Update docs/layout.md with AI-placer invocation and cost notes
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-renderer-layout
order: 14
prerequisites: [TASK-017, TASK-018, TASK-019, TASK-020]
---

## Description

Update `.claude/skills/circuit/docs/layout.md` to add the Phase 2b
sections that were structurally placeholdered in TASK-016:

- AI-placer invocation: when it fires, what input it receives, what
  output to expect.
- Convergence behaviour: rounds, reason codes, fail-loud paths.
- Cost notes: per-run token cap, accounting via `meta.yml.provenance`.
- `--no-ai` flag: when to use it, what it suppresses.
- The promoted rubric checks (from TASK-019): threshold, rationale.

## Acceptance Criteria

- [ ] All four AI-placer sections are added to `docs/layout.md`.
- [ ] A contributor can opt out of AI placer usage purely from this doc.
- [ ] Cost expectations are quantified ("typical run: N tokens; cap: M tokens").
- [ ] The doc cross-references `idea-001.layout-engine-concept.md §7` for design rationale.

## Test Plan

No automated tests required — documentation deliverable. Verify cross-references resolve.

## Prerequisites

- **TASK-017** — AI placer behaviour to document.
- **TASK-018** — `--no-ai` flag to document.
- **TASK-019** — promoted rubric checks to document.
- **TASK-020** — `meta.yml.provenance` fields to reference.

## Notes

This closes out EPIC-002 (Phase 2b half).
