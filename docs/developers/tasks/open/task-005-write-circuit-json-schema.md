---
id: TASK-005
title: Write schema/circuit.schema.json
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: circuit-components
order: 5
prerequisites: [TASK-001, TASK-002, TASK-003, TASK-004]
---

## Description

Author `.claude/skills/circuit/schema/circuit.schema.json` enforcing the
three top-level sections of `.circuit.yml`: `meta`, `components`, and
`connections`. The allowed `type` values must be auto-derived from
whichever `components/*.py` files exist at validation time — adding a
new category file must not require a manual schema edit.

Schema validation is the first stage of the pipeline and is responsible
for rejecting structural errors `S4` (unknown component reference) and
`S5` (unknown pin reference) before any ERC predicate runs.

## Acceptance Criteria

- [ ] `circuit.schema.json` validates the three top-level sections (`meta`, `components`, `connections`) with required keys.
- [ ] `type` values are loaded dynamically from `components/*.py` at validation time (e.g. via a generator script run pre-validation).
- [ ] Validation produces structured findings with check codes `S4`/`S5` for unknown component / unknown pin references.
- [ ] Three connection forms (`pins`, `path`, `bus`) are each validated against their distinct sub-schemas.

## Test Plan

Add `tests/test_schema_validation.py` with pytest fixtures covering: valid esp32 minimal circuit, S4 unknown-component reference, S5 unknown-pin reference, and one well-formed instance per connection form.

## Prerequisites

- **TASK-001** — `mcus.py` provides MCU profiles whose `type` values must be enumerable.
- **TASK-002** — `passives.py` provides passive profiles whose `type` values must be enumerable.
- **TASK-003** — `connectors.py` provides connector profiles whose `type` values must be enumerable.
- **TASK-004** — `sensors.py` provides sensor profiles whose `type` values must be enumerable.

## Notes

See `idea-001.yaml-format.md` for the full `.circuit.yml` format and
the three connection-form sub-schemas. `schema/layout.schema.json` is
a separate deliverable that lands in EPIC-002 alongside the layout
kernel.
