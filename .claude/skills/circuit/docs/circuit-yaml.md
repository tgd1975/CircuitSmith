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

## Sub-blocks and instances

A `.circuit.yml` may declare reusable mini-circuits in a top-level
`sub-blocks:` map and instantiate them in `instances:`. The
flattener (`flatten_sub_blocks()` in `netgraph.py`) inlines every
instance before the rest of the pipeline runs, so the kernel, ERC,
BOM, and KiCad netlist all see one flat circuit.

```yaml
sub-blocks:
  led_indicator:
    components:
      R: { type: passives/resistor, value: 220 }
      D: { type: passives/led }
    ports:
      drive: R.1
      gnd:   D.K
    connections:
      - net: anode
        path: [R.2, D.A]

instances:
  PWR: { sub-block: led_indicator }
  BT:  { sub-block: led_indicator }
  ERR: { sub-block: led_indicator }

connections:
  - net: LED_PWR
    pins: [U1.D2, PWR.drive]
  - net: GND
    pins: [U1.GNDL, PWR.gnd, BT.gnd, ERR.gnd]
```

### `sub-blocks:` keys

| Key | Required | Meaning |
|---|---|---|
| `components` | yes | Local component map; same shape as the top-level `components:` |
| `ports` | yes | Map of `port-name → <local-refdes>.<pin>`. Surface area of the sub-block |
| `connections` | no | Internal nets; same three forms as top-level (`pins`, `path`, `bus`) |

### `instances:` keys

| Key | Required | Meaning |
|---|---|---|
| `sub-block` | yes | Name of an entry in the top-level `sub-blocks:` map |

The schema rejects any other key on an instance entry — there are
no per-instance overrides for component values, labels, or
metadata in v1. Differentiation lives entirely in how the
surrounding top-level `connections:` wire each instance's ports.

### Flattening contract

Per the [EPIC-014 frozen-decisions table](../../../../docs/developers/tasks/active/epic-014-circuit-library-and-renderer-v2.md#frozen-decisions-task-110):

- **Refdes scheme.** Each local component `<local-refdes>` in an
  instance becomes `<local-refdes>_<instance>` in the flat circuit
  (e.g. `R_PWR`, `D_PWR`). The BOM groups by component class.
- **Port references.** Top-level `connections:` use
  `<instance>.<port-name>` as if the instance were a single
  component with the declared ports as pins.
- **Internal nets.** A net defined inside the sub-block as `anode`
  is minted globally as `<instance>__anode` after flattening so
  nets stay unique across instances.
- **Nested sub-blocks are not allowed in v1.** A sub-block whose
  `components.*.type` references another sub-block is rejected
  by S6 (or by the JSON Schema type pattern, which requires the
  `<file>/<name>` form a profile name has).

### Sub-block-aware ERC checks

| Check | Triggers when |
|---|---|
| `S6` | A sub-block's `components.*.type` resolves to another sub-block name |
| `S7` | An `<instance>.<port>` reference in top-level `connections:` names an undeclared instance or port |
| `E11..E14` | Sub-block contract violations the JSON Schema can't catch (e.g. port maps that reference non-existent local pins) |
| `E15` | Reserved by the kernel's voltage-divider detector for ambiguous `R+R` placements — fires when neither the tap-net regex nor a `role: divider` annotation disambiguates |

See [`erc-checks.md`](erc-checks.md) for the full check catalogue.

### Choosing flat vs sub-block authoring

A sub-block earns its keep when the same shape repeats two or more
times **and** the repetition is structural (LEDs on a status panel,
identical RC filters on each input). A one-off shape stays flat;
sub-block syntax adds two layers of indirection (`ports:` and
`<instance>.<port>` lookups) that don't pay back on a singleton.

Two non-obvious constraints worth designing around:

- The kernel's R+LED rule (and the EPIC-014 RC / CC / RR rules)
  match topology only after flattening, so an `R + LED` chain
  inside a sub-block must use `path:` form for the kernel to
  recognise the pair. `pins:` form skips the R+LED pair detector.
- Every instance is electrically identical — so a sub-block
  exposing per-LED colour is, today, three nearly-identical
  sub-blocks (`led_indicator_blue`, `led_indicator_green`,
  `led_indicator_red`) rather than one sub-block with a colour
  parameter. Parameterised sub-blocks are an explicit non-goal
  for v1.

## Schema validation

Every `.circuit.yml` runs through two-phase validation before the
renderer touches it:

1. **JSON Schema** ([`circuit.schema.json`](../schema/circuit.schema.json))
   — structural shape, identifier patterns, the `oneOf` connection-form
   rule.
2. **Post-schema validator** ([`schema/validator.py`](../schema/validator.py))
   — pin reference resolution (S5) and component-type resolution (S4).

The renderer halts with a non-zero exit code on any finding.

## Markdown `circuit` blocks

The block-rewrite integration lets a Markdown document embed
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

The block-rewrite tool and the pre-commit hook ship as part of
EPIC-005 (closed). The rewriter scans Markdown files for ` ```circuit `
fenced blocks, renders each block's YAML to
`<docname>.circuits/<hash>.svg`, and replaces the block with an image
embed. The 8-char hash in the filename is a SHA-256 prefix of the
verbatim block body — identical sources share an SVG; a one-byte edit
changes the filename and the stale render is detected by file-name
lookup alone.

### `show_source` flag (TASK-037)

Add `show_source` to the fence info string for a `<details>` wrapper
that reveals the verbatim source YAML on click — useful for tutorial
pages where readers benefit from seeing input alongside output:

````markdown
```circuit show_source
meta:
  title: Inline button demo
  target: esp32
components:
  U1:  { type: mcu/esp32 }
  SW1: { type: passives/pushbutton }
connections:
  - { net: BTN_A, path: [U1.D13, SW1.1, SW1.2, GND], pull: firmware }
```
````

After rewrite, that block becomes:

```markdown
<details>
<summary>circuit source</summary>

![circuit](page.circuits/9a04f7e1.svg)

\`\`\`yaml
meta:
  title: Inline button demo
…
\`\`\`

</details>
```

The flag is absent by default: a bare ` ```circuit ` block produces
just the image embed — no source disclosure, no `<details>` wrapper.
Both GitHub Markdown and MkDocs render `<details>` natively, so the
same output works in either build path.

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
