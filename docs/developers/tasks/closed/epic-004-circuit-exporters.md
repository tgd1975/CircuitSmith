---
id: EPIC-004
name: circuit-exporters
title: Circuit Skill — BOM and Netlist Exporters
status: closed
opened: 2026-05-12
closed: 2026-05-13
assigned:
branch: release/epic-004-circuit-exporters
---

Seeded by IDEA-001 (Circuit-Skill — AI-Assisted Schematic Generation with ERC, BOM, and Netlist Export).

Phase 4 of IDEA-001. Implements the two downstream exporters:

- **BOM exporter** — walks the `components` section once, groups
  instances by `(type, variant_key)`, emits `bom.md` + `bom.csv`. Never
  consumes `NetGraph`.
- **Netlist exporter** — walks the shared `NetGraph` from EPIC-002,
  flattens to canonical net list, emits KiCad-compatible `main-circuit.net`.

Both exporters are deliberately decoupled (no shared flattening code)
and run independently of ERC findings — a circuit with ERROR-level ERC
findings still produces a BOM and netlist for debugging.

Companion design doc:
`docs/developers/ideas/archived/idea-001.exporters.md`.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
