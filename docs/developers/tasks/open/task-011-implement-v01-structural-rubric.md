---
id: TASK-011
title: Implement v0.1 structural rubric (overlaps, labels_fit, wire_crossings)
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: circuit-renderer-layout
order: 4
prerequisites: [TASK-010]
---

## Description

Implement the v0.1 structural rubric that gates the rendered layout. Three
blocking checks:

- `overlaps` — no two component bodies intersect.
- `labels_fit` — every pin label fits within its allotted slot bounding box.
- `wire_crossings` — counted, with a configurable threshold that blocks
  CI when exceeded.

`wire_crossings` blocks from day one per the Phase 2a deliverable in
`idea-001-circuit-skill.md`. Advisory numeric checks
(`min_label_distance`, `density`) are *recorded* in `meta.yml` but do
not block — they exist to surface trend data without forcing premature
calibration.

## Acceptance Criteria

- [ ] Rubric runs after the router and before SVG emission; a failure aborts emission with a structured diagnostic.
- [ ] All three blocking checks (`overlaps`, `labels_fit`, `wire_crossings`) are implemented and pass on both shipped circuits.
- [ ] Advisory checks (`min_label_distance`, `density`) emit numeric values to `meta.yml` without blocking.
- [ ] Diagnostic output names the failing check and the components/wires involved (not just a boolean).

## Test Plan

Add `tests/test_rubric.py` covering: green path on `full-pedal` fixture, intentional-overlap fixture fails `overlaps`, oversized-label fixture fails `labels_fit`, high-crossing fixture fails `wire_crossings`.

## Prerequisites

- **TASK-010** — `router.py` produces the geometry the rubric evaluates.

## Notes

See `idea-001.layout-engine-concept.md §10` (rubric). Numeric-check
promotion from advisory to blocking is a Phase 2b deliverable (TASK-019).
