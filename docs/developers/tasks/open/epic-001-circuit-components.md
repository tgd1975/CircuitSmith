---
id: EPIC-001
name: circuit-components
title: Circuit Skill — Component Library and Schema
status: open
opened: 2026-05-12
closed:
assigned:
branch: release/epic-001-circuit-components
---

Seeded by IDEA-001 (Circuit-Skill — AI-Assisted Schematic Generation with ERC, BOM, and Netlist Export).

Phase 1 of IDEA-001. Extracts the two hand-coded board definitions from
`scripts/generate-schematic.py` into a structured component library under
`.claude/skills/circuit/components/`, writes the JSON Schema that
`.circuit.yml` files validate against, and refactors the existing generator
to import from the library. No behaviour change — both shipped targets
(ESP32, nRF52840) must produce identical SVG output after this epic closes.

Companion design doc: `docs/developers/ideas/archived/idea-001.components.md`.

**Predecessor source.** `scripts/generate-schematic.py` (and the two reference
SVGs under `docs/builders/wiring/<target>/`) live in
[AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal) — see
[`scripts/generate-schematic.py`](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/scripts/generate-schematic.py)
and
[`docs/builders/wiring/`](https://github.com/tgd1975/AwesomeStudioPedal/tree/main/docs/builders/wiring).
TASK-001 brings them into this repo as the IDEA-019 baseline; the rest of the
epic operates on that baseline.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
