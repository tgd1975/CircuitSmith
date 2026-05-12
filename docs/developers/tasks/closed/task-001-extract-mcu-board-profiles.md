---
id: TASK-001
title: Extract ESP32 and nRF52840 board profiles into components/mcus.py
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: circuit-components
order: 1
prerequisites: [TASK-046, TASK-047, TASK-048]
---

## Autonomy

`Clarification` → `No` per TASK-060 sweep. Board-profile decisions
have defensible defaults in the dossier; file an ADR for any
non-obvious profile choice rather than pausing.

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

- [x] `.claude/skills/circuit/components/mcus.py` defines `esp32` and `nrf52840` profiles with `category`, `metadata`, and `pins` sections.
- [x] Every pin entry declares `name`, `side`, `type`, `direction`, and (where applicable) `is_strapping` and `func`. (Pin name is the dict key.)
- [x] Each profile declares `metadata.keywords` as lowercase NFKC tokens.
- [x] Electrical metadata is sourced from manufacturer datasheets and cited inline in profile comments. ESP32: ESP32-WROOM-32 datasheet + Joy-IT NodeMCU manual. nRF52840: Nordic PS v1.7 + Adafruit Feather pinout. ADR-0010 documents the dev-board-shape choice for the profile.

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
