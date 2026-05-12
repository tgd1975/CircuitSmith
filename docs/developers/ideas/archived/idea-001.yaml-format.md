# YAML Circuit Description

> Sub-note of [IDEA-001](idea-001-circuit-skill.md). Predecessor references
> (e.g. `data/config.json`, IDEA-011/018/019/022) resolve via the
> [Provenance anchor map](idea-001-circuit-skill.md#provenance).

## Format

A WireViz-inspired format with three top-level sections: `meta`, `components`,
`connections`.

**`meta`** — circuit identity, drives the ERC report header and alias system:

```yaml
meta:
  title: AwesomeStudioPedal — ESP32 default build
  target: esp32
  config: data/config.json   # pin aliases sourced from here; optional
```

**`components`** — declarative component list; each key is a reference designator,
each value names a profile from the component library:

```yaml
components:
  U1:
    type: mcu/esp32_wroom_32
    label: ESP32

  SW1:
    type: passives/pushbutton
    label: BTN_A
  SW2:
    type: passives/pushbutton
    label: BTN_B

  R1:
    type: passives/resistor
    value: 220
    label: R_PWR_LED

  D1:
    type: passives/led
    color: green
    label: PWR_LED            # unified LED profile; v_forward looked up by color

  J1:
    type: connectors/usb_c
    label: Power In
```

**`connections`** — every entry is a named net. Three forms — `pins` (unordered
joins), `path` (linear chains), and `bus` (shared conductors with taps) — span
every circuit Schemdraw can render; no fourth form is needed.

---

### Form 1 — `pins` (unordered set)

Endpoints that are electrically joined with no intermediate components *between the
listed endpoints*. Used for power rails, ground rails, and direct wire connections.
The renderer draws the shortest path between endpoints. Listing multiple pins of the
same component is allowed and means those pins are shorted on this net.

```yaml
connections:
  - net: GND
    pins: [SW1.2, SW2.2, D1.K, U1.GND, J1.GND]

  - net: VCC
    pins: [J1.VBUS, U1.VIN]
```

---

### Form 2 — `path` (ordered sequence)

An explicit signal path through intermediate
components. The `net` name labels the logical signal — the name the author cares about
(the source GPIO's function). The flattener turns the path into **wire segments** by
walking the token list and grouping consecutive pins that belong to the same
component into a single node. Each edge between adjacent nodes is one segment. The
first segment carries the declared `net` name; each subsequent segment takes a
content-addressed name derived from its two endpoint pins,
`<net>__<RefA>_<pinA>__<RefB>_<pinB>`. Content-addressed names are stable across
edits — inserting a new path entry does not renumber anything else, so PCB diffs
stay minimal.

**Segment count rule** (authoritative for both the renderer and the netlist
exporter — [idea-001.exporters.md](idea-001.exporters.md) §Net-shape mapping
defers to this definition):

1. Group consecutive tokens of the same component into one node. Net-name tokens
   (e.g. `GND`, `VCC`) are always single-token nodes.
2. The number of segments equals the number of edges between adjacent nodes
   (nodes − 1).
3. A segment touching a net-name node also adds the pin-side endpoint to that
   net's membership (the "merge" — see below). The segment itself still exists
   and still has a name.

This covers linear signal chains — filter networks, protection circuits, any sequence
of passives between a source and a destination.

```yaml
connections:
  # Button: GPIO → switch → GND
  # Nodes: [U1.IO13] [SW1.1, SW1.2] [GND]  →  2 segments
  #   BTN_A                 = [U1.IO13, SW1.1]   (declared name)
  #   BTN_A__SW1_2__GND     = [SW1.2, GND]       (content-addressed)
  #   merge: SW1.2 ∈ GND
  - net: BTN_A
    path: [U1.IO13, SW1.1, SW1.2, GND]
    pull: firmware           # ERC source of truth for E1; no external resistor needed

  # LED: GPIO → 220 Ω resistor → LED → GND
  # Nodes: [U1.IO25] [R1.1, R1.2] [D1.A, D1.K] [GND]  →  3 segments
  #   PWR_LED               = [U1.IO25, R1.1]
  #   PWR_LED__R1_2__D1_A   = [R1.2, D1.A]
  #   PWR_LED__D1_K__GND    = [D1.K, GND]
  #   merge: D1.K ∈ GND
  - net: PWR_LED
    path: [U1.IO25, R1.1, R1.2, D1.A, D1.K, GND]

  # Audio input: jack → coupling cap → series resistor → ADC pin
  - net: AUDIO_IN
    path: [J1.TIP, C1.1, C1.2, R2.1, R2.2, U1.IO32]

  # Power with polarity protection: USB-C → Schottky diode → MCU VIN
  - net: VCC
    path: [J1.VBUS, D2.A, D2.K, U1.VIN]
```

`path` endpoints that are plain net names (`GND`, `VCC`, or any other declared net)
resolve via **net merging**: the pin adjacent to the net-name token is added to
that net's membership in addition to being an endpoint of the segment. This applies
symmetrically at either end of a `path:` — a leading net-name token merges the
second token's pin into the named net the same way a trailing one does. This is
how pull-up resistors tap into a bus net by name:

```yaml
- net: I2C_SDA_PULL
  path: [V33, R2.1, R2.2, I2C_SDA]
# Nodes: [V33] [R2.1, R2.2] [I2C_SDA]  →  2 segments
#   I2C_SDA_PULL                    = [V33, R2.1]     (declared name)
#   I2C_SDA_PULL__R2_2__I2C_SDA     = [R2.2, I2C_SDA] (content-addressed)
# Merges:
#   V33     += [R2.1]    (R2.1 joins V33's membership)
#   I2C_SDA += [R2.2]    (R2.2 joins I2C_SDA's membership)
```

The merge is commutative — order of declaration does not matter. A net-name endpoint
in a path never creates a duplicate membership if the pin is already in that net.

When precise net naming matters for PCB handoff, `segment_names` overrides the
auto-generated names for each segment. The list must have one entry per segment
produced by the segment-count rule above (nodes − 1):

```yaml
  - net: PWR_LED
    path: [U1.IO25, R1.1, R1.2, D1.A, D1.K, GND]
    # Auto names would be:
    #   PWR_LED, PWR_LED__R1_2__D1_A, PWR_LED__D1_K__GND
    # Override with PCB-side convention:
    segment_names: [PWR_LED_DRIVE, PWR_LED_ANODE, PWR_LED_RETURN]
```

**`segment_names` length.** A mismatch (too few or too many entries) is a
validation error, not a silent truncation or zero-fill. The error cites the
expected count (nodes − 1), the actual count, and the auto-generated names so
the author can see exactly what flattening produced.

**Validation boundary.** JSON Schema cannot count nodes, so this check runs in
the post-schema validator step (after schema validation, before rendering and
ERC). The pre-commit hook and CI both invoke the flattener + post-schema
validator before handing the net graph to the renderer — the renderer itself
treats a valid flattened graph as a precondition, not something it re-checks.

---

### Form 3 — `bus` (shared backbone with taps)

A single conductor shared by multiple
components, each tapping in at their own pin. Used for I2C, SPI, power rails with
multiple consumers, and any net where a wire runs past several components.

```yaml
connections:
  # I2C bus: backbone from MCU, taps to OLED and BME280 (declared as IC1 elsewhere)
  - net: I2C_SDA
    bus: true
    backbone: [U1.IO21, OLED.SDA]   # renderer draws the main wire between these
    taps: [IC1.SDA]                  # renderer drops perpendicular stubs to each tap

  - net: I2C_SCL
    bus: true
    backbone: [U1.IO22, OLED.SCL]
    taps: [IC1.SCL]

  # 3.3 V power rail shared by MCU, OLED, and sensor
  - net: V33
    bus: true
    backbone: [U1.3V3, OLED.VCC]
    taps: [IC1.VCC, C2.1]           # decoupling cap taps in mid-rail
```

`backbone` is a list of **two or more** pins that sit on the main wire — the
renderer draws a straight line through them, spacing them at equal intervals
along the backbone direction. `taps` are dropped perpendicularly off that main
wire. The distinction is visual: backbone pins render inline with the wire;
taps render as stubs. Electrically both are members of the same net, so the
choice is purely a readability one — put components on the `backbone` when they
read naturally as "on the line" (the MCU pin, the primary peripheral,
additional peripherals sharing the trunk) and put decoupling caps, pull-ups,
and other secondary attachments in `taps`.

`taps` entries are plain pin strings:

```yaml
taps:
  - IC1.SDA
  - C2.1
```

> **Superseded:** earlier drafts of this doc documented a long-form
> `{ ref: "...", layout: { position: 0.3 } }` entry with per-tap layout
> overrides. That form is removed. Per
> [idea-001.layout-engine-concept.md](idea-001.layout-engine-concept.md) §3
> and §4, all geometric decisions — including per-tap positioning — live
> in `layout.yml` as a slot property (`{ region: bus-<name>, position: 0.3 }`),
> not in the topology. Topology files carry no layout fields.

---

## Net-level attributes

Two keys apply uniformly across all three net forms (`pins`, `path`, `bus`):
`pull:` (firmware/hardware pull specification) and `role:` (GPIO direction
override). Both are net-level, never per-pin.

### `pull:` — pull specification for input nets

Valid values:

- `pull: firmware` — INPUT_PULLUP/INPUT_PULLDOWN set in firmware; no external
  resistor
- `pull: hardware_up` — external resistor to VCC in this circuit
- `pull: hardware_down` — external resistor to GND in this circuit

Omitting `pull` on a net whose effective input direction is `in` triggers ERC
check E1. `pull:` is the ERC's sole source of truth for E1 — see
[idea-001.erc-engine.md §E1 notes](idea-001.erc-engine.md).

**Scope.** `pull:` is legal on all three net forms and is always a direct child
of a `connections[*]` entry — never per-pin, never under `pins[*]`, `path[*]`,
or `taps[*]`. A net that mixes input pins needing different pull semantics is
not expressible and is not supported by design — split the topology into two
nets.

**`pull:` on a `bus:` net** — idiomatic for I²C with three or more devices,
where the pull-up resistor is part of the bus itself rather than a separate
path:

```yaml
- net: I2C_SDA
  bus: true
  backbone: [U1.IO21, OLED.SDA]
  taps: [IC1.SDA, R_SDA.2]      # R_SDA bridges: pin 2 taps into this bus...
  pull: hardware_up              # ...and pin 1 taps into V33 below — so R_SDA
                                 # pulls SDA up to 3.3 V. ERC E7 is satisfied.
- net: V33
  bus: true
  backbone: [U1.3V3, OLED.VCC]
  taps: [IC1.VCC, R_SDA.1, C2.1]      # R_SDA.1 is the other end of the pull-up
```

Compared to the `I2C_SDA_PULL` `path:` trick shown later, the `bus:` form keeps
the pull-up co-located with the bus it pulls and avoids inventing a separate
net name.

### `role:` — per-use direction for `GPIO`-typed pins

For nets touching MCU `GPIO`-typed pins (profile-declared `direction: "bidir"`),
the authoritative per-use direction is set on the net via
`role: in | out | bidir` (see
[idea-001.components.md §3](idea-001.components.md#L163-L175)).

Two shapes:

1. **Scalar** (common case — one GPIO on the net):

   ```yaml
   - net: BTN_A
     path: [U1.IO13, SW1.1, SW1.2, GND]
     pull: firmware
     role: in
   ```

2. **Map keyed by `REF.PIN`** (required when a net touches two or more GPIO
   pins — typical on I²C buses where both MCU pins sit on the same net during
   multi-master configurations, or on any point-to-point GPIO-to-GPIO link):

   ```yaml
   - net: I2C_SDA
     bus: true
     backbone: [U1.IO21, OLED.SDA]
     taps: [IC1.SDA]
     role:
       U1.IO21: bidir
   ```

   The map enumerates only the `GPIO`-typed pins on the net. Peripheral pins
   that are already `bidir` in their profile (I²C SDA/SCL on a sensor, audio
   jack TIP) keep their profile direction and are not listed — adding them
   produces a schema error.

   **Keys are always fully-qualified `REF.PIN`** — never the bare pin name,
   even when all GPIO pins on the net belong to the same component. The
   redundancy is intentional: it keeps GPIO-to-GPIO links (two `REF.PIN` pins
   from two different components on the same net) unambiguous and makes
   single-file grep for a specific GPIO's role trivial.

**Rules:**

- Only `GPIO`-typed pins consume `role:`. A `role:` entry keyed on a non-GPIO
  pin is a validation error (catches typos where the author meant a different
  pin).
- A scalar `role:` on a net with more than one GPIO pin is a validation error;
  promote to the map form.
- A net containing at least one GPIO pin with no applicable `role:` entry
  inherits `bidir` from the profile — but ERC E1 then has no firm direction to
  evaluate, so checks that depend on direction (E1, E5) emit a warning citing
  the missing role.
- Non-GPIO pins on the same net inherit their profile `direction` and ignore
  `role:` — the map form does not need to enumerate them.

The `role:` key is **not** legal per-path-segment; segments are a flattener
artifact, not an authoring surface.

**Validation boundary.** JSON Schema can enforce the shape of `role:` (scalar
vs. map of `REF.PIN`-like keys) and the enum values (`in | out | bidir`).
Everything that depends on knowing which pins are `GPIO`-typed — rejecting
non-GPIO keys, rejecting scalar-on-multi-GPIO, emitting the "missing role"
warning — runs in the validator **after** component profiles are loaded, not
in the schema proper. Error messages name the file and line so the author can
see exactly which pin triggered the check.

---

**Complete example — ESP32 with LED, button, I2C sensor:**

```yaml
meta:
  title: ESP32 + BME280
  target: esp32
  erc:
    E9: warn

components:
  U1:  { type: mcu/esp32_wroom_32,    label: ESP32 }
  SW1: { type: passives/pushbutton,   label: BTN_A }
  R1:  { type: passives/resistor,     value: 220,   label: R_LED }
  D1:  { type: passives/led, color: green, label: PWR_LED }
  IC1: { type: sensors/bme280,        label: BME280 }
  R2:  { type: passives/resistor,     value: 4700,  label: R_SDA }
  R3:  { type: passives/resistor,     value: 4700,  label: R_SCL }
  J1:  { type: connectors/usb_c,      label: Power }

connections:
  - net: BTN_A
    path: [U1.IO13, SW1.1, SW1.2, GND]
    pull: firmware

  - net: PWR_LED
    path: [U1.IO25, R1.1, R1.2, D1.A, D1.K, GND]

  # I2C bus — only two devices, so path form is sufficient;
  # use bus form when three or more devices share the line
  - net: I2C_SDA
    path: [U1.IO21, IC1.SDA]
  - net: I2C_SDA_PULL
    path: [V33, R2.1, R2.2, I2C_SDA]   # pull-up taps into bus net by name

  - net: I2C_SCL
    path: [U1.IO22, IC1.SCL]
  - net: I2C_SCL_PULL
    path: [V33, R3.1, R3.2, I2C_SCL]

  - net: VCC
    path: [J1.VBUS, U1.VIN]
  - net: V33
    pins: [U1.3V3, IC1.VCC]
  - net: GND
    pins: [U1.GND, IC1.GND, J1.GND]
    # SW1.2 and D1.K are already merged into GND by the path: forms above
    # (BTN_A and PWR_LED both terminate in GND) — relisting them here is
    # redundant-but-legal; omit for brevity.
```

---

**Escape hatch.** Circuits that genuinely cannot be expressed as a combination
of the three forms are a topology problem, not a YAML problem: restructure, or
graduate to KiCad (IDEA-011). Components that need non-canonical placement can
be assigned the `free` slot in `layout.yml` with a rubric waiver (see
[idea-001.layout-engine-concept.md](idea-001.layout-engine-concept.md) §2
non-goals and §4.1). `.circuit.yml` itself carries no geometric fields under
any circumstance.

## Schema Validation

Every `.circuit.yml` is validated against `.claude/skills/circuit/schema/circuit.schema.json`
before rendering. The schema enforces:

- `meta.target` is a known target string
- `meta.*` known keys (`title`, `target`, `config`, `aliases`, `erc`) are
  type-checked; unknown keys are preserved and emit a lint **warning** (not an
  error) so plugin experimentation stays cheap but typos stay visible.
  `meta.erc` is a map of check code (`E1`, `E5`, …) to severity
  (`off | warn | error`) — per-circuit overrides of the defaults; owned by
  [idea-001.erc-engine.md](idea-001.erc-engine.md).
- every `components[*].type` resolves to an existing profile in the library
- every `connections[*].pins[*]` follows the `REF.PIN` format
- every referenced `REF` appears in `components`
- every referenced `PIN` exists on the component's profile
- `pull:` only appears as a direct child of a `connections[*]` entry
- `role:` is either a scalar (`in | out | bidir`) or a map keyed by `REF.PIN`
  strings present in the same net; scalar form is rejected when the net
  contains more than one GPIO pin
- `segment_names` length equals the number of flattened segments
- `meta.config`, when set, resolves to an existing file (checked at validation
  time, not at schema time, since JSON Schema cannot express filesystem checks)

Validation runs in the pre-commit hook (before rendering) and in CI. An invalid YAML
fails fast with a human-readable error — before any drawing or ERC work is attempted.
Schema validation catches unknown references and unknown pins (ERC checks S4, S5) at
this stage, so the ERC only sees structurally valid net graphs.

Adding a new component profile automatically extends the schema's allowed `type` values;
no manual schema update is required.

## Markdown Integration

The YAML lives inside a fenced code block in Markdown. CI renders it to SVG, hides the
source, and embeds the image — the same pattern the project already uses for Schemdraw
scripts.

**What the author writes:**

````markdown
```circuit
meta:
  title: ESP32 default build
  target: esp32

components:
  U1:
    type: mcu/esp32_wroom_32
  SW1:
    type: passives/pushbutton
    label: BTN_A

connections:
  - net: BTN_A
    pins: [U1.IO13, SW1.1]
  - net: GND
    pins: [SW1.2, U1.GND]
```
````

**What CI rewrites it to (default — source hidden):**

```markdown
<!-- circuit:begin hash:a3f2c1 -->
![Circuit diagram](docs/builders/wiring/esp32/circuit-a3f2c1.svg)
<!-- circuit:end -->
```

**With `show_source` flag — source shown in a collapsible block:**

````markdown
```circuit show_source
meta:
  ...
```
````

renders to:

```markdown
<!-- circuit:begin hash:a3f2c1 source:shown -->
![Circuit diagram](docs/builders/wiring/esp32/circuit-a3f2c1.svg)

<details><summary>Circuit source</summary>

```yaml
meta:
  title: ESP32 default build
  ...
```

</details>
<!-- circuit:end -->
```

The `<details>/<summary>` collapsible is GitHub-native Markdown — no JavaScript,
renders everywhere including issues and PRs.

**Global default** is controlled by `CIRCUIT_SHOW_SOURCE` in
`.github/workflows/generate-circuits.yml`. The per-block `show_source` flag overrides it.

**Staleness detection:** the SVG filename contains the hash of the YAML source. If the
YAML changes, the hash changes, the old image reference breaks, and CI fails — the same
mechanism the existing schematic pipeline uses.

**MkDocs (IDEA-022):** when the docs site moves to MkDocs + Material theme, the
`pymdownx.superfences` custom formatter replaces the CI rewrite step. The ` ```circuit `
block is intercepted at build time, the renderer is called inline, and the SVG is embedded
directly in the HTML. The YAML never appears in the rendered output. No workflow change
needed on the author's side.

---

## Cross-cutting decisions

These decisions round out the three-net-form grammar so that Phase 2 code can
land without revisiting the format:

### 1. YAML loader — `ruamel.yaml`, pinned

The renderer uses **`ruamel.yaml`** in round-trip mode, pinned in
`.claude/skills/circuit/requirements.txt` and documented in the skill's
`SKILL.md`. Rationale:

- Map insertion order is preserved across load → dump → load, which the
  layout engine relies on (see
  [idea-001.layout-engine-concept.md §15](idea-001.layout-engine-concept.md)
  and the i2c-sensor side tie-break at §5.3 — "pin declared first in topology
  wins").
- PyYAML ≥ 5.1 preserves order on load by default but loses it through dump,
  which matters for any future tooling that rewrites `.circuit.yml`
  programmatically (formatters, migration scripts). `ruamel.yaml` keeps order
  in both directions and is a strict superset for our read path.
- Comments survive round-trips — useful later if the renderer ever annotates
  files in place.

A regression test in the skill's test suite loads a fixture with a specific key
order, round-trips it, and asserts equality — the loader pin is only useful if
it is enforced.

### 2. `layout.yml` schema lives next to the layout concept doc

Schema file: `.claude/skills/circuit/schema/layout.schema.json` (alongside
`circuit.schema.json`). Prose owner:
[idea-001.layout-engine-concept.md](idea-001.layout-engine-concept.md), next
to the slot vocabulary.

### 3. Net-name and identifier rules

The namespaces are kept **disjoint** by construction:

- Component references (`components` keys) and net names (`connections[*].net`)
  share a single identifier namespace. A name may appear as exactly one of the
  two — never both. Using the same identifier for a component and a net is a
  validation error with message `"'X' is declared both as a component and as
  a net"`.
- Within a `path:`, a token `X` resolves as a **net name** only if `X` is
  declared in `connections`. Otherwise `X` must be of the form `REF.PIN` with
  `REF` present in `components`. A bare identifier that matches neither is a
  validation error, not silently treated as a future net.
- A `REF.PIN` token always resolves as a pin; there is no "net named
  `R1.2`" fallback.

**Net-name syntax.** Net names match `^[A-Za-z0-9_+\-]+$` **and** must contain
at least one ASCII letter (`[A-Za-z]`). Rationale:

- Allows common rail names (`3V3`, `5V`, `12V`, `+3V3`, `VCC_3V3`) and
  differential-pair suffixes (`USB_D+`, `USB_D-`) that KiCad and WireViz both
  accept.
- Excludes `.` — preserves the `REF.PIN` disambiguation in `path:` tokens.
- Excludes whitespace — prevents ambiguity in the flat `pins: [...]` form.
- Rejects names that are only digits, only signs, or only combinations thereof
  (`3`, `12`, `+`, `-`, `+_`, `-+`) — these have no sensible electrical meaning
  and would visually collide with integer indices or stray punctuation.

**Validation boundary.** The character-class part is a JSON Schema pattern.
The "must contain at least one letter" constraint cannot be expressed in a
single ECMA-262 regex without look-around (which JSON Schema draft 2020-12
permits but not all validators implement), so it is enforced in the
post-schema validator with a dedicated error message citing the offending
net name.

**Component-reference syntax.** Component keys match `^[A-Za-z_][A-Za-z0-9_]*$`
— the stricter form, because refs appear left of a `.` in pin tokens and must
be unambiguous to split on. A pin identifier (right of the `.`) is any
non-empty string of `[A-Za-z0-9_+\-/]` so profile-declared pin names like
`3V3`, `D+`, `D-`, `IO/CE` work.

Together, these rules make the merge resolution in Form 2 unambiguous: an
endpoint token of a `path:` (first or last) is a net-merge target **if and
only if** it is a declared net name; otherwise it must parse as `REF.PIN`.
Order of declaration does not matter — net-name resolution is done after
parsing the whole file.
