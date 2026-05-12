---
id: ADR-0004
title: `bom_exporter` walks `components`; `netlist_exporter` walks `NetGraph`; they never cross
status: Accepted
date: 2026-05-12
dossier-section: idea-001-circuit-skill.md §Architecture
---

## Context

A bill of materials (BOM) and a netlist describe orthogonal things:

- A **BOM** is a *parts list* — quantities, manufacturer part
  numbers, package types, prices. It does not care whether pin 7 of
  the MCU is connected to GND or to a sensor.
- A **netlist** is a *connectivity list* — which pins on which
  components are joined by which signal. It does not care whether the
  MCU costs €3.20 or €4.80.

A naive implementation would share a "circuit model" between them and
let each pick out the fields it needs. That coupling is the wrong
trade: the next "convenience" feature (BOM that knows about decoupling
caps, netlist that knows component prices) lands in the shared model
and decays it.

## Decision

The two exporters consume **different inputs** and are forbidden from
sharing helpers:

- `bom_exporter.py` walks the `components` list from `.circuit.yml`.
  It has no awareness of connectivity.
- `netlist_exporter.py` walks `NetGraph` (see [ADR-0003](0003-netgraph-shared-contract.md)).
  It has no awareness of component pricing, BOM grouping, or part
  numbers beyond the reference designator.

This is enforced by the boundary-import contract test (TASK-050).
Neither file imports from the other, and neither imports private
modules of the other.

## Consequences

**Easier:**

- Either exporter can be replaced independently — a different BOM
  format does not touch the netlist code and vice versa.
- The boundary test catches accidental cross-imports at CI time,
  before they harden into a fixture.
- Both exporters are trivially testable in isolation; their
  fixtures are the input format they walk, nothing else.

**Harder:**

- A feature that genuinely needs *both* views (e.g. a per-net cost
  attribution) cannot live in either exporter and has to be a new
  consumer of both inputs at a higher level.
- Refactors that "would be neat to share" — a common
  reference-designator parser, a common unit-formatter — must be
  resisted unless they go through a third, neutral module.

## See also

[`idea-001-circuit-skill.md §Architecture`](../ideas/archived/idea-001-circuit-skill.md)
for the pipeline diagram showing the two parallel exporter paths.
