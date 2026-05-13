---
id: TASK-013
title: Write schema/layout.schema.json
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Small (<2h)
effort_actual: Small (<2h)
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

- [x] `layout.schema.json` enforces all slot-vocabulary fields per `idea-001.layout-engine-concept.md §4`. _Region enum covers `mcu-center`/`left-column`/`right-column`/`top-row`/`bottom-row`/`free` plus the three dynamic region patterns (`path-of-…`, `bus-…`, `pin-symbol-…`). The `attach-index-redundant` §4.2 rule is enforced by an `allOf` `if/then`._
- [x] Topology fingerprint is a required top-level field — layouts without one fail validation. _`topology-fingerprint` is in `placement.required` and the pattern matches `sha1:` / `sha256:` digests. `test_missing_topology_fingerprint_fails` verifies._
- [x] Three region-anchor override forms are validated against their distinct sub-schemas. _`capacity-overrides` (rows/cols), `region-anchor-overrides` (dx/dy), and the per-placement `gx`/`gy` for `free` slots each have their own `$defs` entry; `test_region_anchor_overrides_*` and `test_free_slot_*` cover each form._
- [x] Validation produces structured findings that the renderer (TASK-012) can surface. _`schema/layout_validator.py:validate_layout()` returns `list[Finding]` matching the circuit-side validator's contract (`check`, `severity`, `message`, `location`)._

## Test Plan

Add `tests/test_layout_schema.py` covering: both shipped `layout.yml` files validate green, a layout missing the topology fingerprint fails, an invalid region-anchor override produces a clear error.

## Prerequisites

- **TASK-009** — `kernel.py` defines the canonical slot vocabulary that this schema codifies.

## Notes

See `idea-001.layout-engine-concept.md §4` for the slot vocabulary.
