---
id: TASK-112
title: Kernel canonical rule — R + C high-pass
status: open
opened: 2026-05-14
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 3
prerequisites: [TASK-110]
---

## Description

Adds the R + C high-pass canonical-slot rule — the mirror of the
low-pass rule from TASK-111. Topology fingerprint: R two-terminal,
C two-terminal, R goes to GND, C is in series on the signal path.
Slot assignment: C on top (in series), R below (to GND), output tap
at the C–R junction.

Independent of TASK-111; can land in parallel.

## Acceptance Criteria

- [ ] Rule entry added under `src/circuitsmith/layout/` with the high-pass topology fingerprint.
- [ ] Slot assignment produces C-top (series), R-below (to GND), output-tap-at-junction.
- [ ] Golden fixture committed for single-instance and pair.
- [ ] No regression on existing fixtures (including TASK-111's low-pass goldens).

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/layout/test_rc_high_pass_rule.py`.
- Cover: single-instance match, pair match, distinguishability from
  low-pass (a low-pass topology must *not* match the high-pass rule
  and vice versa), placement determinism, golden-SVG byte-identity.

## Prerequisites

- **TASK-110** — frozen decisions consumed here.

## Notes

- The low-pass and high-pass rules differ only in which side of the
  RC pair touches GND. The fingerprint must be precise enough to
  distinguish them — otherwise a single ambiguous match emits the
  wrong layout silently.
