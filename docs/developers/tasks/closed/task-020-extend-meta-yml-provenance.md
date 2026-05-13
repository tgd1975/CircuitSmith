---
id: TASK-020
title: Extend meta.yml.provenance with ai_invoked and escalations
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
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

- [x] `meta.yml.provenance.ai_invoked` is written on every renderer run (true/false, never absent). _Renderer's `_provenance_lines()` emits `ai_invoked: true|false` unconditionally; `test_kernel_only_run_records_ai_invoked_false` + `test_ai_run_records_ai_invoked_true_with_iteration_count` cover both branches._
- [x] `meta.yml.provenance.escalations` lists every escalation reason code; an empty array on a kernel-only success run. _TASK-057 already established the empty-array invariant; TASK-020 extends the schema's category enum with the `ai-placer-*` reason codes and the v1 `rubric-fail-min-label-distance` / `rubric-fail-density` codes that landed under TASK-019. `test_schema_enum_covers_all_emitted_escalation_categories` enforces._
- [x] Both fields are documented in `docs/layout.md`. _The meta.yml block at [`.claude/skills/circuit/docs/layout.md`](../../../.claude/skills/circuit/docs/layout.md) covers `ai_invoked`, `iterations`, `ai_invocations`, and the escalations enum. TASK-021 will add the AI-placer narrative section that builds on this._
- [x] An automated release-prep review tool can parse `escalations` across all committed `meta.yml` files to compute a kernel-failure rate. _`scripts/check_phase2b_trigger.py` does exactly this (TASK-058); `test_release_prep_review_can_parse_escalation_corpus` confirms ruamel.yaml parses the renderer's flow-style output cleanly._

## Implementation notes

The `ai_invocations` block is the §7.3 cost-accounting record: one
flow-style entry per AI dispatch carrying `reason`, `iterations`,
`input_tokens`, `output_tokens`, and the `components` whose
ambiguities the placer was asked to resolve. The block is omitted on
kernel-only runs to keep the v0.1 fixture meta.yml byte-stable (the
fixture re-baseline TASK-019 mentioned was unnecessary because the
omit-when-empty rule preserves the prior shape). The `aiReason` /
`aiInvocation` sub-schemas in `meta.schema.json` formalise this
contract for future tooling.

A small bug surfaced during the inline-YAML emit: a Python list was
being stringified via `str(value)`, producing `"['R1']"`. Fixed by
teaching `_yaml_inline()` to emit lists in YAML flow form (`[R1]`).

## Test Plan

Add `tests/test_meta_yml_provenance.py` covering: kernel-only run records `ai_invoked: false` + empty `escalations`; AI-placer run records `ai_invoked: true` + the relevant reason code.

## Prerequisites

- **TASK-017** — AI placer must exist to populate `ai_invoked: true`.

## Notes

See `idea-001.layout-engine-concept.md §17.2` (drift guard).
