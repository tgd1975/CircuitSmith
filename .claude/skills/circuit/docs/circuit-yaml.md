# `.circuit.yml` format reference

> Audience: contributors authoring circuits. Companion design doc:
> [`docs/developers/ideas/archived/idea-001.yaml-format.md`](../../../../docs/developers/ideas/archived/idea-001.yaml-format.md).
> Layout engine consumer: [`layout.md`](layout.md).

A `.circuit.yml` describes a circuit declaratively in three top-level
sections: `meta`, `components`, `connections`. The renderer
([`renderer.py`](../renderer.py)) takes one file and produces an SVG,
an updated `layout.yml`, and a `meta.yml` sidecar.

## Top-level structure

```yaml
meta:
  title: ESP32 default build
  target: esp32

components:
  U1:  { type: mcu/esp32,           label: ESP32 }
  R1:  { type: passives/resistor,   value: 220 }
  D1:  { type: passives/led,        color: green }
  J1:  { type: connectors/usb_c,    label: Power }

connections:
  - net: PWR_LED
    path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]
  - net: GND
    pins: [J1.GND, U1.GNDL]
  - net: VCC
    pins: [J1.VBUS, U1.VIN]
```

### `meta`

| Key | Required | Meaning |
|---|---|---|
| `title` | yes | Drives the SVG `<title>` and the ERC report header |
| `target` | yes | Selects the MCU profile and the per-target pin defaults |
| `config` | no | Optional path to a pin-alias file (legacy) |
| `aliases` | no | Map of `REF.PIN → friendly-name` for human-facing surfaces |
| `erc` | no | Per-circuit ERC severity overrides, e.g. `{ E9: warn }` |

### `components`

Each key is a reference designator (`U1`, `R1`, `SW_A`, …). The value
names a profile from the library plus any per-component metadata.

```yaml
components:
  U1:  { type: mcu/esp32,         label: ESP32 }
  R1:  { type: passives/resistor, value: 220 }
  D1:  { type: passives/led,      color: green }
```

Profile names follow the `<file_stem>/<dict_name>` convention
documented in [`components.md`](components.md). Adding a new
profile is a code change in `.claude/skills/circuit/components/*.py`,
not a `.circuit.yml` change.

### `connections`

Every entry is a named net plus exactly one of the three connection
forms below. The schema enforces "exactly one form per entry"; mixing
`pins` and `path` is a schema error.

## Form 1 — `pins` (unordered set)

For pins that join with no intermediate component between the listed
endpoints. Used for power rails, ground rails, and direct wire joins.

```yaml
- net: GND
  pins: [J1.GND, U1.GNDL, SW1.2, D1.K]

- net: VCC
  pins: [J1.VBUS, U1.VIN]
```

Listing multiple pins of the same component is allowed and means those
pins are shorted on this net.

## Form 2 — `path` (ordered sequence)

For signal paths through intermediate components — filter networks,
LED+resistor chains, button debouncers, any sequence of passives
between a source and a destination.

```yaml
- net: PWR_LED
  path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]
```

The flattener groups consecutive tokens of the same component into
nodes, then turns each edge between adjacent nodes into a wire
**segment**:

```text
path:  [U1.D25,    R1.1, R1.2,    D1.A, D1.K,    GND]
nodes: [U1.D25] | [R1.1, R1.2] | [D1.A, D1.K] | [GND]
segments:        ↑ PWR_LED      ↑               ↑
                                PWR_LED__R1_2__D1_A
                                                PWR_LED__D1_K__GND
```

- The **first segment** carries the declared net name (`PWR_LED`).
- Subsequent segments take a content-addressed name:
  `<net>__<RefA>_<pinA>__<RefB>_<pinB>`. Names are stable across
  edits — inserting a new path entry never renumbers other segments.
- A segment terminating at a **bare net name** (no `.`) **merges**
  the adjacent pin into the named net's membership. In the example
  above, `D1.K` joins `GND`'s pin list automatically.

When PCB-side naming matters, override the auto names with
`segment_names`:

```yaml
- net: PWR_LED
  path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]
  segment_names: [PWR_LED_DRIVE, PWR_LED_ANODE, PWR_LED_RETURN]
```

Length must match the segment count exactly; mismatch is a validation
error.

## Form 3 — `bus` (shared backbone with taps)

For a conductor shared by three or more components — I²C, SPI, power
rails with multiple consumers.

