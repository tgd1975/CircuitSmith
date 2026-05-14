---
id: TASK-120
title: Component profile — bjt_npn and bjt_pnp
status: open
opened: 2026-05-14
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 11
prerequisites: [TASK-110]
---

## Description

Adds the BJT component profiles to a new file
`src/circuitsmith/components/actives.py`. Two profiles in this task
(`bjt_npn` + `bjt_pnp`) — they share the same pin convention and
ship together.

Per IDEA-009 *Open questions* (frozen in TASK-110), pin keys are
`B` / `C` / `E` matching the standard schematic-symbol convention.
Direction sensitivity (CE amp vs CC follower vs CB amp) is
annotated with a per-pin `role:` field — `pins.B.role: "base"`,
`pins.C.role: "collector"`, `pins.E.role: "emitter"`. Layout rules
read `pin.role` directly (no separate metadata table).

Schemdraw dispatch via `metadata.symbol: "Bjt"` and `"BjtPnp"`. The
profiles are auto-discovered by
[`schema/registry.py`](../../../src/circuitsmith/schema/registry.py)
on the next `validate()` call.

## Acceptance Criteria

- [ ] `bjt_npn` and `bjt_pnp` profiles validate; a `circuit.yml` referencing them parses without S5 errors.
- [ ] Golden SVG fixture for a CE amplifier renders, exercising the `role:`-driven layout.
- [ ] `.claude/skills/circuit/docs/components.md` gains an "Active devices" table with rows for the two BJT profiles.
- [ ] No regression on existing fixtures.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/components/test_bjt_profiles.py`.
- Cover: profile auto-discovery (registry picks up `actives.py`),
  `role:` field validates per pin, schema rejects a BJT instance
  with a missing `role` (this is the input to TASK-123's
  pin-role-unset rule), golden-SVG byte-identity for the CE
  amplifier.

## Documentation

- `.claude/skills/circuit/docs/components.md` — new "Active
  devices" table with `bjt_npn` and `bjt_pnp` rows.

## Prerequisites

- **TASK-110** — frozen decisions: `pins.X.role:` shape (not
  `metadata.bjt_terminals`).

## Notes

- The `complexity: Senior` rating reflects the analog-signal-flow
  layout judgement, not the profile authoring itself. Picking the
  right `role:` semantics for downstream layout rules is the
  cross-cutting concern.
- FET / Darlington / multi-emitter profiles are explicitly out of
  scope per IDEA-009 *Out of scope*. They follow the same shape
  in a future iteration.
