---
id: ADR-0001
title: Slots, not raw coordinates, in `layout.yml`
status: Accepted
date: 2026-05-12
dossier-section: idea-001.layout-engine-concept.md §4
---

## Context

A schematic layout has to be **deterministic** (same input → same
SVG, byte-for-byte) and **reviewable** (a human reading `layout.yml`
should be able to tell whether the placement is sensible without
rendering it). Two representations are on the table:

- Raw `(x, y)` coordinates in millimetres or grid units. Maximally
  expressive; the renderer is a thin pass-through.
- **Slots** — named positions on a canonical grid keyed off the
  schematic's topology (`mcu.left.row[3]`, `bus.power.rail`, etc.),
  with the layout engine assigning components to slots.

Raw coordinates leak rendering concerns into the data model: a `47.3`
in `layout.yml` has no semantic anchor — change the grid pitch and
every coordinate has to move. Slots stay stable across rendering
changes because they are *topological*.

## Decision

`layout.yml` records **slot assignments**, not raw coordinates. The
canonical slot vocabulary lives in
[`idea-001.layout-engine-concept.md §4`](../ideas/archived/idea-001.layout-engine-concept.md);
extensions are added with their semantic anchor stated. The renderer
resolves slot → coordinate at render time using a fixed grid map; the
map is part of the renderer, not the data.

## Consequences

**Easier:**

- Layout reviews focus on placement *intent* (does the MCU sit
  between its decoupling caps?) rather than pixel arithmetic.
- Renderer changes (grid pitch, padding, page size) do not
  invalidate existing `layout.yml` files.
- Diffs on layout changes read as topology changes, not millimetre
  noise.

**Harder:**

- Layouts that genuinely need raw coordinates (a one-off floor-plan
  override) have to add a slot name first. There is no escape hatch
  into raw coordinates — that's the point.
- The slot vocabulary becomes a curated artifact; adding a slot
  requires thinking about whether it's a genuine topological
  position or just a coordinate in disguise.

## See also

[`idea-001.layout-engine-concept.md §4`](../ideas/archived/idea-001.layout-engine-concept.md)
for the slot vocabulary and the resolution algorithm.
