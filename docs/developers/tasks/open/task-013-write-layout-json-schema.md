---
id: TASK-013
title: Write schema/layout.schema.json
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Medium
human-in-loop: No
epic: circuit-renderer-layout
order: 6
prerequisites: [TASK-009]
---

## Description

Author `.claude/skills/circuit/schema/layout.schema.json` — the JSON
Schema that `.layout.yml` files validate against. Matches the slot
vocabulary defined in the kernel (TASK-009), including placements,
regions, capacity overrides, region-anchor overrides, and the topology
fingerprint that detects stale layouts.

## Acceptance Criteria

- [ ] `layout.schema.json` enforces all slot-vocabulary fields per `idea-001.layout-engine-concept.md §4`.
- [ ] Topology fingerprint is a required top-level field — layouts without one fail validation.
- [ ] Three region-anchor override forms are validated against their distinct sub-schemas.
- [ ] Validation produces structured findings that the renderer (TASK-012) can surface.

## Test Plan

Add `tests/test_layout_schema.py` covering: both shipped `layout.yml` files validate green, a layout missing the topology fingerprint fails, an invalid region-anchor override produces a clear error.

## Prerequisites

- **TASK-009** — `kernel.py` defines the canonical slot vocabulary that this schema codifies.

## Notes

See `idea-001.layout-engine-concept.md §4` for the slot vocabulary.
