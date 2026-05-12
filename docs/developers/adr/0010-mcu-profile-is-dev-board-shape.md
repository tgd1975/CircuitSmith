---
id: ADR-0010
title: MCU profiles in components/mcus.py describe the dev-board pinout, with silicon metadata at the chip level
status: Accepted
date: 2026-05-12
dossier-section: docs/developers/ideas/archived/idea-001.components.md
---

## Context

[`idea-001.components.md`](../ideas/archived/idea-001.components.md) shows
the `ESP32_WROOM_32` profile example using silicon-level pin names
(`IO0`, `IO34`, `IO36 alt:VP`), but TASK-001's acceptance criteria
name the profile dicts `esp32` and `nrf52840` (lowercase) and the
predecessor [`scripts/generate-schematic.py`](../../../scripts/generate-schematic.py)
inherited from AwesomeStudioPedal enumerates the **dev-board header
pins** (`D34`, `VP`, `VIN`, `EN`, `3.3V`, …), not the raw silicon
pinout (38 pins for ESP32-WROOM-32, ~48 for nRF52840). Two readings
of "MCU profile" are possible:

1. **Silicon profile** — enumerate every chip pin; dev-board layout
   stays elsewhere. Pure but disconnected from what the generator
   consumes.
2. **Dev-board profile** — enumerate the pins the dev board breaks
   out to headers; carry silicon-level electrical metadata (Vcc
   range, current limits, strapping flags) on each pin via direct
   mapping. Pragmatic and what the byte-identity refactor needs.

## Decision

Adopt reading **(2)**. `.claude/skills/circuit/components/mcus.py`
ships two profile dicts named `esp32` and `nrf52840` whose `pins`
sections enumerate the dev-board headers (Joy-IT NodeMCU-32S and
Adafruit Feather nRF52840 Express, respectively — the two boards the
predecessor script targets). Each pin entry carries:

- **Pin name** — the dev-board label (`D34`, `VIN`, `EN`, `3.3V`,
  `A0`, …). This is what `.circuit.yml` and the generator reference.
- **`alt:`** — the silicon pin identifier when it differs from the
  board label (`IO34`, `P0.04`, `P0.11`, …). Datasheet aliases like
  `VP` → `IO36` also use this field.
- **`type` / `direction` / `is_strapping` / `func`** — derived from
  the silicon role, not the board label.
- **Chip-level `metadata`** (`vcc_min`, `vcc_max`,
  `max_gpio_current_ma`, `max_total_current_ma`) — sourced from the
  silicon datasheet and cited inline.

## Consequences

**Easier:**

- The TASK-006 byte-identity refactor: the generator iterates the
  profile's pin list directly, so the SVG output is mechanically the
  same.
- ERC checks E1, E2, E10 read silicon-level metadata at the pin or
  profile level without any cross-table lookup.
- Hand-authoring `.circuit.yml` references familiar dev-board labels
  (`D21`, `D22`, `A0`) — what's printed on the silkscreen — rather
  than silicon identifiers.

**Harder:**

- A future "swap the dev board for the bare chip on a PCB" workflow
  needs either a second profile (`esp32_wroom_32_bare`) or a profile
  variant. We do not ship that today.
- Pins on the chip but not on the dev-board header (e.g. ESP32 IO0,
  IO6–IO11 internal flash) are absent from the profile and therefore
  invisible to ERC. This is acceptable for makers using dev boards;
  bare-chip projects need a separate profile when they land.

## See also

- [TASK-001](../tasks/active/task-001-extract-mcu-board-profiles.md)
  — the task that ships these profiles.
- [`idea-001.components.md`](../ideas/archived/idea-001.components.md)
  — three-section profile structure and electrical-metadata contract.
- [`scripts/generate-schematic.py`](../../../scripts/generate-schematic.py)
  — predecessor with the inline dev-board pin tables.
- [ADR-0007](0007-skill-directory-is-the-library.md) — the skill
  directory is the library; this profile lands there.
