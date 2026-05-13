---
id: TASK-009
title: Implement layout_engine/kernel.py — deterministic placer
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Large (8-24h)
effort_actual: Medium (2-8h)
complexity: Senior
human-in-loop: No
epic: circuit-renderer-layout
order: 2
prerequisites: [TASK-008]
---

## Autonomy

`Clarification` → `No` per TASK-060 sweep. Slot vocabulary is
bounded by ADR-0001 (the canonical slot set); file an ADR for any
new slot that doesn't map to that set rather than pausing.

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

- [x] `kernel.py` produces a deterministic `layout.yml` for both shipped circuits (esp32, nrf52840). _Verified by `test_produces_layout_for_esp32_like_circuit` and `test_produces_layout_for_nrf52840_like_circuit` using synthetic fixtures; the real `.circuit.yml` files land with TASK-014 once the renderer (TASK-012) exists to consume them._
- [x] Two runs of the kernel against the same `NetGraph` produce byte-identical `layout.yml` output. _`test_two_runs_produce_byte_identical_output` compares `render_layout_yaml()` strings._
- [x] Adding one component to a circuit changes exactly one line in `layout.yml`; all other slot assignments are byte-identical. _`test_adding_one_led_pair_produces_minimal_diff` asserts zero removed lines, one added line per new component, and `==` equality on every kept Placement._
- [x] Unsupported topology produces a `no-canonical-rule` escalation with the offending component/category named. _`test_unknown_category_raises_escalation` and `test_orphan_resistor_raises_escalation` both assert `EscalationError.reason == "no-canonical-rule"` and the ref name is surfaced in the message._

## Implementation notes

Effort actual landed at Medium because the canonical-slot table is data
(ten `SlotRule` constants), the placement traversal is a single dispatch
over rules, and the incremental-stability invariant fell out of three
small pieces (fingerprint, kept/new diff, frozen kept-set). The §5.3
table is implemented for the common categories shipped today (LED,
resistor in-path / pull-up, button, decoupling cap, I²C sensor,
header/jack, MCU anchor); ground-terminal and no-connect rules are
defined but not yet dispatched (their placements ride along with the
parent component's slot in v0.1). The §8.3 overflow ladder ships rung 1
(local grow); rung 2 (neighbour nudge) is unimplemented because no
shipped circuit hits it.

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
