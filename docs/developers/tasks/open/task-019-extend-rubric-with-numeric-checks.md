---
id: TASK-019
title: Extend rubric with numeric checks promoted from advisory
status: open
opened: 2026-05-12
effort: Medium (2-8h)
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

- [ ] At least one previously-advisory check is promoted to blocking with an empirically-derived threshold.
- [ ] The threshold is documented in `docs/layout.md` with a one-line rationale ("75th percentile across N green Phase 2a runs").
- [ ] Both shipped circuits pass the promoted checks at the new threshold.
- [ ] Promotion does not silently invalidate any prior fixture — explicit re-baseline of `full-pedal` is committed if needed.

## Test Plan

Add `tests/test_rubric_v1.py` covering: each promoted check fires on a fixture below the threshold, passes above; both shipped circuits pass at the empirical threshold.

## Prerequisites

- **TASK-017** — AI placer ships with v1 rubric updates as a coherent change.

## Notes

See `idea-001.layout-engine-concept.md §10` (advisory → blocking
promotion procedure).
