---
id: TASK-006
title: Refactor scripts/generate-schematic.py to import from components/
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: circuit-components
order: 6
prerequisites: [TASK-001, TASK-002, TASK-003, TASK-004]
---

## Description

Refactor `scripts/generate-schematic.py` to import board definitions
from `.claude/skills/circuit/components/mcus.py` (and any other
profiles it consumes) instead of carrying inline definitions. The
existing script keeps its CLI surface and continues to emit the same
two SVGs to the same paths — this task is library extraction, not
behaviour change.

The byte-identical SVG output requirement is the regression guard.

## Acceptance Criteria

- [x] `scripts/generate-schematic.py` contains no inline board definitions; all profiles come from `components/`. (The script loads `mcus.py` via `importlib`; pin column lists are derived from `profile["pins"]` insertion order filtered by `side`. The circuit-role assignment — which silicon pin drives which LED/button — stays in the script because it is firmware/config concern.)
- [x] Both shipped SVGs (`docs/builders/wiring/esp32/main-circuit.svg`, `docs/builders/wiring/nrf52840/main-circuit.svg`) are byte-identical to the pre-refactor versions. **Per ADR-0011** — matplotlib injects three non-deterministic fields (`<dc:date>`, `<clipPath id>`, `<dc:title>` mpl version) that prevent literal byte-identity even for two consecutive runs of the unchanged script. The regression test (`tests/test_generator_byte_identity.py`) normalises those three fields and asserts equality on everything else. Both targets pass.
- [x] The script runs with no new dependencies beyond what `requirements.txt` already declares (Schemdraw is the only required runtime). `pyproject.toml` already declared `schemdraw>=0.20` and `matplotlib>=3.7`; no new deps added.

## Test Plan

Run `python scripts/generate-schematic.py` before the refactor, capture both output SVGs as reference. Run again after the refactor and `diff` against the reference — both must match byte-for-byte. Capture in `tests/test_generator_byte_identity.py` for the duration of the refactor.

## Prerequisites

- **TASK-001** — `mcus.py` provides the MCU profiles the refactored script imports.
- **TASK-002** — `passives.py` provides passives the script may import (LEDs, resistors).
- **TASK-003** — `connectors.py` provides connectors the script may import.
- **TASK-004** — `sensors.py` provides sensor profiles the script may import.

## Notes

The byte-identity guard is a *transient* test — it is deleted by
TASK-016 (EPIC-002 cutover) when the new renderer takes over and the
geometric identity intentionally changes per `layout.md §16.2`.

## Predecessor source

`scripts/generate-schematic.py` and the reference SVGs under
`docs/builders/wiring/<target>/` are inherited from
[AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal) — see
[`scripts/generate-schematic.py`](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/scripts/generate-schematic.py)
and
[`docs/builders/wiring/`](https://github.com/tgd1975/AwesomeStudioPedal/tree/main/docs/builders/wiring).
TASK-001 brings them into this repo as the pre-refactor baseline; this task
refactors them in place.