```yaml
- net: I2C_SDA
  bus: true
  backbone: [U1.D21, OLED.SDA]
  taps:     [IC1.SDA, R2.2]
```

- `backbone` is a list of two or more pins on the main wire; the
  renderer spaces them at equal intervals.
- `taps` are dropped perpendicularly off the backbone — the
  distinction is visual, not electrical. KiCad netlist sees one
  electrical net containing every backbone pin plus every tap.

## Net-level attributes

Two keys apply uniformly across all three forms.

### `pull` — pull specification for input nets

```yaml
- net: BTN_A
  path: [U1.D13, SW1.1, SW1.2, GND]
  pull: firmware           # or `hardware_up`, `hardware_down`
```

ERC's E1 check requires a `pull:` declaration on every net containing a
signal-input pin (or an external pull-up/pull-down resistor on the same
net). `pull:` is **net-level** — never per-pin, never under `pins[*]`
or `path[*]`.

### `role` — per-use direction for `GPIO`-typed pins

For nets where an MCU GPIO pin's runtime direction differs from its
profile default (`bidir`):

```yaml
- net: BTN_A
  path: [U1.D13, SW1.1, SW1.2, GND]
  role: in
```

When a net touches two or more GPIO pins, the scalar form is rejected;
promote to a map keyed by `REF.PIN`:

```yaml
- net: I2C_SDA
  bus: true
  backbone: [U1.D21, OLED.SDA]
  role:
    U1.D21: bidir
```

## Schema validation

Every `.circuit.yml` runs through two-phase validation before the
renderer touches it:

1. **JSON Schema** ([`circuit.schema.json`](../schema/circuit.schema.json))
   — structural shape, identifier patterns, the `oneOf` connection-form
   rule.
2. **Post-schema validator** ([`schema/validator.py`](../schema/validator.py))
   — pin reference resolution (S5) and component-type resolution (S4).

The renderer halts with a non-zero exit code on any finding.

## Markdown `circuit` blocks (preview)

EPIC-005 lands the integration that lets a Markdown document embed
`.circuit.yml` content directly:

````markdown
```circuit
meta:
  title: Inline button demo
  target: esp32
components:
  U1: { type: mcu/esp32 }
  SW1: { type: passives/pushbutton }
connections:
  - { net: BTN_A, path: [U1.D13, SW1.1, SW1.2, GND], pull: firmware }
```
````

The pre-commit hook (TASK-038) and the block-rewrite tool (TASK-036)
ship in EPIC-005. Today the canonical path is a stand-alone
`<name>.circuit.yml` file passed to the renderer via
`--circuit <path>`.

## Staleness detection

CI re-runs the renderer over every committed `.circuit.yml` and
compares the output against the committed fixture
(`tests/fixtures/full-pedal/<target>/expected.svg`). Drift fails the
build under `tests/test_renderer_staleness.py`. The fix is to re-run
the renderer locally and re-commit, not to patch SVG / `layout.yml`
by hand.

## Complete worked example

```yaml
meta:
  title: ESP32 NodeMCU default build
  target: esp32

components:
  U1:    { type: mcu/esp32,         label: ESP32 }
  J1:    { type: connectors/usb_c,  label: Power }
  R_PWR: { type: passives/resistor, value: 220 }
  D_PWR: { type: passives/led,      color: blue,  label: PWR }
  SW_A:  { type: passives/pushbutton, label: BTN_A }

connections:
  - net: VCC
    pins: [J1.VBUS, U1.VIN]
  - net: GND
    pins: [J1.GND, U1.GNDL]
  - net: LED_PWR
    path: [U1.D2, R_PWR.1, R_PWR.2, D_PWR.A, D_PWR.K, GND]
  - net: BTN_A
    path: [U1.D13, SW_A.1, SW_A.2, GND]
    pull: firmware
```

See the host project's shipped `.circuit.yml` fixtures (e.g.
`esp32.circuit.yml`, `nrf52840.circuit.yml`) for the full-pedal
reference circuits this skill ships with.

See also:

- [`layout.md`](layout.md) — slot vocabulary, rubric, `meta.yml`.
- [`components.md`](components.md) — the component library + profile
  contract.
- [`docs/developers/ideas/archived/idea-001.yaml-format.md`](../../../../docs/developers/ideas/archived/idea-001.yaml-format.md)
  — design rationale and rejected alternatives.
