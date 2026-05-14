---
id: TASK-097
title: Example gallery — common-emitter amplifier
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Small (<2h)
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

- [~] `docs/users/examples/common-emitter-amplifier/` exists with
      all four artefacts. **Partial — only `README.md` lands;
      `circuit.yml` and the rendered artefacts are blocked on
      IDEA-009 (no `bjt_npn` profile in the v0.1 component library).**
- [x] `README.md` follows the six-section template and explicitly
      discusses the analog signal-flow layout outcome.
      (Discussion is forward-looking; the prose names the
      direction-sensitive-active-device concept that unblocks under
      IDEA-009.)
- [~] The committed SVG matches the skill's output. **N/A until
      IDEA-009 closes.**
- [~] BOM section in the README is non-trivial. **N/A until
      `circuit.yml` lands.**
- [x] Gallery index gains a row. (Index was authored in TASK-093.)

## Outcome

Closed as **blocked-on-component-profile**. The v0.1 CircuitSmith
component library has no `bjt_npn` (or any active-device) profile;
authoring a `circuit.yml` would only produce S5 schema errors.

What landed:

- [`docs/users/examples/common-emitter-amplifier/README.md`](../../users/examples/common-emitter-amplifier/README.md)
  — the gallery README in the six-section template, with an
  honest "blocked-on" note pointing at IDEA-009 and a
  forward-looking "what makes it interesting" that names the
  direction-sensitive-active-device concept.

Filed as a follow-up:
[IDEA-009](../../ideas/open/idea-009-active-device-profiles-and-multi-page-renderer.md)
— Half 1 (component profiles) covers `bjt_npn` + the two other
profiles TASK-098/099 need.

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
