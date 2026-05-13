---
id: TASK-097
title: Example gallery — common-emitter amplifier
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: tutorial-and-examples
order: 6
prerequisites: [TASK-096]
---

## Description

The first gallery entry with an *active device* and an analog
signal-flow story. A common-emitter amplifier with:

- One BJT.
- Biasing network (two resistors on the base, one emitter resistor,
  one collector resistor).
- AC-coupling capacitors on input and output.
- Dual-rail or single-rail supply (single-rail is fine; pick the
  simpler one).

What this stresses:

- **Layout kernel** — analog signal flow (input on the left, output
  on the right, supply at top, ground at bottom). The layout
  kernel's slot assignment must produce a layout that *reads*
  like an analog schematic, not a topologically-correct mess.
- **ERC** — rule catalog should validate the biasing topology
  (DC operating point sanity, missing-bypass-cap warnings, etc.)
  to the extent the catalog covers analog circuits.
- **BOM** — first example with capacitors *and* resistors *and* an
  active device; the BOM table starts looking realistic.

Deliverable matches the structure established in TASK-096:
`circuit.yml`, `layout.yml`, `meta.yml`, the rendered SVG, and a
`README.md` following the six-section template.

The example's "what makes it interesting" section should call out
the layout kernel's analog-flow handling explicitly — this is the
example readers will reference when asking "does CircuitSmith do
analog?".

## Acceptance Criteria

- [ ] `docs/users/examples/common-emitter-amplifier/` exists with
      all four artefacts.
- [ ] `README.md` follows the six-section template and explicitly
      discusses the analog signal-flow layout outcome.
- [ ] The committed SVG matches the skill's output.
- [ ] BOM section in the README is non-trivial (resistor values,
      capacitor values, transistor part number — not just
      placeholders).
- [ ] Gallery index gains a row.

## Test Plan

No automated tests required — change is documentation. Regression
coverage in TASK-101.

Manual verification:

1. Run the skill; confirm output matches.
2. Eyeball the layout: input-on-left / output-on-right convention
   should hold. If it does *not*, log the deviation as a
   layout-kernel follow-up rather than papering over it in the
   example.
3. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-096** — establishes the gallery README template this
  example follows.

## Notes

- Pick component values that produce a plausible audio-frequency
  amplifier (e.g. Av≈10, biased for ~half-supply at the collector).
  Random values produce a circuit that renders fine but reads as
  nonsense to anyone who actually does electronics.
- This example is `complexity: Senior` because the circuit design
  choices (biasing values, coupling cap sizing) require electronics
  knowledge to do convincingly. Don't delegate the value choices to
  pure aesthetic judgment.
