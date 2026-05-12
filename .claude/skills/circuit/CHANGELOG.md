# Changelog — circuit skill

All notable changes to this skill are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
follow [SemVer](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- v0.1 scope (Phase 1 of the dossier) — component library + schema:
  - `components/mcus.py` — `esp32` (Joy-IT NodeMCU-32S) and
    `nrf52840` (Adafruit Feather) dev-board profiles with full
    silicon-electrical metadata: Vcc range, per-GPIO and total
    current budgets, strapping flags, default I²C-pin `func` tags.
  - `components/passives.py` — `resistor`, `capacitor`, unified
    `LED` profile with `v_forward_by_color`, `pushbutton`, `piezo`.
  - `components/connectors.py` — `usb_c`, `dc_jack_2_1mm`, mono /
    stereo 6.35 mm jacks, plus `make_header(n)` and
    `make_screw_terminal(n)` factories materialised at module-import
    for sizes 2 / 3 / 4 / 6 / 8 pins.
  - `components/sensors.py` — `bme280` (I²C environmental sensor) and
    `ssd1306` (I²C 128×64 OLED).
  - `schema/circuit.schema.json` — structural schema for the three
    top-level sections (`meta`, `components`, `connections`) plus the
    three connection forms (`pins`, `path`, `bus`).
  - `schema/validator.py` + `schema/registry.py` — post-schema
    validator that walks `components/*.py` at validation time, builds
    the registry of valid `type:` strings, and emits S4 / S5 findings
    on unknown component / unknown pin references.

### Documentation

- `docs/index.md` — what the skill is, how to install, "Hello,
  circuit" example.
- `docs/components.md` — Phase 1 library reference and profile
  authoring guide.
