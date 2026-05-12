---
id: TASK-001
title: Extract ESP32 and nRF52840 board profiles into components/mcus.py
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Medium
human-in-loop: Clarification
epic: circuit-components
order: 1
prerequisites: [TASK-046, TASK-047, TASK-048]
---

## Description

The existing `scripts/generate-schematic.py` hard-codes both shipped MCU
board definitions inline. This task extracts both into full component
profiles in `.claude/skills/circuit/components/mcus.py`, following the
three-section structure (`category`, `metadata`, `pins`) defined in
`docs/developers/ideas/archived/idea-001.components.md`.

Each profile must declare full electrical metadata so downstream ERC
checks (E1 current-budget, E2 strapping pins, E10 pin conflict) have
the values they need: `vcc_min`, `vcc_max`, `max_gpio_current_ma`,
`max_total_current_ma`, plus per-pin `is_strapping` flags.

## Acceptance Criteria

- [ ] `.claude/skills/circuit/components/mcus.py` defines `esp32` and `nrf52840` profiles with `category`, `metadata`, and `pins` sections.
- [ ] Every pin entry declares `name`, `side`, `type`, `direction`, and (where applicable) `is_strapping` and `func`.
- [ ] Each profile declares `metadata.keywords` as lowercase NFKC tokens.
- [ ] Electrical metadata is sourced from manufacturer datasheets and cited inline in profile comments.

## Test Plan

No automated tests required at this task — TASK-006 (refactor `generate-schematic.py`) provides the integration test by comparing pre/post SVG output for byte identity.

## Prerequisites

- **TASK-046** — `pyproject.toml` declares the runtime deps the profiles will import (`schemdraw` is needed for the eventual renderer; `ruamel.yaml` for the schema).
- **TASK-047** — pytest is configured before any test scaffolding lands.
- **TASK-048** — CI runs the tests, so a Phase 1 PR has a green gate.

## Notes

Cross-references: `idea-001.components.md` (profile format, initial library); `idea-001.erc-engine.md` (which ERC fields each piece of metadata feeds).

## Predecessor source

`scripts/generate-schematic.py` lives in
[AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/scripts/generate-schematic.py),
not in CircuitSmith. The first step of this task is to bring that script (and
its referenced data) in as the baseline before extracting profiles. The script
will be deleted in TASK-015 (cutover); it only exists in this repo for the
duration of the refactor.
