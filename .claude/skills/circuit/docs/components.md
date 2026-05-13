# Components — Phase 1 library and authoring guide

This page documents the day-one component library and the workflow
for adding new profiles. The authoritative design lives in the
host project's dossier
(`docs/developers/ideas/archived/idea-001.components.md`); this
page is the reader-facing version that ships with the skill.

## Profile shape — three sections

Every profile is a Python dict with three top-level keys:

```python
example = {
    "category": "<layout-engine class>",
    "metadata": { ... },                # label, datasheet, electrical limits
    "pins":     { "<NAME>": { ... } },  # per-pin side, type, direction
}
```

- `category` keys the layout engine's canonical-slot table (not
  semantics). User-writable values: `led`, `resistor`, `capacitor`,
  `button`, `i2c-sensor`, `header`, `jack`, `ic`.
- `metadata` carries human-readable identity (`label`, `manufacturer`,
  `datasheet`) and electrical constraints used by ERC (`vcc_min`,
  `vcc_max`, `max_gpio_current_ma`, `max_total_current_ma`).
  `metadata.keywords` is a lowercase-NFKC vocabulary the rule catalog
  intersects with to decide which educational rules surface.
- `pins` is an ordered map (insertion-order preserved). Every pin
  declares `side` (`top|bottom|left|right`), `type` (open string —
  conventions: `GPIO`, `POWER`, `GROUND`, `INPUT_ONLY`, `RESET`,
  `ANODE`, `CATHODE`, `TERMINAL`, `CONTACT`, `SIGNAL`, `I2C`, `SPEC`),
  and `direction` (`in|out|bidir`). Optional: `pull`, `is_strapping`,
  `func`, `alt`, `display_label`, `required`.

A few rules the schema enforces:

- `type: INPUT_ONLY` ⇒ `direction: "in"`.
- `type: GROUND` ⇒ `direction: "in"`.
- `type: POWER` ⇒ `direction: "in" | "out"`, never `bidir`.
- `type: GPIO` ⇒ `direction: "bidir"` (firmware-directional; the
  per-use direction lives on `.circuit.yml` nets via `role:`).
- `is_strapping: True` forbids an internal `pull:` on the same pin.

## Day-one library

### `mcus.py`

