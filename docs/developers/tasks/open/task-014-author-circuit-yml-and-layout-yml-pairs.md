---
id: TASK-014
title: Author esp32 and nrf52840 .circuit.yml + .layout.yml pairs
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: circuit-renderer-layout
order: 7
prerequisites: [TASK-005, TASK-012, TASK-013]
---

## Autonomy

`Clarification` → `No` per TASK-060 sweep. Example pairs are
illustrative, not load-bearing — pick the most representative and
file an ADR if a pair seems contentious. The golden-hash contract
test (TASK-053) will catch any drift that affects determinism.

## Description

Translate the current `data/config.json` into two
`.circuit.yml` files (`data/esp32.circuit.yml`,
`data/nrf52840.circuit.yml`) and generate matching `layout.yml` pairs by
running the v0.1 kernel against each. This is the topology + layout
seed for the cutover (TASK-015).

The `.circuit.yml` files are authored *by hand* (the AI placer is a
Phase 2b feature); the `.layout.yml` files are kernel-generated. Both
shipped circuits must be rubric-green out of the gate — any rubric
failures here are real layout work, not a TASK-015 carry-over.

## Acceptance Criteria

- [ ] `data/esp32.circuit.yml` and `data/nrf52840.circuit.yml` exist and validate green against `circuit.schema.json`.
- [ ] Both files capture every component and connection in `data/config.json` (no information loss in the translation).
- [ ] Running the kernel against each produces a `layout.yml` that is rubric-green per TASK-011.
- [ ] The resulting SVGs match the "readable, not pretty" bar per `layout §16.2`.

## Test Plan

Add `tests/test_full_pedal_fixture.py` confirming that running the renderer over both `.circuit.yml` files produces SVGs whose XML element count and `data-ref` attributes match the committed `full-pedal` fixture (TASK-015).

## Prerequisites

- **TASK-005** — `.circuit.yml` files must validate against the schema.
- **TASK-012** — the renderer must produce SVGs from these files.
- **TASK-013** — generated `.layout.yml` files must validate against the layout schema.

## Notes

`data/config.json` is the existing source-of-truth. Translation is
hand-driven; verify pin assignments against the manufacturer
datasheets if anything looks ambiguous.

## Predecessor source

`data/config.json` lives in
[AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/data/config.json),
not in CircuitSmith. TASK-001 brings it into this repo alongside
`scripts/generate-schematic.py` as the IDEA-019 baseline; this task translates
that file into the two `.circuit.yml` pairs.
