---
id: TASK-113
title: Kernel canonical rule — C + C decoupling pair
status: open
opened: 2026-05-14
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 4
prerequisites: [TASK-110]
---

## Description

Adds the C + C decoupling-pair canonical-slot rule. Topology
fingerprint: two capacitors in parallel, both terminals on one cap
connected to the same nets as the corresponding terminals on the
other (VCC and GND). Conventional shape is `100 nF || 10 µF` — a
fast bypass plus a bulk reservoir cap on the same rail.

Slot assignment: stack the pair tightly, shared GND rail, both caps
in the power-rail decoupling region. The pair reads as one
sub-system, not two unrelated caps.

Independent of TASK-111 and TASK-112; can land in parallel.

## Acceptance Criteria

- [ ] Rule entry added under `src/circuitsmith/layout/` with the C+C parallel-on-rail fingerprint.
- [ ] Slot assignment stacks the pair on a shared GND rail.
- [ ] Golden fixture committed (single instance, and a circuit with two decoupling pairs on different rails).
- [ ] No regression on existing fixtures.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/layout/test_cc_decoupling_rule.py`.
- Cover: pair-on-VCC match, pair-on-VDD3V3 match, mismatch (caps
  with different non-GND terminals — should *not* match), pair on
  multiple rails, golden-SVG byte-identity.

## Prerequisites

- **TASK-110** — frozen decisions consumed here.

## Notes

- The rule does not care about cap *values*; the topology is the
  fingerprint. A 100 nF + 100 nF "pair" still matches, even though
  it's electrically pointless — that's an ERC concern, not a
  layout concern.
- If the same rail has three or more caps in parallel, the rule
  fires once per consecutive pair; the renderer's stacking should
  degrade gracefully. Document any cap-count limit in the rule's
  fingerprint description.
