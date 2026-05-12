---
id: TASK-033
title: Implement netlist_exporter.py — flatten NetGraph to KiCad .net
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Senior
human-in-loop: No
epic: circuit-exporters
order: 3
prerequisites: [TASK-008]
---

## Description

Implement `.claude/skills/circuit/netlist_exporter.py`. Walks the
shared `NetGraph` (TASK-008), flattens to a canonical list of nets
keyed by net name, serialises to KiCad-compatible `.net` format,
writes `main-circuit.net` alongside the SVG.

Flattening rules are specified in `idea-001.exporters.md §Flattening`
— shared anonymous nets (`path` and `bus` forms) get synthetic names
(`N1`, `N2`, ...) and named nets (`pins` form) keep their declared
names. The exporter never re-parses YAML or re-walks components —
`NetGraph` is the single source of truth for topology.

## Acceptance Criteria

- [ ] `netlist_exporter.py` produces `main-circuit.net` for both shipped targets.
- [ ] Named nets (`pins` form, e.g. `VCC`, `GND`, `SCL`, `SDA`) preserve their declared names.
- [ ] Anonymous nets get synthetic names; numbering is deterministic across two runs.
- [ ] Output is a valid KiCad `.net` file (parses with `kicad-cli` if available, or via a syntax sanity check).

## Test Plan

Add `tests/test_netlist_exporter.py` covering: net naming determinism, snapshot of `.net` output for `full-pedal` fixture, KiCad parse smoke (skipped if `kicad-cli` not present).

## Prerequisites

- **TASK-008** — `NetGraph` is the exporter's input.

## Notes

KiCad-side parse verification ships in TASK-034 as a manual spot check
to avoid blocking on a KiCad install in CI.
