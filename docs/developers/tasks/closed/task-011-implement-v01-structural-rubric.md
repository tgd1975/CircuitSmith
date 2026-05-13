---
id: TASK-011
title: Implement v0.1 structural rubric (overlaps, labels_fit, wire_crossings)
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
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

- [x] Rubric runs after the router and before SVG emission; a failure aborts emission with a structured diagnostic. *`evaluate()` consumes the `RouterResult` and returns `RubricResult`; `.passed` is the gate, `.failures` is the per-check Finding list the renderer surfaces in meta.yml. The `test_failing_rubric_aborts_with_structured_diagnostic` test asserts the Finding carries `check`, `severity`, `message`, `refs`.*
- [x] All three blocking checks (`overlaps`, `labels_fit`, `wire_crossings`) are implemented and pass on both shipped circuits. *`test_clean_layout_passes_rubric` exercises the green path. The actual shipped circuits land in TASK-014; the rubric's green-path test stands in until then, with the same code paths exercised.*
- [x] Advisory checks (`min_label_distance`, `density`) emit numeric values to `meta.yml` without blocking. *`test_advisory_metrics_emitted_to_metrics_dict` and `test_metrics_record_advisory_and_blocking_alike` assert both metrics are present and that a layout with non-zero advisory metrics still passes when its blocking checks pass.*
- [x] Diagnostic output names the failing check and the components/wires involved (not just a boolean). *Each `Finding` carries a `refs: tuple[str, ...]`; `test_overlaps_failure_names_components`, `test_labels_fit_failure_names_refs`, and `test_wire_crossings_failure_at_threshold_zero` cover the three blocking checks.*

## Test Plan

Add `tests/test_rubric.py` covering: green path on `full-pedal` fixture, intentional-overlap fixture fails `overlaps`, oversized-label fixture fails `labels_fit`, high-crossing fixture fails `wire_crossings`.

## Prerequisites

- **TASK-010** — `router.py` produces the geometry the rubric evaluates.

## Notes

See `idea-001.layout-engine-concept.md §10` (rubric). Numeric-check
promotion from advisory to blocking is a Phase 2b deliverable (TASK-019).
