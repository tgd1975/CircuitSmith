---
id: TASK-131
title: Gallery re-attempt — op-amp non-inverting buffer (supersedes TASK-099)
status: open
opened: 2026-05-14
effort: Small (<2h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 22
prerequisites: [TASK-122, TASK-123]
---

## Description

Authors the op-amp-non-inverting-buffer gallery entry's
`circuit.yml` against the new `ic/opamp_dual_supply` profile
(TASK-122). Single page. Replaces TASK-099's placeholder.

A non-inverting buffer has its output tied to its inverting input
(unity gain). Add two power-rail decoupling caps (one on `V+` to
GND, one on `V-` to GND); these exercise the C+C decoupling rule
from TASK-113 as a bonus, and avoid TASK-123's power-pin-floating
ERC error.

Supersedes TASK-099 (kept for history).

## Acceptance Criteria

- [ ] `docs/users/examples/opamp-non-inverting-buffer/` gains `circuit.yml`, `layout.yml`, `meta.yml`, `opamp-non-inverting-buffer.svg`, `erc-report.md`.
- [ ] Power-rail decoupling caps present on both `V+` and `V-`; ERC power-pin-floating rule passes (negative case).
- [ ] `README.md` follows the six-section template fully.
- [ ] The committed SVG is byte-identical to the renderer's output.

## Test Plan

No new automated tests required — TASK-101's gallery regression
script covers the artefacts.

Manual verification:

1. Run the skill against `circuit.yml`; confirm output matches.
2. Verify the topology is genuinely unity-gain (output → IN-,
   IN+ takes the input signal).
3. `markdownlint-cli2` passes.

## Documentation

- `docs/users/examples/opamp-non-inverting-buffer/README.md` —
  replace the blocked-on-IDEA-009 prose with an EPIC-014
  implementation pointer; fill the SVG + BOM sections.

## Prerequisites

- **TASK-122** — ic/opamp_dual_supply profile must exist for
  the YAML to reference.
- **TASK-123** — active-device ERC must accept a correctly
  authored op-amp circuit (power-pin-floating rule's negative
  case passes when both rails are decoupled).

## Notes

- A unity-gain buffer is the simplest meaningful op-amp
  application; the example deliberately doesn't add resistive
  feedback for non-unity gain because that would make the
  topology a different example (non-inverting amplifier rather
  than buffer). Save the gain variant for a future gallery
  entry if needed.
