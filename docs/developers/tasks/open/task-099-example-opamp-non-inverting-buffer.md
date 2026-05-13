---
id: TASK-099
title: Example gallery — op-amp non-inverting buffer
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: tutorial-and-examples
order: 8
prerequisites: [TASK-096]
---

## Description

An op-amp non-inverting buffer (gain of 1) on a dual-rail supply.
Components:

- One op-amp (single-package, dual-rail).
- Two feedback resistors (R1 to ground, R2 in feedback loop —
  zero ohms for unity gain, or two equal resistors for gain of 2;
  pick the buffer-classic configuration).
- Input AC-coupling cap (optional; document the choice).
- Dual-rail supply (+V, -V, GND).
- Bypass capacitors on each rail.

What this stresses:

- **Feedback loop layout** — the feedback wire from output back to
  the inverting input is the classic schematic-readability test.
  Layout kernel must route this without crossing the signal path.
- **Dual-rail supply** — first example with three power nets
  (+V, -V, GND). Tests the renderer's supply-symbol placement and
  the netgraph's three-net topology.
- **ERC** — should validate that both supply rails are decoupled
  (E3 / E4 rule territory) and that the op-amp's supply pins are
  actually connected (E1).

Deliverable: `docs/users/examples/opamp-buffer/` with the four
artefacts plus the six-section `README.md`.

The "what makes it interesting" section calls out the feedback-loop
layout and the dual-rail supply explicitly.

## Acceptance Criteria

- [ ] `docs/users/examples/opamp-buffer/` exists with all artefacts.
- [ ] `README.md` follows the template and discusses feedback-loop
      layout + dual-rail supply.
- [ ] The feedback wire in the SVG does not cross the signal path
      (if it does, log the deviation as a router follow-up — do
      not paper over).
- [ ] Both supply rails have decoupling caps in the schematic *and*
      in the BOM.
- [ ] Gallery index gains a row.

## Test Plan

No automated tests required — change is documentation. Regression
coverage in TASK-101.

Manual verification:

1. Run the skill; confirm output matches.
2. Eyeball the feedback-loop routing.
3. Confirm the ERC report fires no errors and the WARNING set is
   limited to known-acceptable items.
4. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-096** — gallery template.

## Notes

- Don't use the op-amp's "internal compensation" or "rail-to-rail"
  attributes as text in the README — those are part-specific and
  drift with whatever op-amp profile is in the library. Stick to
  topology-level claims.
- If the component library doesn't have an op-amp profile, this is
  blocking — add the profile (small scope creep) or file a
  follow-up. Don't fake the symbol in the SVG.
