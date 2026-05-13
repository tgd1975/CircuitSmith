---
id: TASK-098
title: Example gallery — 555 monostable timer
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Medium
human-in-loop: Clarification
epic: tutorial-and-examples
order: 7
prerequisites: [TASK-096]
---

## Description

A single-IC example: 555 timer wired as a monostable. Components:

- One 555 (8-pin DIP or SOIC).
- Timing resistor and capacitor.
- Trigger input (push-button or transient).
- Output LED + current-limiting resistor.
- Decoupling cap on VCC.

What this stresses:

- **Pin assignment** — the 555 has 8 pins with non-trivial roles
  (Trigger, Output, Reset, Control, Threshold, Discharge, GND, VCC).
  The schema's pin-naming and the renderer's pin-label placement
  both get exercised.
- **Component grouping** — the timing components (R, C) belong
  visually together; the LED output belongs visually together; the
  supply decoupling belongs near the IC. The layout kernel's
  grouping logic gets a workout.
- **Single-IC layout** — first gallery entry where one component
  dominates the page; tests the renderer's IC-centric layout.

Deliverable matches the TASK-096 template:
`docs/users/examples/555-monostable/` with the four artefacts plus
a six-section `README.md`.

The "what makes it interesting" section should call out pin
assignment and grouping explicitly.

## Acceptance Criteria

- [ ] `docs/users/examples/555-monostable/` exists with all
      artefacts.
- [ ] `README.md` follows the six-section template and explicitly
      discusses pin assignment + component grouping.
- [ ] The 555's pin labels in the rendered SVG match the
      canonical 555 pinout (no swapped trigger/threshold etc.).
- [ ] Gallery index gains a row.

## Test Plan

No automated tests required — change is documentation. Regression
coverage in TASK-101.

Manual verification:

1. Run the skill; confirm output matches committed artefacts.
2. Cross-check the pin labels against a 555 datasheet (any
   manufacturer; the pinout is universal).
3. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-096** — gallery template.

## Notes

- The 555 is in the canonical sensor/timer territory for the
  components library (TASK-004). If it does not yet have a profile,
  this example forces one — either author the profile inline (small
  scope creep) or file a follow-up task to add it before this
  example can ship.
- Timing values for "monostable" should produce a visible pulse
  (e.g. R = 1MΩ, C = 1µF → ~1.1s pulse). Avoid sub-millisecond
  timing values that no human can visually verify when actually
  building the circuit.
