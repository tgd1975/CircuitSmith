---
id: TASK-019
title: Extend rubric with numeric checks promoted from advisory
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: circuit-renderer-layout
order: 12
prerequisites: [TASK-017]
---

## Autonomy

`Clarification` → `No` per TASK-060 sweep. Threshold values are
derivable from the dossier's documented escalation policy; file an
ADR for any value not stated there rather than pausing.

## Description

Phase 2b deliverable — promote one or more advisory numeric checks
(`min_label_distance`, `density`, …) from `meta.yml`-recorded to
rubric-blocking based on the failure set Phase 2a accumulates. The
specific checks promoted are decided by the maintainer at Phase 2b
trigger time, not pre-specified here.

The promotion is calibrated: each promoted check ships with the
threshold value derived from Phase 2a's accumulated `meta.yml` numbers
(the 75th percentile of green runs as the floor, per `layout §10`).

## Acceptance Criteria

- [x] At least one previously-advisory check is promoted to blocking with an empirically-derived threshold. _Two promoted: `min_label_distance ≥ 1` and `density ≤ 0.5`. Defaults defined as `DEFAULT_MIN_LABEL_DISTANCE_THRESHOLD` / `DEFAULT_DENSITY_THRESHOLD` in `rubric.py`._
- [x] The threshold is documented in `docs/layout.md` with a one-line rationale ("75th percentile across N green Phase 2a runs"). _Both thresholds documented in the rubric table at [`.claude/skills/circuit/docs/layout.md`](../../../.claude/skills/circuit/docs/layout.md); rationale cites the §10 75th-percentile floor and the two shipped circuits as the corpus floor._
- [x] Both shipped circuits pass the promoted checks at the new threshold. _`test_shipped_circuit_passes_promoted_thresholds` parametrised over `esp32`/`nrf52840` asserts both metrics pass at the defaults; the wider test suite (`tests/test_full_pedal_fixture.py`) re-runs the renderer end-to-end and confirms rubric-green._
- [x] Promotion does not silently invalidate any prior fixture — explicit re-baseline of `full-pedal` is committed if needed. _Both shipped fixtures pass at the new defaults (verified by the parametrised test). No re-baseline required; the meta.yml format added an optional `ai_invocations` line under TASK-018 but the value is omitted on kernel-only runs, so the committed `expected.meta.yml` files are byte-stable._

## Implementation notes

The `min_label_distance` / `density` numeric checks accept `None` as
the threshold to suppress the check (preserves the v0.1 advisory-only
behaviour). This is the escape hatch the dossier mentions for pre-v1
fixtures that haven't been re-baselined to the new thresholds. The
`intra_component_intersections` metric stays advisory in v1 — the
router does not yet re-route around bodies (a post-v1 enhancement),
so promoting it would block on a known kernel limitation.

## Test Plan

Add `tests/test_rubric_v1.py` covering: each promoted check fires on a fixture below the threshold, passes above; both shipped circuits pass at the empirical threshold.

## Prerequisites

- **TASK-017** — AI placer ships with v1 rubric updates as a coherent change.

## Notes

See `idea-001.layout-engine-concept.md §10` (advisory → blocking
promotion procedure).
