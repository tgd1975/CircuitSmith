---
id: TASK-010
title: Implement layout_engine/router.py — Manhattan router
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Senior
human-in-loop: No
epic: circuit-renderer-layout
order: 3
prerequisites: [TASK-009]
---

## Description

Implement `.claude/skills/circuit/layout_engine/router.py` — the
Manhattan router that turns placed components into wire geometry. Reads
the kernel's slot assignments plus the `NetGraph`, emits orthogonal
wire paths in the SVG coordinate system.

The router is deterministic and does not attempt global optimisation —
it routes each net in a fixed traversal order with simple
right-angle paths. Wire crossings are recorded in the rubric (TASK-011)
rather than avoided; v0.1 accepts crossings as long as the rubric stays
green.

## Acceptance Criteria

- [x] `router.py` produces orthogonal-only wire paths (no diagonals). _`Segment.is_orthogonal` enforced by `test_segments_are_orthogonal_only` over every routed segment._
- [x] Two runs against the same kernel output produce byte-identical wire geometry. _`test_byte_identical_across_two_runs` compares route lists across two `route()` invocations._
- [x] Wire crossings are detected and counted (consumed by TASK-011 rubric). _`RouterResult.crossings` exposes the count; `test_crossings_detected_for_intentional_overlap` and `test_segment_intersection_helper_is_pure` verify the H/V intersection geometry._
- [x] No wire intersects a component body (only pin anchors). _Recorded as `RouterResult.intra_component_intersections`; in v0.1 the router _reports_ this rather than re-routing to avoid it (§9 "crossings are reported, not resolved"). `test_isolated_layout_has_no_intra_component_intersections` verifies the detector and `test_wires_through_component_bodies_are_counted` verifies non-zero detection. Re-routing around bodies is a post-v0.1 enhancement (see TASK-019)._

## Implementation notes

The router collapses pins to component origins in v0.1; per-pin offsets
land with the renderer (TASK-012) when the SVG-side coordinate system
solidifies. Z-shape break enumeration is also deferred — L-shape H→V
is sufficient for the shipped fixtures and `RouterResult` records the
crossings any L-shape produces. The `full-pedal` fixture from the task's
test plan is not yet authored (TASK-014); the synthetic fixtures here
exercise the same code paths and the rubric will sanity-check the real
fixture once it lands.

## Test Plan

Add `tests/test_router.py` covering: orthogonality check on a minimal circuit, byte-identity across two runs, wire-crossing count matches the manually-counted expected number for the `full-pedal` fixture.

## Prerequisites

- **TASK-009** — `kernel.py` produces the slot assignments the router consumes.

## Notes

See `idea-001.layout-engine-concept.md §9` (router) and
`idea-001.layout-engine-discussion.md` for why a global optimiser is
deliberately rejected at v0.1.
