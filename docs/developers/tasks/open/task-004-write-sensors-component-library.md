---
id: TASK-004
title: Write components/sensors.py
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-components
order: 4
---

## Description

Author `.claude/skills/circuit/components/sensors.py` with the two
day-one sensor profiles: BME280 (temperature/humidity/pressure over
I2C) and SSD1306 128×64 I2C OLED display.

The SSD1306 deliberately rides on `category: i2c-sensor` even though it
is a display — `category` keys layout shape, not electrical semantics.
This is a worked example of the design invariant in
`idea-001.components.md`.

## Acceptance Criteria

- [ ] `sensors.py` defines `bme280` and `ssd1306` profiles.
- [ ] Both profiles declare I2C-specific pins (`SDA`, `SCL`, `VCC`, `GND`) with `type: i2c-data`/`i2c-clock` as appropriate.
- [ ] Both profiles declare `metadata.keywords` (lowercase NFKC tokens).
- [ ] `bme280.metadata` declares `i2c_address: 0x76` (or default per datasheet); `ssd1306.metadata` declares `i2c_address: 0x3C`.

## Test Plan

No automated tests required — the BME280 profile is exercised by the Phase 6 acceptance test (TASK-041) which adds it to a real circuit.

## Notes

`sensors.py` does not exist before this task — the schema
auto-derives allowed `type` strings from whichever `components/*.py`
files exist, so a new category file requires no manual schema update
(see `idea-001-circuit-skill.md` architecture section).
