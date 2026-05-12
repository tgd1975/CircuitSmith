---
id: TASK-020
title: Extend meta.yml.provenance with ai_invoked and escalations
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-renderer-layout
order: 13
prerequisites: [TASK-017, TASK-057]
---

## Description

Extend the `meta.yml` sidecar's `provenance` block with `ai_invoked`
and the AI-placer-specific entries of the `escalations` array
introduced by [TASK-057](task-057-emit-v01-escalations-to-meta-yml.md):

- `ai_invoked: bool` — true if the AI placer was called for this run.
- AI-specific `escalations[].category` values (e.g. `ai-no-converge`,
  `ai-token-cap`, plus any AI-placer reason codes from `layout §7`) are
  added on top of the v0.1 enum from TASK-057.

The base `escalations` field (with the v0.1 enum:
`no-canonical-rule`, `slot-overflow`, `router-stall`,
`rubric-fail-*`) is introduced by TASK-057 — this task layers the
Phase 2b additions on top of that foundation.

Together these fields are the v0.1/v1 drift guard per `layout §17.2`:
they make the kernel-failure rate visible at every release-prep review
and replace speculation with evidence when deciding whether to promote
further numeric checks or retire the AI placer.

## Acceptance Criteria

- [ ] `meta.yml.provenance.ai_invoked` is written on every renderer run (true/false, never absent).
- [ ] `meta.yml.provenance.escalations` lists every escalation reason code; an empty array on a kernel-only success run.
- [ ] Both fields are documented in `docs/layout.md`.
- [ ] An automated release-prep review tool can parse `escalations` across all committed `meta.yml` files to compute a kernel-failure rate.

## Test Plan

Add `tests/test_meta_yml_provenance.py` covering: kernel-only run records `ai_invoked: false` + empty `escalations`; AI-placer run records `ai_invoked: true` + the relevant reason code.

## Prerequisites

- **TASK-017** — AI placer must exist to populate `ai_invoked: true`.

## Notes

See `idea-001.layout-engine-concept.md §17.2` (drift guard).
