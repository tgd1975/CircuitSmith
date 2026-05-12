# Components — Profiles and Authoring

> Sub-note of [IDEA-001](idea-001-circuit-skill.md). Predecessor references
> (e.g. `scripts/generate-schematic.py`, IDEA-011/018/019/022) resolve via the
> [Provenance anchor map](idea-001-circuit-skill.md#provenance).

## Profile structure

A valid component profile has three in-dict top-level sections — `category`, `metadata`,
`pins` — plus a `type` string derived from filename and dict name (so not literally
written in the dict). Each is required — the JSON Schema validator and the pre-commit
hook reject profiles missing any of them.

**Design invariant — category keys layout, not semantics.** `category` exists solely
as the lookup key for the layout engine's canonical-slot table (§5.3). Electrical
semantics — what a pin *is* — come from `pins[*].type` and `pins[*].direction`. ERC
rules, the current budget check, the I2C pull-up check, and every other
safety-relevant rule read `type` / `direction`, never `category`. This invariant is
what lets a piezo buzzer ride on `category: resistor` (identical layout shape, no
ERC rule keyed on `category: resistor`) and a SSD1306 OLED ride on
`category: i2c-sensor` without inheriting sensor-specific semantics. Read
`category` values as shape-family names, not semantic classes — if the
`i2c-sensor` row were renamed to `i2c-peripheral` tomorrow, the SSD1306 would
move with it and nothing about its electrical meaning would change. Future rules
must not key on `category` without first widening this contract.

### 1. `category` — explicit layout-engine classification

The `category` field is the lookup key for the canonical-slot table in
[idea-001.layout-engine-concept.md §5.3](idea-001.layout-engine-concept.md), and is
**independent of the filesystem-addressable `type:`**. Decoupling the two is
deliberate: the topology-fingerprint in layout §8.4 hashes `category`, not `type`,
so renaming or splitting a `components/*.py` file does not invalidate downstream
`layout.yml`. The decoupling protects layout invalidation on filesystem
reorganisation — it does **not** protect `.circuit.yml` files, which still
reference `type: passives/led` literally and need updating if the file is
renamed. Multiple profiles can share a category — every LED colour profile, if
the library ever grows beyond the single unified LED profile, maps to
`category: led`.

```python
LED = {
    "category": "led",
    "metadata": { ... },
    "pins": { ... },
}
```

Valid **user-writable** categories — the ones a hand-authored profile may declare:
`led`, `resistor`, `capacitor`, `button`, `i2c-sensor`, `header`, `jack`, `ic`.

**Kernel-only** categories are populated by rendering primitives the kernel inserts
automatically at placement time per layout §5.3; no author writes a profile for them:
`power-symbol`, `ground-terminal`, `no-connect`. Their rendering primitives live in
the layout kernel itself, not in `components/*.py` — so a reader looking for a
`power_symbol.py` file will not find one, and should not add one. The schema rejects
a user-authored profile that declares one of these values.

Unknown categories are rejected at schema-load time — the validator runs before
the layout engine, so the engine never sees an unknown value. Layout §5.3's
"unknown categories always escalate" fallback exists only as a belt-and-braces
guard. In practice the escalation path fires when a known category's canonical
slot is already occupied — e.g. when a circuit contains a second IC in
addition to its primary MCU — not for entirely unknown categories, which the
schema has already rejected. Adding a new user-writable category is **not** a
one-file change — see "Adding a component — workflow" below.

### 2. `metadata` — human-readable identity and electrical constraints

```python
"metadata": {
    "label": "ESP32 WROOM-32",        # shown on the IC block
    "manufacturer": "Espressif",
    "datasheet": "https://...",        # URL to pin reference
}
```

For MCUs, also include electrical limits used by the ERC current budget check:

```python
    "vcc_min": 3.0,
    "vcc_max": 3.6,
    "max_gpio_current_ma": 12,
    "max_total_current_ma": 200,
```

For LEDs, `metadata` carries the colour-indexed forward-voltage table — see
"Pattern: component-level variant selection" below — rather than a single
`v_forward` scalar.

**`metadata.keywords` — surfacing vocabulary shared with the rule catalog.** An
optional list of short lowercase tokens that describe what the component *is* in
terms a maker would recognise (`"led"`, `"i2c"`, `"pull-up"`, `"decoupling"`).
The circuit skill intersects this list with the `keywords` field of
[rule-catalog entries](idea-001.rule-catalog.md#catalog-format) to decide which
educational rules to surface when the profile is used. Authoring rules:

- written in lowercase, NFKC-normalised form (`"i2c"` not `"I2C"` or `"I²C"`);
- every token used by a catalog entry must appear on at least one shipped profile
  — `validate_catalog.py` enforces this invariant against
  `.claude/skills/circuit/components/*.py`;
- a profile that does not participate in any catalog rule may omit the field.

```python
"metadata": {
    "label": "BME280",
    "manufacturer": "Bosch",
    "datasheet": "https://...",
    "keywords": ["i2c", "sensor", "3.3v"],
}
```

### 3. `pins` — every physical pin, with mandatory side, type, and direction

```python
"pins": {
    "PIN_NAME": {
        "side": "left" | "right" | "top" | "bottom",   # mandatory, closed enum
        "type": "<open string>",                       # mandatory (see below)
        "direction": "in" | "out" | "bidir",           # mandatory, closed enum
        # optional:
        "pull": "up" | "down",          # internal pull resistor
        "is_strapping": True,           # triggers ERC strapping-pin check
        "func": ["I2C_SDA", "ADC1"],    # peripheral functions (ERC bus checks)
        "alt": "VP",                    # alternate label printed on pin
        "required": True,               # S1: ERC errors if this pin has no net
    },
    ...
}
```

**`type` is an open string describing the terminal role.** The schema accepts any
string; the authoritative electrical semantics come from `direction` (and, for ICs,
`is_strapping` / `func`), so the `type` literal exists primarily for reader
legibility and for ERC messages that cite pin role by name. Convention — not enforced
— uses these literals so profiles read consistently:

- MCU / IC pins: `GPIO`, `POWER`, `GROUND`, `INPUT_ONLY`, `RESET`, `SPEC`
- LEDs, diodes: `ANODE`, `CATHODE`
- Capacitors: `POS`, `NEG`
- Resistors, generic passives: `TERMINAL`
- Pushbuttons: `CONTACT`
- Audio jacks: `SIGNAL`, `RING`, `GROUND`
- I2C pins on sensors: `I2C` (data line) or `POWER` / `GROUND` for supply

A profile introducing a genuinely new literal is fine; adding it to this list in the
same PR keeps the convention discoverable.

**Schema-enforced implications.** A small set of `type` literals carry a direction
constraint that the schema checks, so authors cannot create inconsistent profiles:

- `type: INPUT_ONLY` ⇒ `direction: "in"` (schema rejects other values)
- `type: GROUND` ⇒ `direction: "in"` (ground pins sink, never source)
- `type: POWER` ⇒ `direction: "in"` or `"out"`, never `"bidir"` (power pins either sink or source; they do not switch direction)
- `type: GPIO` ⇒ `direction: "bidir"` (firmware-directional; see GPIO rule below)

This list is exhaustive: any other `type` literal (`ANODE`, `CATHODE`, `POS`,
`CONTACT`, `SIGNAL`, `TERMINAL`, …) is convention only — the schema does not
constrain its `direction`, so authors are free to pair them as the component
demands.

**`side` is mandatory on every pin.** A pin with no side has no canonical slot
(layout §5.2's `side-column(P)` returns undefined), so placement fails loudly:
in v0.1 the kernel exits non-zero per layout §7.3; in v1 the AI placer is
invoked. The `free` slot is never an automatic fallback — it is author-selected
in `layout.yml` with a rubric waiver. Making `side` schema-mandatory forces the
failure mode to land as a schema error at profile-authoring time, rather than
as a placement escalation downstream. Side assignment convention:

- `top` — positive supply (VCC, VIN, 3V3, VBAT, VBUS)
- `bottom` — ground (GND)
- `left` — inputs and left-column pins (board-specific; follow physical layout)
- `right` — outputs and right-column pins

When physical layout is ambiguous (symmetric parts, MCUs where inputs and outputs
intermix on both edges), use this tiebreaker: **`left` faces other components on
the same board; `right` faces the board edge.** For MCUs placed centrally, fall
back to datasheet pin numbering — odd side / even side by convention. The rule
exists so canonical-slot placement is deterministic, not aesthetically optimal;
the AI placer (v1) or a manual `layout.yml` override handles final aesthetic choices.

**Side on GND-typed pins is advisory.** A pin declared `type: GROUND` with
`side: bottom` does *not* cause the kernel to route a wire toward the MCU's GND pin.
Layout §5.3's `ground-terminal` rule intercepts any non-pin GND connection and
renders `elm.Ground` at the component's near edge within its own slot; all ground
symbols alias to the global GND net by construction. Profile-level `side` on a GND
pin is preserved for BOM / documentation purposes only.

**`direction` is mandatory, with a GPIO-specific rule.** We use a **profile/circuit
hybrid** for pin directionality: the profile declares the widest direction the pin
can physically carry (`in`, `out`, or `bidir`), and `.circuit.yml` narrows it
per-use via a net-level `role:` key on the cases where it matters. Everywhere below,
"the hybrid" refers to this split. **Semantic convention for `direction`:** on signal
pins (GPIO, INPUT_ONLY, SIGNAL) it tracks signal flow; on supply pins (POWER, GROUND)
and passives (ANODE, CATHODE) it tracks conventional current flow — so an LED anode
is `in` (current enters) and its cathode is `out` (current exits).

Most pins have an unambiguous direction at profile-authoring time: LED anode is `in`,
cathode is `out`; jack tip/sleeve follow audio-signal role; I2C SDA/SCL are `bidir`;
an `INPUT_ONLY`-typed pin is always `in`. For these, the profile declares `direction`
directly.

MCU `GPIO`-typed pins are the canonical instance of the hybrid: firmware decides in
vs. out at runtime, so the profile declares `direction: "bidir"` (the only legal
value on a `GPIO`) and the **authoritative per-use direction** is carried in
`.circuit.yml` via a `role: in | out | bidir` key on the net itself. A net that
does not set `role:` inherits the pin's profile direction (so non-GPIO pins need no
net-level role). The yaml schema for `role:` — specifically where it attaches
(per-net, per-path-segment, per-pin-within-net) — lives in
[idea-001.yaml-format.md](idea-001.yaml-format.md); this doc owns only the
pin-level side of the hybrid.

**`type` and `direction` are not redundant.** An IC's VCC pin is
`type: POWER, direction: in` (it consumes power), while a regulator's VCC output is
`type: POWER, direction: out` (it sources). `type` names the electrical role;
`direction` names the flow.

This hybrid is what a future signal-flow rubric (deferred from v1 per [layout
§10](idea-001.layout-engine-concept.md) — the placeholder name was
`signal_flow_ok`) would consume if it ships; encoding per-pin direction
**now** means the later rubric needs no schema break. If the deferred check
is dropped entirely, the per-pin `direction` still earns its keep via the
schema-enforced implications (INPUT_ONLY, GROUND, POWER) and via ERC rules
that read `direction` directly (E4 INPUT_ONLY-driven).

**`func` is optional in general but category-required where a check depends on it.**
ERC checks that key on peripheral function read `func` tags on pins. The I2C
pull-up check (E7) is the motivating case: it activates only when a pin carries
`func: ["I2C_SDA"]` or `["I2C_SCL"]`. To prevent a hand-authored profile from
silently disabling E7, the schema requires that:

- On a `category: i2c-sensor` profile, data-line pins must use `type: I2C`
  (not `SDA`, `SCL`, or other near-synonyms) **and** declare
  `func: ["I2C_SDA"]` or `["I2C_SCL"]`. The schema enforces both halves:
  the `type: I2C` literal is the hook the `func`-required rule keys on, so
  pinning the rule to a concrete literal (rather than a semantic phrase
  like "the data line") makes it mechanically checkable. Pins for VCC /
  GND need no `func`.
- An MCU / IC profile tags only the pins that are the chip's **default** I2C
  assignment in silicon (e.g. ESP32 `IO21`/`IO22`, nRF52840 default TWIM
  pinning) — not every GPIO that the internal GPIO-matrix can route to I2C.
  On parts where any GPIO can host I2C, over-tagging every pin is both noisy
  and misleading about which pins are the "natural" choice. A rule-catalog
  backstop warns (not errors) when `.circuit.yml` wires a non-default pin as
  I2C without a `func` tag, so remapping the bus surfaces as a diagnostic
  rather than silent failure.

The general rule: `func` is optional metadata for pins whose peripheral role is
incidental, and category-required for pins whose electrical behaviour the ERC
can only detect through `func`.

**`is_strapping: True` forbids an internal `pull:` on the same pin.** Strapping
pins are sampled by the silicon *at reset*, before firmware runs; internal pull
resistors only engage after boot, so a profile-level `pull:` on a strapping pin
cannot establish the required boot level and is almost always an authoring
mistake. The schema rejects a profile that declares both fields on the same
pin. The pull that actually satisfies the strapping requirement is wired in
`.circuit.yml` (net-level `pull: firmware` or `pull: hardware_up`) and checked
by ERC E5 — not by this schema rule.

#### Profile examples

Four examples, one per shape that recurs across the project's circuits.

**MCU (excerpt).** `ic` category. Strapping pin, input-only pin with datasheet
alias, and I2C-capable GPIO shown; the full ESP32 profile has ~36 pins following
the same shape:

```python
ESP32_WROOM_32 = {
    "category": "ic",
    "metadata": {
        "label": "ESP32 WROOM-32",
        "manufacturer": "Espressif",
        "vcc_min": 3.0,
        "vcc_max": 3.6,
        "max_gpio_current_ma": 12,
        "max_total_current_ma": 200,
    },
    "pins": {
        "3V3":  {"side": "top",    "type": "POWER",      "direction": "in"},
        "GND":  {"side": "bottom", "type": "GROUND",     "direction": "in"},
        "IO0":  {"side": "right",  "type": "GPIO",       "direction": "bidir",
                 "is_strapping": True},
        "IO34": {"side": "right",  "type": "INPUT_ONLY", "direction": "in"},
        "IO36": {"side": "right",  "type": "INPUT_ONLY", "direction": "in",
                 "alt": "VP"},                                   # datasheet alias
        "IO21": {"side": "right",  "type": "GPIO",       "direction": "bidir",
                 "func": ["I2C_SDA"]},
        # ... remaining pins omitted
    },
}
```

The `alt` field on `IO36` is what the schematic renderer prints next to the pin
(the datasheet's `VP` name is more familiar than `IO36` to ESP32 readers). It does
not change the net-level identifier — `.circuit.yml` still references `IO36`.

**Pushbutton.** `button` category. Two electrically symmetric terminals on
opposite sides so the canonical button routing (one pin toward the MCU column, the
other toward GND) works:

```python
PUSHBUTTON = {
    "category": "button",
    "metadata": { "label": "BTN" },
    "pins": {
        "1": {"side": "left",  "type": "CONTACT", "direction": "bidir"},
        "2": {"side": "right", "type": "CONTACT", "direction": "bidir"},
    },
}
```

Placed in `right-column` next to an MCU, pin 1 faces the MCU (left) and pin 2 faces
the outside (right); the canonical-slot rule for `button` in §5.3 relies on exactly
this orientation.

**Mono audio jack.** `jack` category. Both terminals live on the left because the
jack is edge-mounted; the `bidir` tip lets `.circuit.yml` declare either
"audio-in" or "audio-out" via a net-level `role:` override:

```python
MONO_JACK_6_35MM = {
    "category": "jack",
    "metadata": { "label": "Mono 1/4\" jack" },
    "pins": {
        "TIP":    {"side": "left", "type": "SIGNAL", "direction": "bidir"},
        "SLEEVE": {"side": "left", "type": "GROUND", "direction": "in"},
    },
}
```

**I2C sensor.** `i2c-sensor` category. SDA/SCL both `bidir` per the hybrid
(profile declares `bidir`; `.circuit.yml` narrows only if needed); power on
top, ground on bottom per convention. The `func` tag is what activates ERC
check E7 (I2C pull-up):

```python
BME280 = {
    "category": "i2c-sensor",
    "metadata": { "label": "BME280", "manufacturer": "Bosch" },
    "pins": {
        "VCC": {"side": "top",    "type": "POWER",  "direction": "in"},
        "GND": {"side": "bottom", "type": "GROUND", "direction": "in"},
        "SDA": {"side": "left",   "type": "I2C",    "direction": "bidir",
                "func": ["I2C_SDA"]},
        "SCL": {"side": "left",   "type": "I2C",    "direction": "bidir",
                "func": ["I2C_SCL"]},
    },
}
```

A resistor profile is trivially similar (two pins, `type: TERMINAL`, both `bidir`);
no dedicated example is warranted.

#### Composite components

Headers, OLED strips, audio jacks with switch contacts, multi-section parts are
expressed as a **single profile with per-pin `side`**. No sub-layout primitive is
introduced. The §5.3 `header` / `jack` row already targets them; internal ordering
along each side follows the declaration order of the `pins` dict (Python preserves
insertion order for dict literals since 3.7, so the order written in
`components/*.py` is the order the layout kernel sees).
A composite that cannot be expressed this way is a topology problem, not a profile
problem — see layout §2 non-goals.

### 4. Schema registration

The `type` string must match the file and dict name so the JSON Schema validator can
resolve it automatically:

```
components/mcus.py       → type: "mcu/<dict_name_lowercase>"
components/passives.py   → type: "passives/<dict_name_lowercase>"
components/connectors.py → type: "connectors/<dict_name_lowercase>"
```

Adding a new file (e.g. `components/sensors.py`) automatically creates a new
`sensors/...` type namespace: the pre-commit hook re-derives the allowed `type`
list from the full component library on every run, walking every `components/*.py`
it finds. No manual schema update is needed when adding a profile within an existing
category, nor when introducing a new profile file within an existing category
taxonomy. Adding a **new** category name
(as a §5.3 row) has additional obligations outside this file; see the workflow
table below.

**Filename is organisational, not semantic.** Files group profiles by theme — `mcus`,
`passives`, `connectors`, `sensors` — and do not map 1-to-1 to `category`. A BME280
(`category: i2c-sensor`) may live in `sensors.py`; a piezo buzzer
(`category: resistor` by layout shape) lives in `passives.py`. The skill picks the
thematically best file, or creates a new one using a short plural noun
(`sensors.py`, `displays.py`, `regulators.py`). Creating a new file is *not* the
same as creating a new category — the category gatekeeping in §1 is untouched.

### Phase 1 cutover — one-shot greenfield build of the profile library

The rules in sections 1–4 are stricter than the current state of the repo, which
has no structured component profiles at all — `scripts/generate-schematic.py` hard-codes
per-component rendering inline (e.g. `LED_R = 220`), and there is no `category`,
per-pin `side`, or `direction` to migrate. The cutover below is therefore a greenfield
build of `components/*.py` rather than a transformation of existing dicts.

Per the [Phase Plan in idea-001-circuit-skill.md](idea-001-circuit-skill.md#phase-plan),
the **profile library and `schema/circuit.schema.json` ship together in the Phase 1 PR**
(alongside the refactored `generate-schematic.py`). Every day-one profile listed below
lands in that single commit, each with `category`, `side` on every pin, and `direction`
(per the rules above). A reviewer of the Phase 1 PR should expect `components/` to
appear as a new directory with the full initial library; there is no staged-rollout
mode where some profiles have the new fields and others don't. The Phase 2 cutover
described in
[idea-001.layout-engine-concept.md §16.1](idea-001.layout-engine-concept.md) is a
separate PR that consumes this library to ship the YAML renderer + layout kernel.

---

## Pattern: component-level variant selection

A single profile can parameterise over a bounded family of physically-similar
variants by exposing a lookup table in `metadata` and accepting a selector key on
the component entry in `.circuit.yml`. **LED colour** is the motivating case: pin
shape, direction, and slot placement are identical across colours; only the forward
voltage varies, and that value is consumed by ERC check E3.

```python
# components/passives.py
LED = {
    "category": "led",
    "metadata": {
        "label": "LED",
        "v_forward_by_color": {
            "red":   2.0,
            "green": 2.1,
            "amber": 2.0,
            "blue":  3.2,
            "white": 3.2,
        },
        "v_forward_default": 2.0,   # used when color: is omitted
    },
    "pins": {
        "A": {"side": "left",  "type": "ANODE",   "direction": "in"},
        "K": {"side": "right", "type": "CATHODE", "direction": "out"},
    },
}
```

In `.circuit.yml`:

```yaml
components:
  D1: { type: passives/led, color: green, label: PWR_LED }
```

The ERC check E3 reads `v_forward_by_color[color]` to calculate
`I = (VCC - v_forward) / R` — an author declaring `color: blue` gets the 3.2 V
calculation, not the 2.0 V default. **Omitted or unrecognised `color:` falls back
to `v_forward_default`.** The common case is `D1: { type: passives/led }` with no
colour specified at all — the default 2.0 V is a safe approximation for most
visible LEDs, so demanding an explicit colour would be needless friction. A
`color:` value that isn't a key of `v_forward_by_color` (typo, unlisted colour)
is treated the same way rather than schema-rejected: the tooling can't
distinguish a typo from an intentional "unspecified" declaration, and the
uniform "only exact matches against the table drive a colour-specific
`v_forward`" rule is simpler than two behaviours. The earlier `LED_STANDARD` +
`LED_RED/GREEN/BLUE/WHITE` dict-spread pattern is retired: one profile + one
variant table is simpler to read, simpler to schema-validate, and lets ERC warn
on the declared colour when the author bothered to declare one.

The pattern generalises to any profile where a single categorical axis varies while
the schema-visible structure is constant. Resistor wattage ratings would be a
candidate (`power_by_value`); capacitor dielectric type would not (dielectric
affects the pin model, not just a scalar). Reach for this pattern only when the
axis is genuinely orthogonal to schema shape.

---

## Adding a Component — workflow

The circuit skill handles component addition. Whether it is a one-file change depends on
whether the component introduces a new category.

**Rule IDs and bumps — one-line primer.** Each row in layout §5.3 carries an integer
rule ID. The topology-fingerprint in layout §8.4 hashes that ID into each
`layout.yml`, so bumping the ID of a rule (meaning: changing the rule's placement
logic in a way that could alter existing layouts) forces every downstream
`layout.yml` that uses it to auto-invalidate and re-run the kernel. A new category
always introduces a fresh rule ID (no bump). A *change* to an existing category's
placement behaviour is what triggers a bump. See layout §8.4 for the full
fingerprint mechanics.

| Case | Files changed |
|---|---|
| **Existing category** (e.g. a new I2C sensor that fits `i2c-sensor`) | Profile file only (`components/*.py`). One-file change. |
| **New category** (no row in §5.3 yet) | Profile file **plus** a §5.3 canonical-slot row in [idea-001.layout-engine-concept.md](idea-001.layout-engine-concept.md) **plus** a fresh rule-ID allocated for that row in the kernel rule table. Two-file change; no bump of an existing ID is involved, so downstream `layout.yml` files are not invalidated. |
| **Changing an existing category's placement behaviour** (new slot math, new label default, new placement rule for a row that already exists) | §5.3 row edit + **rule-ID bump** on that row in the kernel rule table. The profile file is usually not touched (this is a layout-kernel change, not a profile change). Per layout §8.4 the bump cascades: every downstream `layout.yml` using the bumped rule auto-invalidates and needs a `/circuit layout` re-run. |

**Connection-shape names.** The identifiers used in §5.3
(`led-anode-pin-cathode-gnd`, `resistor-in-path`, …) live adjacent to the
canonical-slot table in the layout engine concept, not in this file. They are computed
by the kernel from `(topology, category)` at placement time; component profiles do not
declare them. A new category that introduces a new connection shape adds the shape
identifier in the same PR as the §5.3 row.

### Asking the circuit skill to add a component

> "Add a BME280 temperature/humidity sensor to the component library."

The skill will:

1. Look up the BME280 datasheet pinout.
2. Determine the category. BME280 is an `i2c-sensor` — existing row in §5.3, so this is
   a one-file change.
3. Pick a thematically fitting file — for BME280, `components/sensors.py` (creating
   it if it does not exist; see "filename is organisational" above). Write the
   profile with mandatory `category`, `side` on every pin, and `direction` on
   every pin (MCU `GPIO`s use `bidir` per the hybrid rule).
4. For a genuinely new category, draft the §5.3 row as well and allocate a fresh
   rule-ID for it in the kernel rule table (no bump — new rows get new IDs).
5. Run the schema validator to confirm the new `type:` resolves and every pin carries
   the mandatory fields.
6. Report what ERC checks become active for this component (I2C → check 7 activates).

---

## Initial library

The profiles shipped with the Phase 1 cutover PR (see "Phase 1 cutover" above).
This list is heuristic, not derived from a survey — it targets the median maker
project (read a sensor, display or transmit the value, maybe drive a small
load) plus this project's audio-pedal core. It is intentionally not exhaustive:
additions grow reactively per [layout §14.2](idea-001.layout-engine-concept.md)
as real needs surface. Every row in the first table fits an existing §5.3
canonical-slot row and is therefore trivially solvable by the deterministic
kernel. Rows in the second table are components maker projects reach for
often, but each needs layout work (a §5.3 row, possibly a rule-ID bump) before
it can ship cleanly.

### Ships on day one

| Profile | File | Category | Why |
|---|---|---|---|
| `ESP32_WROOM_32` | `mcus.py` | `ic` | our primary target |
| `NRF52840` | `mcus.py` | `ic` | our secondary target |
| `RESISTOR` | `passives.py` | `resistor` | foundational; every circuit |
| `CAPACITOR` | `passives.py` | `capacitor` | decoupling + filtering |
| `LED` | `passives.py` | `led` | unified profile with `v_forward_by_color`; retires the LED_RED/GREEN/BLUE/WHITE spread |
| `PUSHBUTTON` | `passives.py` | `button` | user input |
| `PIEZO_BUZZER` | `passives.py` | `resistor` (¹) | audible alerts; layout-identical to a 2-pin inline passive |
| `USB_C` | `connectors.py` | `jack` | 5 V power input |
| `DC_BARREL_JACK_2_1MM` | `connectors.py` | `jack` | 9 V pedal supply |
| `MONO_JACK_6_35MM` | `connectors.py` | `jack` | audio in/out |
| `STEREO_JACK_6_35MM` | `connectors.py` | `jack` | stereo audio |
| `PIN_HEADER_2` / `_3` / `_4` / `_6` / `_8` ² | `connectors.py` | `header` | module breakouts, programming headers |
| `SCREW_TERMINAL_2` / `_3` ² | `connectors.py` | `header` | external wiring (relays, power-in) |
| `BME280` | `sensors.py` | `i2c-sensor` | temp / humidity / pressure — the skill-workflow canonical example |
| `SSD1306_128X64_I2C` | `sensors.py` | `i2c-sensor` (³) | the default maker OLED; layout-identical to an I2C sensor |

¹ A piezo buzzer is not electrically a resistor, but its layout shape (2-pin
inline passive on a GPIO path) is identical. `category` keys layout, not
semantics — a deliberate consequence of the components.md §1 decoupling.
Rendering picks the schemdraw element from an optional `metadata.symbol`
field on the profile (e.g. `"symbol": "Speaker"` for the piezo,
`"symbol": "LED"` for the LED profile); when omitted, the kernel falls back
to a per-`category` default. `category` is never consulted directly for
symbol choice, so two profiles sharing `category: resistor` can still
render as different elements.

² `PIN_HEADER_*` and `SCREW_TERMINAL_*` are generated from a template, not
hand-written as five / two separate dicts: a single `make_header(n)` function in
`connectors.py` emits each `PIN_HEADER_<n>` profile with `n` pins all declaring
`side: bottom`. This matches the canonical placement for `header` in layout
§5.3 (`top-row` or `bottom-row`): when the header lands in `top-row` the pins
face the board interior below; when it lands in `bottom-row` the same `side:
bottom` is preserved as a declaration of "pins face the board interior from
the edge", and the kernel handles the geometric flip at render time. The
`side` value on a header pin is therefore a fixed declaration of
"interior-facing", not a literal cardinal direction on the final schematic.
Generation runs at module import time — the dicts are materialised as
top-level names in `connectors.py` before the pre-commit hook's "walk every
`components/*.py`" pass (§4) sees them, so from the validator's perspective
there is no difference between a templated profile and a hand-written one.
The generated profiles are still schema-validated individually once loaded — the
template is a deduplication convenience, not a schema shortcut. Adding a new size
(e.g. `PIN_HEADER_10`) is a one-line change; the category stays `header`.

³ SSD1306 is a display, not a sensor; it rides on `i2c-sensor` for the same
"layout-identical" reason as piezo. If the category is renamed to `i2c-peripheral`
(see backlog, DHT22/DHT11 row), SSD1306 moves with it. Until then, reading
`category: i2c-sensor` as "shares the I2C-peripheral canonical-slot shape" avoids
misinterpreting it as a semantic claim.

### Backlog — requires a new §5.3 row first

These are common-maker components we do **not** ship on day one because each
needs layout work first. Ordered by how often a blocked project would hit the
missing row.

| Pattern | Needs | Priority |
|---|---|---|
| Generic diode / Schottky (for reverse-polarity protection) | `diode` row — ERC E9 needs a semantic distinction from `resistor`, not just a type label; otherwise every USB-C / barrel-jack circuit fails E9 by construction | **High** — E9 ships at v0.1 as WARNING (not ERROR) for this reason; see [erc-engine §E9 note](idea-001.erc-engine.md). Promotes to ERROR once `diode` lands |
| 3-pin linear regulator (AMS1117-3.3, LM7805) | `regulator` row: fixed-role 3 pins (IN / OUT / GND) | High — ubiquitous on maker boards |
| Potentiometer / trimpot | `pot` row: ADC-tap-between-rails shape (VCC / wiper / GND) | High — maker-UI workhorse |
| DHT22 / DHT11 (1-wire digital sensor) | Rename `i2c-sensor` row to `digital-sensor`, or add a parallel row | Medium |
| N-MOSFET / NPN BJT as a switch | `transistor-switch` row: gate-drain-source / base-collector-emitter roles | Medium |
| Rotary encoder | `encoder` row: 3 pins (A / B / common) ± push switch | Medium |
| WS2812 / addressable LED chain | New topology (data-chain, not a net) — likely out of scope per layout §2 non-goals | Low |
| Servo / motor header with specific wiring | Either `PIN_HEADER_3` variant or `servo-header` row | Low |

---

## Pin aliases

Aliases rename profile pins for human readability — they live in this doc
(rather than in [idea-001.yaml-format.md](idea-001.yaml-format.md)) because
every consumer that cites a pin by name — ERC messages, BOM rows, the
netlist — resolves aliases against the profile's pin identifiers, so the
alias contract is co-located with the profile contract that defines those
identifiers.

Every GPIO can carry a human-readable alias that propagates through ERC, BOM, and
netlist. Aliases are declared either inline under `meta.aliases` or sourced from an
external file referenced by `meta.config: data/config.json` — the YAML-level schema
for both forms, including validation that the `meta.config` path resolves to an
existing file, lives in [idea-001.yaml-format.md](idea-001.yaml-format.md) (see the
`meta.*` keys rules there):

```yaml
meta:
  aliases:
    IO25: PWR_LED
    IO26: BT_LED
    IO13: BTN_A
```

ERC messages use aliases: `"BTN_A: floating input"` rather than `"IO13: floating
input"`. BOM rows that surface a pin name (rare — mostly diagnostic columns) use
the alias for the same reason. **The KiCad netlist does not** — see
[idea-001.exporters.md §Net naming](idea-001.exporters.md), which uses physical
pin identifiers in `(node (ref X) (pin Y))` because KiCad matches pin numbers,
not friendly names. Aliases are orthogonal to `category`, `side`, and
`direction` — they rename pins for human readability only, without changing any
schema-visible profile structure.
