---
id: TASK-130
title: Gallery re-attempt — 555 monostable (supersedes TASK-098)
status: open
opened: 2026-05-14
effort: Small (<2h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 21
prerequisites: [TASK-121, TASK-123]
---

## Description

Authors the 555-monostable gallery entry's `circuit.yml` against
the new `ic/555` profile (TASK-121). Single page. Replaces
TASK-098's placeholder.

Pick R and C values that produce a sensible monostable pulse width
(the classic `t = 1.1 * R * C`). Values that yield, say, 1 ms or
100 ms reads as deliberate; random values do not.

Supersedes TASK-098 (kept for history).

## Acceptance Criteria

- [ ] `docs/users/examples/555-monostable/` gains `circuit.yml`, `layout.yml`, `meta.yml`, `555-monostable.svg`, `erc-report.md`.
- [ ] R + C values produce a documented pulse width (named in the README's "what makes it interesting" section).
- [ ] `README.md` follows the six-section template fully.
- [ ] ERC report clean — no false-positive pin-naming-drift warnings (use silkscreen-pin form throughout for cleanliness).
- [ ] The committed SVG is byte-identical to the renderer's output.

## Test Plan

No new automated tests required — TASK-101's gallery regression
script covers the artefacts.

Manual verification:

1. Run the skill against `circuit.yml`; confirm output matches.
2. Verify the pulse-width arithmetic from the chosen R/C values.
3. `markdownlint-cli2` passes.

## Documentation

- `docs/users/examples/555-monostable/README.md` — replace the
  blocked-on-IDEA-009 prose with an EPIC-014 implementation
  pointer; fill the SVG + BOM sections.

## Prerequisites

- **TASK-121** — ic/555 profile must exist for the YAML to
  reference.
- **TASK-123** — active-device ERC must accept a correctly
  authored 555 circuit (pin-naming-drift rule's negative case
  passes when silkscreen-pin form is used consistently).

## Notes

- Use the silkscreen-pin form (`U1.1`, `U1.2`, …) in
  `connections:` to avoid TASK-123's pin-naming-drift warning.
  Document the silicon-name aliases in the README prose so
  readers can map silkscreen to function — that's pedagogical
  content the warning *suggests* should live in code-style
  guidance, not the YAML itself.
