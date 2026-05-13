---
id: TASK-096
title: Example gallery — voltage divider
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Junior
human-in-loop: Clarification
epic: tutorial-and-examples
order: 5
prerequisites: [TASK-093]
---

## Description

The smallest meaningful gallery entry: a two-resistor voltage
divider. Single page, no active devices, no biasing, no exotic
components. Establishes the gallery directory's conventions.

Deliverable: `docs/users/examples/voltage-divider/` containing:

- `circuit.yml` — the input.
- `layout.yml`, `meta.yml` — the generated layout artefacts.
- `voltage-divider.svg` — the rendered output.
- `README.md` — what the example demonstrates and what makes it
  the "minimal" gallery entry. Includes the rendered SVG inline,
  the input YAML in a code block (excerpted from `circuit.yml`),
  and a short "what to read next" pointer to the next example.

Gallery README conventions to lock in here (followed by TASK-097
through TASK-100):

1. **Top heading**: H1 with the example's name.
2. **What it demonstrates**: one paragraph, no jargon.
3. **The input**: fenced YAML excerpt from the committed
   `circuit.yml` (do not paraphrase).
4. **The output**: the SVG inline + the BOM table (if non-trivial).
5. **What makes it interesting**: a short prose paragraph naming
   the subsystems exercised and any layout / ERC subtleties.
6. **Next example**: pointer to the next entry in the gallery's
   suggested reading order.

The voltage divider is deliberately first because its README sets
the template every other example follows.

## Acceptance Criteria

- [ ] `docs/users/examples/voltage-divider/` exists with all four
      artefacts (`circuit.yml`, `layout.yml`, `meta.yml`, the SVG).
- [ ] `README.md` follows the six-section structure above.
- [ ] The committed SVG is byte-identical to the output of running
      the skill against the committed `circuit.yml`.
- [ ] The example index in `docs/users/examples/README.md` (from
      TASK-093) gains a row for this entry.

## Test Plan

No automated tests required — change is documentation. Regression
coverage for the committed artefacts lands in TASK-101.

Manual verification:

1. Run the skill against `circuit.yml`; confirm output matches the
   committed artefacts.
2. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-093** — the example sub-directory and gallery index must
  exist.

## Notes

- This task is `complexity: Junior` deliberately — the technical
  content is the simplest possible circuit. The complexity lives in
  *establishing the template*, which is a documentation skill, not
  a circuit-design skill.
- Don't add a third resistor "for interest". The whole point of the
  voltage divider is that it's the smallest non-trivial gallery
  entry; complicating it defeats its role.
