---
id: TASK-122
title: Component profile — ic/opamp_dual_supply
status: closed
closed: 2026-05-14
opened: 2026-05-14
effort: Small (<2h)
effort_actual: XS (<30m)
complexity: Medium
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 13
prerequisites: [TASK-110]
---

## Description

Adds the dual-supply op-amp profile to `src/circuitsmith/components/ics.py`
(shared with TASK-121).

Per IDEA-009 frozen-decisions, pin keys are **symbolic** — `IN+`,
`IN-`, `OUT`, `V+`, `V-` — not silkscreen numbers. ADR-0010's
silkscreen rule applies to ICs whose schematic symbol shows pin
numbers (the 555 does); op-amp symbols (the triangle) do not, so
the rule doesn't bite.

Pin sides: signal pins on the left (`IN+`, `IN-`) and right
(`OUT`); power pins top/bottom (`V+`, `V-`). `metadata.symbol:
"Opamp"` for Schemdraw's triangle element.

## Acceptance Criteria

- [ ] `ic/opamp_dual_supply` profile validates; `circuit.yml` referencing it parses without S5 errors.
- [ ] Golden SVG fixture for a non-inverting buffer renders, with the triangle symbol, signal pins on left/right, power pins top/bottom.
- [ ] `.claude/skills/circuit/docs/components.md` ICs table gains a row for `ic/opamp_dual_supply` (the row joins the table introduced by TASK-121).
- [ ] No regression on existing fixtures.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/components/test_opamp_profile.py`.
- Cover: profile auto-discovery, symbolic-pin resolution
  (`U1.IN+`, `U1.V-`), power-pin direction (`V+` is `direction:
  "in"`, never `bidir`), golden-SVG byte-identity for the
  non-inverting buffer.

## Documentation

- `.claude/skills/circuit/docs/components.md` — adds the
  `ic/opamp_dual_supply` row to the ICs table started in
  TASK-121.

## Prerequisites

- **TASK-110** — frozen decisions: symbolic pin keys (not
  silkscreen-numbered).

## Notes

- Single-supply (rail-to-GND) op-amp topologies are explicitly
  out of scope per IDEA-009 *Out of scope*. Adding a
  `ic/opamp_single_supply` profile is a future iteration with its
  own power-pin ERC rule and biasing convention.
- The `V+` / `V-` keys contain literal `+` and `-` characters in
  YAML. Schema-time validation must accept them as valid pin
  names (the existing schema may already allow this — confirm
  during task-active phase).
