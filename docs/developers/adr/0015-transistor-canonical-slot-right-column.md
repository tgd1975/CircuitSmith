---
id: ADR-0015
title: BJT canonical slot is `right-column` next-free, base resistor attached
status: Accepted
date: 2026-05-14
dossier-section: docs/developers/ideas/archived/idea-001.layout-engine-concept.md#17.3-remaining-risks
---

## Context

EPIC-014 / TASK-120 introduces the first active-device profiles
(`actives/bjt_npn`, `actives/bjt_pnp`). The dossier
(`idea-001.layout-engine-concept.md` §17.3) explicitly defers the
§5.3 canonical-slot row for transistors to whichever task adopts
them — neither IDEA-009 nor the EPIC-014 frozen-decisions table
fixes a placement, only the pin-key convention (`B`/`C`/`E` with
per-pin `role:`).

The CE-amplifier smoke fixture this task ships needs *some*
placement to render. The choices considered:

1. **`right-column` next-free** — same region used for LEDs,
   buttons, and I²C sensors with right-side dominant pins. Treats
   the BJT as "an MCU-driven device that sinks to GND," matching
   the common-emitter-from-GPIO case (and the
   PNP-emitter-to-VCC case via the same geometry mirrored).
2. **`path-of-<MCU.PIN>`** — place the BJT inline on the base-
   drive path, like a series resistor. Forces the kernel to
   recognise the BJT as a 3-terminal interruption of the path,
   which the v0.1 path-flattener does not model.
3. **`free` slot only** — refuse to auto-place; require the
   author or the AI placer to hand-position every transistor.
   Rejected: the CE-amp fixture is a routine maker shape and
   should not require manual layout.

## Decision

A `category: transistor` lands in `region: right-column`,
`row: next-free`. A resistor whose path joins the BJT's base
(`B`) becomes `attached-to:` the BJT, sharing the slot —
identical to the resistor-rides-with-LED rule already in the
canonical-slot table.

The two-side allocation in the profile (`B` on left, `C`/`E` on
right) lets schemdraw orient the symbol naturally inside the
right-column slot: base on the column's inner edge facing the
MCU, collector and emitter facing outward. The `role:` field on
each pin is read by TASK-123's ERC (pin-role-unset rule) and is
available to future layout rules that distinguish CE / CC / CB
configurations.

When the topology departs from "MCU-driven, single device" — e.g.
push-pull pairs, current mirrors, regulator output stages — the
kernel raises `no-canonical-rule` and the AI placer (Phase 2b)
handles it.

## Consequences

**Easier:**

- The CE-amp fixture renders deterministically without manual
  layout authoring; the canonical-slot rule reuses the
  attached-to mechanism already proven on R+LED pairs.
- Adding a transistor to an existing circuit produces a
  single-line `layout.yml` diff (the `next-free` invariant
  carries over).

**Harder:**

- Multi-transistor topologies (push-pull, differential pair,
  current mirror) all escalate to the AI placer. A future ADR
  can split the rule when those shapes appear in real circuits;
  the §17.3 framing explicitly leaves that growth path open.
- The decision binds NPN and PNP to the same slot family;
  visually they sit interchangeably in the right column. A
  later refinement can route PNPs to a power-rail-side slot
  for clarity if the right-column gets crowded.

## See also

- [idea-001.layout-engine-concept.md §17.3](../ideas/archived/idea-001.layout-engine-concept.md)
  — the dossier framing for "new categories enter §5.3 one row
  at a time" plus the AI-placer escalation hook.
- [ADR-0001](0001-slots-not-coordinates.md) — slot vocabulary
  this decision adds a row to.
- [TASK-120](../tasks/active/task-120-component-profile-bjt-npn-and-pnp.md)
  — the implementing task.
