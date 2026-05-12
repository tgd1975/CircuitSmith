---
id: TASK-031
title: Implement bom_exporter.py — Markdown and CSV
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: circuit-exporters
order: 1
prerequisites: [TASK-001, TASK-002, TASK-003, TASK-004]
---

## Description

Implement `.claude/skills/circuit/bom_exporter.py`. Iterates the
`components` section of a `.circuit.yml` exactly once; groups rows by
`(component.type, variant_key(component))` where `variant_key` is the
per-category projection defined in `idea-001.exporters.md §Variant
projection`.

The BOM exporter does **not** consume `NetGraph`. BOM is a counting
problem, not a topology problem — keeping the exporters decoupled
prevents the netlist's flattening rules from leaking into the BOM
output.

Outputs: `bom.md` (Markdown table for human reading) and `bom.csv`
(CSV for spreadsheet import).

## Acceptance Criteria

- [ ] `bom_exporter.py` produces `bom.md` and `bom.csv` for both shipped targets.
- [ ] Variant grouping follows the per-category projection: two 220 Ω resistors collapse to one row; 220 Ω and 1 kΩ are separate rows; red and green LEDs are separate rows.
- [ ] Markdown output renders correctly in GitHub preview (tested manually).
- [ ] CSV output imports into a spreadsheet without manual cleanup.

## Test Plan

Add `tests/test_bom_exporter.py` covering: grouping for each category's variant key, both Markdown and CSV output shapes match snapshot fixtures, output is deterministic across two runs.

## Prerequisites

- **TASK-001** — MCU profile metadata feeds BOM rows.
- **TASK-002** — passives profiles (LED, resistor) supply the variant fields BOM groups on.
- **TASK-003** — connector profiles supply BOM rows.
- **TASK-004** — sensor profiles supply BOM rows.

## Notes

See `idea-001.exporters.md` for the canonical row format and the
per-category variant projection. The exporter is portability-contract
compliant (path-agnostic).
