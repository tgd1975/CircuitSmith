---
id: TASK-100
title: Example gallery — multi-page split (stresses renderer page-break)
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: tutorial-and-examples
order: 9
prerequisites: [TASK-096]
---

## Description

A gallery entry large enough that the renderer must break it across
multiple pages. This is the only example whose primary purpose is to
exercise the page-break path — every other example fits on a single
page.

Candidate circuit shapes (pick whichever is closest to something
that occurs naturally in CircuitSmith's domain):

- **Multi-section audio chain** — input buffer → gain stage →
  tone control → output buffer. Four sub-blocks, naturally
  page-breakable on sub-block boundaries.
- **Multi-rail power supply** — three rails (e.g. +12V, +5V, +3.3V)
  with three regulator sections + bulk capacitance on each.
- **Sensor + MCU + actuator** — a small system: sensor with
  conditioning circuitry → MCU footprint → MOSFET driver → load.
  Pages split on subsystem boundaries.

What this stresses:

- **Renderer page-break logic** — the only example that actually
  produces a multi-page SVG (or multiple SVGs, depending on how the
  renderer expresses page breaks today).
- **Cross-page net continuity** — nets that cross page boundaries
  get cross-reference labels. The renderer's label-placement and
  the BOM exporter's "global net" accounting both get exercised.
- **Sub-block reuse across pages** — if the chosen shape has
  repeated sub-blocks, they should end up on the same page where
  topologically reasonable.

Deliverable: `docs/users/examples/multi-page/` with all artefacts.
The artefact set is *larger* than the single-page examples:
multiple SVGs (one per page) or one SVG with multiple `<svg>`
sub-trees, depending on the renderer's current page-break output.
Commit whatever the renderer produces, byte-identical.

## Acceptance Criteria

- [ ] `docs/users/examples/multi-page/` exists with all artefacts.
- [ ] The rendered output has at least two pages (or, if the
      renderer expresses pages as separate files, at least two SVG
      files).
- [ ] Cross-page net labels render correctly (no orphaned cross-
      references).
- [ ] `README.md` follows the six-section template and discusses
      the page-break behaviour and any caveats.
- [ ] Gallery index gains a row.

## Test Plan

No automated tests required — change is documentation. Regression
coverage in TASK-101.

Manual verification:

1. Run the skill; confirm the multi-page output matches the
   committed artefacts.
2. Walk every cross-page net label and confirm the reference
   resolves to the other page.
3. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-096** — gallery template.

## Notes

- This is the example most likely to expose renderer bugs (page
  breaks are a less-trodden path than single-page render). If the
  current page-break implementation has known limitations, document
  them in the README's "what makes it interesting" section as
  known caveats — readers learning *what CircuitSmith does* should
  also learn *what its current edge cases are*.
- The candidate shapes are suggestions; the author should pick
  whichever shape produces the *clearest* multi-page output, not
  the most-electronically-interesting one. The point of this
  example is the page-break behaviour, not the circuit topology.