| Profile | Board | Category | Key metadata |
|---|---|---|---|
| `esp32`     | Joy-IT SBC-NodeMCU-ESP32 (30-pin)         | `ic` | Vcc 3.0–3.6 V; 12 mA / GPIO; 200 mA total |
| `nrf52840`  | Adafruit Feather nRF52840 Express (#4062) | `ic` | Vcc 1.7–3.6 V; 14 mA / GPIO; 200 mA total |

Both are **dev-board** profiles per ADR-0010: pin names follow the
header silkscreen (`D34`, `VIN`, `A0`, …), silicon identifiers
(`IO34`, `P0.04`, …) live in each pin's `alt:` field. The
`display_label` field overrides what the renderer prints next to a
pin when the silkscreen text differs from the dict key — e.g.
`VP (D36)`, `D13 P1.09`.

ESP32 strapping pins exposed on the header: `D2`, `D5`, `D12`, `D15`.
ESP32 input-only pins: `D34`, `D35`, `VP` (IO36), `VN` (IO39).
ESP32 default I²C pinning: SDA on `D21`, SCL on `D22`.

nRF52840 has no boot-strapping pins (boot mode set by UICR).
Adafruit Feather default TWI: SDA on `SDA` (P0.12), SCL on `SCL`
(P0.11).

### `passives.py`

| Profile     | Category   | Notes |
|---|---|---|
| `resistor`  | `resistor` | 2-pin generic. |
| `capacitor` | `capacitor`| 2-pin non-polarised. |
| `LED`       | `led`      | Unified profile with colour-indexed `v_forward_by_color` (red 2.0 V, green/yellow 2.1 V, amber 2.0 V, blue/white 3.2 V); `v_forward_default = 2.0`. Select via `{ color: ... }` on the component entry. |
| `pushbutton`| `button`   | Two electrically symmetric contacts on opposite sides. |
| `piezo`     | `resistor` | 2-pin inline passive — `category: resistor` keys layout; `metadata.symbol: "Speaker"` picks the rendering symbol. |

### `connectors.py`

| Profile               | Category | Notes |
|---|---|---|
| `usb_c`               | `jack`   | VBUS / GND / D+/D- / CC1 / CC2 (subset wired). |
| `dc_jack_2_1mm`       | `jack`   | Centre-positive convention; tip is POWER, sleeve is GND. |
| `mono_jack_6_35mm`    | `jack`   | Edge-mounted; `.circuit.yml` narrows direction via net-level `role:`. |
| `stereo_jack_6_35mm`  | `jack`   | TRS — tip, ring, sleeve. |
| `PIN_HEADER_2/3/4/6/8`| `header` | Materialised from `make_header(n)` at module import. |
| `SCREW_TERMINAL_2/3`  | `header` | Materialised from `make_screw_terminal(n)`. |

Adding a new size (e.g. `PIN_HEADER_10`) is a one-line append.

### `sensors.py`

| Profile   | Category      | I²C address | Notes |
|---|---|---|---|
| `bme280`  | `i2c-sensor`  | `0x76`      | Bosch temperature / humidity / pressure. The 0x77 variant ships on some breakouts (SDO tied to VDDIO). |
| `ssd1306` | `i2c-sensor`  | `0x3C`      | Solomon Systech 128×64 OLED; `category: i2c-sensor` keys layout, not semantics — see ADR-0010 / dossier footnote ³. |

Data-line pins on `i2c-sensor` profiles use `type: I2C` with
`func: ["I2C_SDA" | "I2C_SCL"]`. Both halves are schema-required so
ERC E7 (I²C pull-up check) activates.

## Authoring a new profile

The schema auto-discovers profiles at validation time —
`schema/registry.py` walks `components/*.py` and pulls every
top-level dict whose keys are a superset of `{category, metadata,
pins}`. So:

- **Adding a profile within an existing category** — drop a new dict
  into a thematically fitting file (`passives.py`, `sensors.py`, …).
  The schema picks it up on the next `validate()` call; no manual
  schema edit required.
- **Adding a profile in a new theme** — create a new
  `components/<theme>.py` (e.g. `components/regulators.py`). The
  schema's type prefix is `<theme>/<dict_name_lowercase>`. Still no
  schema edit required.
- **Adding a brand-new category** — touches the layout-engine
  concept doc as well (a new §5.3 row). This is a multi-file change,
  not in scope for a Phase 1 reader; see the dossier's "Adding a
  Component — workflow" section.

A profile-authoring checklist:

1. Look up the datasheet pinout and electrical limits.
2. Pick the `category` from the layout engine's vocabulary.
3. Write the profile dict with `category`, `metadata`, `pins`. Every
   pin needs `side`, `type`, `direction`. Add `is_strapping`,
   `func`, `alt`, `display_label` as the silicon warrants.
4. Add `metadata.keywords` (lowercase NFKC) if the profile
   participates in any educational rule.
5. Validate against the schema:

   ```python
   from circuitsmith.schema import validate
   # … load your circuit.yml that references the new profile …
   findings = validate(circuit)
   assert not findings
   ```

6. Mention the new profile in `CHANGELOG.md`'s `[Unreleased]`
   section.

## Component-level variant selection

The unified `LED` profile is the worked example. One profile
parameterises over the colour axis via a lookup table in `metadata`:

```python
LED = {
    "category": "led",
    "metadata": {
        "v_forward_by_color": {"red": 2.0, "green": 2.1, ...},
        "v_forward_default": 2.0,
    },
    "pins": {"A": ..., "K": ...},
}
```

`.circuit.yml` selects a colour:

```yaml
D1: { type: passives/led, color: green, label: PWR_LED }
```

ERC E3 (current-limit calculation) reads
`v_forward_by_color[color]`; an unrecognised or omitted `color:`
falls back to `v_forward_default`. The pattern generalises to any
profile where a single categorical axis varies while schema-visible
structure is constant.

## See also

- [`docs/index.md`](index.md) — install + Hello-circuit.
- Dossier (`docs/developers/ideas/archived/idea-001.components.md` in
  the host project) — the full design argument, including the
  category-keys-layout-not-semantics invariant and the day-one
  library rationale.
