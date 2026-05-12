---
id: TASK-002
title: Write components/passives.py
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-components
order: 2
---

## Description

Author `.claude/skills/circuit/components/passives.py` with the day-one
passive component library: resistor, capacitor, **unified LED profile**
(with `v_forward_by_color` per the component-level variant-selection
pattern in `idea-001.components.md`), pushbutton, piezo buzzer.

The unified LED profile is deliberate — colour is a variant of one
component type, not five separate types. This keeps the BOM grouping
correct (one LED row per `(type, color)` pair) and the schema simple.

## Acceptance Criteria

- [x] `passives.py` defines `resistor`, `capacitor`, `LED`, `pushbutton`, `piezo` profiles.
- [x] `LED.metadata` declares `v_forward_by_color` covering at least red, green, blue, yellow, white. (Also amber.)
- [x] Every profile declares `metadata.keywords` (lowercase NFKC tokens).
- [x] Every pin declares `type` and `direction` (the fields ERC keys on).

## Test Plan

No automated tests required — the profile library is reference data validated structurally by the JSON Schema in TASK-005 and consumed by the renderer in TASK-012.

## Notes

The piezo deliberately rides on `category: resistor` (identical layout
shape) — `category` keys layout, not semantics. See the design
invariant note at the top of `idea-001.components.md`.
