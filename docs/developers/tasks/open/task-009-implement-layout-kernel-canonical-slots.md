---
id: TASK-009
title: Implement layout_engine/kernel.py — deterministic placer
status: open
opened: 2026-05-12
effort: Large (8-24h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-renderer-layout
order: 2
prerequisites: [TASK-008]
---

## Description

Implement `.claude/skills/circuit/layout_engine/kernel.py` — the v0.1
deterministic placer. Reads a `NetGraph` plus the canonical-slot table
(`§5.3` of the layout-engine concept), produces a `layout.yml` with one
slot assignment per component. No AI calls, no randomness, no
backtracking — the kernel is a lookup-and-place routine.

The kernel ships with the incremental-placer invariant: adding a sixth
LED to an existing five-LED layout must change exactly one line in
`layout.yml`, and every kept component's slot must remain byte-identical.
This invariant is the regression guard that Phase 6 acceptance test 5
(TASK-041) exercises.

When the canonical-slot table has no rule for a topology, the kernel
fails loud with a `no-canonical-rule` escalation — a hand-authored
`free`-slot entry plus a `§5.3` table follow-up is the resolution path
in v0.1 (the AI placer in Phase 2b will handle it automatically).

## Acceptance Criteria

- [ ] `kernel.py` produces a deterministic `layout.yml` for both shipped circuits (esp32, nrf52840).
- [ ] Two runs of the kernel against the same `NetGraph` produce byte-identical `layout.yml` output.
- [ ] Adding one component to a circuit changes exactly one line in `layout.yml`; all other slot assignments are byte-identical.
- [ ] Unsupported topology produces a `no-canonical-rule` escalation with the offending component/category named.

## Test Plan

Add `tests/test_kernel.py` covering: byte-identical output for two runs on the same input, single-line diff on incremental component addition, and the `no-canonical-rule` escalation for a category absent from the slot table.

## Prerequisites

- **TASK-008** — `NetGraph` is the kernel's input.

## Sizing rationale

Sized Large because the canonical-slot table, the placement traversal, and the incremental-stability invariant must all be in place before the kernel is useful. Splitting further produces partial states (e.g. "placer without incremental stability") that are not shippable.

## Notes

See `idea-001.layout-engine-concept.md §5` (slot vocabulary), `§5.3`
(canonical-slot table), `§8` (incremental placer). The rationale and
rejected alternatives live in
`idea-001.layout-engine-discussion.md`.
