---
id: TASK-035
title: Extend CI staleness guard for bom + netlist; update docs/index.md
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-exporters
order: 5
prerequisites: [TASK-031, TASK-033]
---

## Description

Two small changes that close out EPIC-004:

1. Extend the CI staleness guard (last touched in TASK-029) to include
   `bom.md`, `bom.csv`, and `main-circuit.net` for both targets.
2. Update `.claude/skills/circuit/docs/index.md` with the BOM and
   netlist export usage sections (CLI invocation, output paths,
   downstream consumer notes).

## Acceptance Criteria

- [x] CI staleness guard covers all three exporter artefacts per target.
- [x] An induced staleness on any of the three files fails CI cleanly with a clear error.
- [x] `docs/index.md` has BOM and netlist sections explaining when and how to use them.
- [x] Cross-references to `idea-001.exporters.md` resolve.

## Test Plan

CI smoke test: induce staleness in each of the three files on a throwaway branch; confirm CI fails with the expected error. Documentation: visual spot check.

## Prerequisites

- **TASK-031** — `bom.md`/`bom.csv` must exist to guard.
- **TASK-033** — `main-circuit.net` must exist to guard.

## Notes

This closes out EPIC-004.
