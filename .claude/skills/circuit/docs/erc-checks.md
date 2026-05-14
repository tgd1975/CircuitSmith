# ERC Checks — Reference

When ERC fires on your PR, find the check code below for the trigger,
meaning, severity, suppression, and a link to the catalog entry's
"Why / Senior's tip / Source" block.

Authoritative source: the engine's
[`CHECK_TABLE`](../../../../src/circuitsmith/erc_engine.py) and the
catalog at
[`src/circuitsmith/knowledge/rules.json`](../../../../src/circuitsmith/knowledge/rules.json).
This document mirrors those for human reading; if a divergence
appears, the code and catalog win and this doc gets a correcting PR.

Public-contract reminder: the check IDs `S1–S7` and `E1–E22` are
**stable**. Adding a check reserves a new ID; deprecating retires one
without renumbering. The skill, CI gate, and catalog entries all key
on these IDs.

---

## S1 — Unconnected required pin

**Trigger.** A pin whose profile declares `required: true` does not
appear in any net's membership.

**Meaning.** The author placed a component but forgot a required
electrical connection. For example: a USB-C jack with no GND
connection, or a sensor module whose VCC pin is unwired.

**Severity.** ERROR by default.

**Suppression.** Override the profile's `required` flag per-component
when you genuinely intend to leave the pin open (e.g. an EN pin you
will wire from a header later):

```yaml
components:
  U1:
    type: mcu/esp32
    pin_overrides:
      EN: { required: false }
```

**Catalog.** [`rules.json` → S1](../../../../src/circuitsmith/knowledge/rules.json).

---

## S2 — Dangling net

**Trigger.** A net listed under `connections[*].net` has exactly one
endpoint pin in its membership after path-flattening and merges.

**Meaning.** Almost always a wiring typo — the author meant to list a
second pin but lost it during a refactor or copy-paste.

**Severity.** ERROR by default.

**Suppression.** No per-net suppression — fix the wiring. If you
genuinely want an isolated test point, declare it on a component pin
rather than as a free net.

**Catalog.** [`rules.json` → S2](../../../../src/circuitsmith/knowledge/rules.json).

---

## S3 — Duplicate net name

**Trigger.** Two or more `connections[*].net` entries share the same
name without an explicit merge intent.

**Meaning.** Either a rename gap (the author meant to call them
different things) or an attempt to merge two definitions into one net.
YAML's silent duplicate-key resolution makes this dangerous without
the warning.

**Severity.** WARNING by default.

**Suppression.** Rename one side, or fold both definitions into a
single `pins:` entry listing every endpoint:

```yaml
# instead of:
- net: VCC
  pins: [J1.VBUS]
- net: VCC
  pins: [U1.VIN]
# write:
- net: VCC
  pins: [J1.VBUS, U1.VIN]
```

**Catalog.** [`rules.json` → S3](../../../../src/circuitsmith/knowledge/rules.json).

---

## S4 — Unknown reference

**Trigger.** A `connections[*]` token references a `REF` not declared
under `components`.

**Meaning.** Rename gap — the component was renamed and a stale
reference remained. Detected by the schema validator before the
ERC engine runs; surfaces in the same report under the same severity
column.

**Severity.** ERROR by default.

**Suppression.** Not suppressible — fix the reference. Use your
editor's project-wide rename when refactoring component refs.

**Catalog.** [`rules.json` → S4](../../../../src/circuitsmith/knowledge/rules.json).

---

## S5 — Unknown pin

**Trigger.** A `REF.PIN` token references a pin that is not on the
component's profile.

**Meaning.** The author wrote a silicon-level pin name (e.g.
`U1.IO13`) where the dev-board profile uses the silkscreen name
(`U1.D13`). Detected by the schema validator.

**Severity.** ERROR by default.

**Suppression.** Not suppressible — fix the reference. Read the
profile dict in `src/circuitsmith/components/` to see the valid pin
names; the `alt:` field on each pin holds the silicon-level name.

**Catalog.** [`rules.json` → S5](../../../../src/circuitsmith/knowledge/rules.json).

---

## S6 / S7 — Sub-block schema validation (EPIC-014, TASK-117)

**Trigger.** S6 fires when a `.circuit.yml` references a
`sub-block:` that is not declared in the file's top-level
`sub-blocks:` map. S7 fires when an `instances:` entry omits a
required named-port mapping (a port the sub-block declares is
missing from the instantiation).

**Meaning.** S6 catches typos in instance declarations
(`sub-block: led_indictator` vs `led_indicator`). S7 catches
under-wired instances — every named port the sub-block exposes
must map to a parent-circuit net. Both fire at the schema layer,
before flatten / NetGraph construction.

**Severity.** ERROR by default. Not suppressible.

**Catalog.** [`rules.json` → S6, S7](../../../../src/circuitsmith/knowledge/rules.json).
The full sub-block grammar is documented in
[`circuit-yaml.md`](circuit-yaml.md#sub-blocks-and-instances).

---

## E1 — Floating input

**Trigger.** A net contains a signal-input pin (`INPUT_ONLY` type, or
GPIO with runtime `role: in`, or GPIO with no role on a net touching a
switch) and has neither a `pull:` declaration nor an external
pull-resistor to a power-class or ground-class net.

**Meaning.** The input would float — its measured level depends on
stray capacitance, and reads would be random bits.

**Severity.** ERROR by default; downgraded to WARNING when the only
candidate inputs have unresolved `role:` (the engine cannot
distinguish "input that needs a pull" from "output that doesn't").

**Suppression.** Declare `pull: firmware` on the net when the firmware
enables `INPUT_PULLUP`; declare `pull: hardware_up` / `hardware_down`
when an external resistor anchors the level:

```yaml
- net: BTN_A
  path: [U1.D13, SW1.1, SW1.2, GND]
  pull: firmware
```

To suppress on a specific net (deliberate floating test point):

```yaml
- net: TEST_POINT
  pins: [U1.D34]
  erc: { E1: off }
```

**Catalog.** [`rules.json` → E1](../../../../src/circuitsmith/knowledge/rules.json).

---

## E2 — LED missing resistor

**Trigger.** An LED anode pin (`A`) sits on a `path:` net, and the
flattened walk between the driving GPIO and the anode contains no
resistor component. LEDs on `pins:` or `bus:` nets fire E2 directly
(non-path topology is the error — a current-limiter has no defined
position).

**Meaning.** Without a series resistor, the LED draws all the current
the GPIO can source. The LED dies; the GPIO eventually does too.

**Severity.** ERROR by default.

**Suppression.** Add the resistor (don't suppress). For an LED on a
deliberately-current-limited GPIO (rare, e.g. a constant-current
driver IC):

```yaml
components:
  D1:
    type: passives/led
    color: green
    erc: { E2: off }
```

**Catalog.** [`rules.json` → E2](../../../../src/circuitsmith/knowledge/rules.json).

---

## E3 — LED resistor out of range

**Trigger.** An LED's current-limiting resistor produces a calculated
current below ~1 mA (LED too dim) or above the MCU's
`max_gpio_current_ma` (pin at risk). Calculation: `I = (VCC -
v_forward) / R`.

**Meaning.** Below 1 mA the LED is invisible. Above the GPIO's budget
the pin's drive transistor weakens with every cycle.

**Severity.** WARNING by default — the resistor value is the
author's stated intent; the inputs (`vcc_max`, `v_forward`) are
nominal. Authors who want pin-at-risk to block CI can promote E3 via
`meta.erc: { E3: error }`.

**Suppression.** Adjust the resistor value (preferred). To suppress on
a specific net:

```yaml
- net: LED_BT
  path: [U1.D26, R_BT.1, R_BT.2, D_BT.A, D_BT.K, GND]
  erc: { E3: off }
```

**Catalog.** [`rules.json` → E3](../../../../src/circuitsmith/knowledge/rules.json).

---

## E4 — INPUT_ONLY pin driven

**Trigger.** A net contains a pin whose profile `type` is `INPUT_ONLY`
and at least one other pin whose profile `direction` is `"out"`.

**Meaning.** The input-only pin cannot drive the line, but the output
pin will. The input reads whatever the output drives — not the
intended signal — and the assignment is a wiring bug.

**Severity.** ERROR by default.

**Suppression.** Re-pin to a regular bidirectional GPIO. If you
genuinely want the contention (rare; usually for ADC reads while
another peripheral drives the line):

```yaml
- net: AUX_READ
  pins: [U1.D34, U2.OUT]
  erc: { E4: off }
```

**Catalog.** [`rules.json` → E4](../../../../src/circuitsmith/knowledge/rules.json).

---

## E5 — Strapping pin without pull

**Trigger.** A net contains an MCU strapping pin
(`is_strapping: true`) and a switch (`category: button`), and has no
`pull: firmware`/`hardware_up`/`hardware_down`.

**Meaning.** The strapping pin samples at reset; an open switch with
no defined level makes the boot mode non-deterministic.

**Severity.** WARNING by default. Authors who want strapping-pin
issues to fail CI can promote per-circuit:

```yaml
meta:
  erc: { E5: error }
```

**Suppression.** Declare a pull on the net (preferred), or suppress
per-component if you know what you are doing:

```yaml
components:
  U1:
    type: mcu/esp32
    erc: { E5: off }   # I trust my firmware to handle boot mode
```

**Catalog.** [`rules.json` → E5](../../../../src/circuitsmith/knowledge/rules.json).

---

## E6 — Missing decoupling cap

**Trigger.** A non-MCU IC has a `POWER`-typed pin whose net contains
no capacitor component. Dormant when only the MCU is present on a
rail — dev-board MCUs carry their own decoupling.

**Meaning.** Digital switching draws transient current spikes; without
a local capacitor, the rail voltage drops at the IC and the chip
glitches.

**Severity.** WARNING by default. Promote to ERROR per-circuit for
boards where decoupling is non-negotiable:

```yaml
meta:
  erc: { E6: error }
```

**Suppression.** Add the cap (preferred). For a multi-IC rail already
decoupled by a shared bulk cap, no further action is needed — E6 is
satisfied by any cap on the net.

**Catalog.** [`rules.json` → E6](../../../../src/circuitsmith/knowledge/rules.json).

---

## E7 — I2C missing pull-up

**Trigger.** A net contains *two or more* pins carrying an I2C
`func:` tag (`I2C_SDA` or `I2C_SCL`) and has no resistor terminating
on a power-class net.

**Meaning.** I2C is open-drain — no device drives the line high; the
pull-up does. Without it, SDA/SCL float and the bus does not
communicate.

**Severity.** WARNING by default.

**Suppression.** Wire the pull-ups (preferred). If your breakout board
already provides them:

```yaml
components:
  S1:
    type: sensors/bme280
    erc: { E7: off }   # breakout has integrated pull-ups
```

**Catalog.** [`rules.json` → E7](../../../../src/circuitsmith/knowledge/rules.json).

---

## E8 — Current budget exceeded

**Trigger.** The summed indicator current across all LED paths
exceeds the MCU's `max_total_current_ma` metadata.

**Meaning.** Going above the chip's total-current budget browns the
3.3 V rail; intermittent resets follow.

**Severity.** WARNING by default. Circuit-wide finding — Ref and Pin
columns render as `—`.

**Suppression.** Drive heavy LED loads through an external transistor
or LED-driver IC. To suppress per-circuit (rare; only when you have
measured the actual draw):

```yaml
meta:
  erc: { E8: off }
```

**Catalog.** [`rules.json` → E8](../../../../src/circuitsmith/knowledge/rules.json).

---

## E9 — Reverse-polarity unprotected

**Trigger.** A power-input connector (`kind: power-connector`) has a
`POWER`-typed pin whose net contains no diode or P-MOSFET protection
element.

**Meaning.** A reverse-polarity supply destroys the MCU. The check
exists to nudge every board toward a series diode or P-MOSFET in
line with the supply input.

**Severity.** **WARNING on v0.1** because the `diode` component
category is backlogged — without it, every USB-C / barrel-jack
circuit would fail E9 by construction. Auto-promotes to ERROR once
the `diode` category lands. Each ERC report's "Pending promotions"
block documents this for that report's reader.

**Suppression.** Once the `diode` category exists, wire a Schottky or
P-MOSFET in series and E9 passes. To suppress for a USB-C connector
that has CC-pin protection in compliant cables:

```yaml
components:
  J1:
    type: connectors/usb_c
    erc: { E9: off }
```

**Catalog.** [`rules.json` → E9](../../../../src/circuitsmith/knowledge/rules.json).

---

## E10 — Pin conflict

**Trigger.** The same physical pin (`REF.PIN`) appears in two or more
*declared* nets.

**Meaning.** The pin can be in one state at a time; two nets claiming
it is a contradiction. Either the nets should be merged or one
endpoint should re-pin.

**Severity.** ERROR by default. When two declared nets both touch the
pin, the most-severe of the two nets' overrides wins.

**Suppression.** Merge the nets, or re-pin (preferred). Suppression on
a multi-bus shared pin (rare; for example a software bit-banged
signal sharing two roles):

```yaml
- net: MUX_A
  pins: [U1.D13, X1.SIG]
  erc: { E10: off }
- net: MUX_B
  pins: [U1.D13, X2.SIG]
  erc: { E10: off }
```

**Catalog.** [`rules.json` → E10](../../../../src/circuitsmith/knowledge/rules.json).

---

## E11..E15 — Sub-block and divider rules (EPIC-014)

E11..E14 cover the sub-block contract — port-wiring, double-driven
instances, refdes collisions after flatten. E15 fires when an R+R
rail-to-GND topology can't be classified as a voltage divider
without a hint (tap-name regex or `role: divider`). Each rule's
trigger, severity, and suppression recipe lives in the catalog:
[`rules.json`](../../../../src/circuitsmith/knowledge/rules.json).

---

## E16 — BJT pin role unset (EPIC-014, TASK-123)

**Trigger.** A component whose profile category is `transistor`
has one or more pins in `pins_detail` without a `role:`
annotation.

**Meaning.** The direction-sensitive kernel rule (ADR-0015) reads
`role:` to identify base / collector / emitter; an unset role
leaves the device unplaceable. Fails fast at ERC rather than
producing a confusing kernel escalation.

**Severity.** ERROR by default. The v1 `bjt_npn` and `bjt_pnp`
profiles ship with `role:` on every pin, so the check is silent
on existing fixtures.

**Suppression.** Add `role: "base" | "collector" | "emitter"` to
every pin in the profile's `pins.X` dict. Per the EPIC-014
frozen-decisions table the role enum is closed in v1; FET /
Darlington follow-ups extend it.

**Catalog.** [`rules.json` → E16](../../../../src/circuitsmith/knowledge/rules.json).

---

## E17 — Op-amp power pin floating (EPIC-014, TASK-123)

**Trigger.** A component whose `metadata.kind == "opamp"` has a
`POWER_INPUT`-typed pin that is not a member of any declared net.

**Meaning.** Op-amp supply pins have no safe floating defaults —
an unconnected `V+` or `V-` is a silicon-damage trap that the
schematic must surface before render. The check reads the
profile's pin-type tag, not the literal pin name, so single-
supply op-amp profiles (future work) inherit the rule for free.

**Severity.** ERROR by default.

**Suppression.** Wire both supply pins to the appropriate rails.
A `meta.erc: { E17: off }` global suppression is reserved for
experimental fixtures and should never ship.

**Catalog.** [`rules.json` → E17](../../../../src/circuitsmith/knowledge/rules.json).

---

## E18 — 555 pin-naming drift (EPIC-014, TASK-123)

**Trigger.** A connection on a component whose `metadata.kind ==
"timer"` references a silicon-name alias (`T1.GND`) rather than
the silkscreen-pin form (`T1.1`).

**Meaning.** Both forms resolve to the same electrical pin
(TASK-121's S5 extension accepts aliases). The warning encourages
the silkscreen-pin form as canonical per ADR-0010 — style-only,
the underlying netlist is identical. The warning message names
the silkscreen-pin replacement (`T1.GND` → `T1.1`).

**Severity.** WARNING by default. Suppressing is fine when the
team prefers the silicon-name form.

**Suppression.** Either replace each silicon-name reference with
the silkscreen-pin form the warning names, or set
`meta.erc: { E18: off }` globally to prefer the silicon-name form
across the file.

**Catalog.** [`rules.json` → E18](../../../../src/circuitsmith/knowledge/rules.json).

## E19 — Page declared but empty (EPIC-014, TASK-127)

**Trigger.** A page name appears in the layout's top-level
`pages:` block, but no placement carries that name in its `page:`
field.

**Meaning.** Pages partition the slot vocabulary
(see [layout.md / Pages partition](layout.md)); a declared page
commits the renderer to emitting a blank `<stem>-pN.svg`. An
empty page is almost always a leftover from a placement-tag typo
or an in-progress edit.

**Severity.** WARNING.

**Suppression.** Delete the empty page from `pages:`, or fix the
placement-tag typo that should have populated it. For
intentional placeholder pages, `meta.erc: { E19: off }`.

**Catalog.** [`rules.json` → E19](../../../../src/circuitsmith/knowledge/rules.json).

## E20 — Page referenced but undeclared (EPIC-014, TASK-127)

**Trigger.** A placement carries `page: pX` where `pX` is not in
the top-level `pages:` block.

**Meaning.** Schema-level cross-validation catches the same drift
(`layout-page-undeclared`); E20 is the ERC mirror so a stale
`.layout.yml` surfaces in the ERC report alongside any layout-
schema findings.

**Severity.** ERROR.

**Suppression.** Either add the missing page to `pages:` or
correct the placement's `page:` value.

**Catalog.** [`rules.json` → E20](../../../../src/circuitsmith/knowledge/rules.json).

## E21 — Cross-page net invisible on one side (EPIC-014, TASK-127)

**Trigger.** A net's pins span ≥ 2 pages, but at least one local
endpoint's placement has no resolvable region (missing
`region:`, broken `attached-to` chain).

**Meaning.** Cross-page labels (TASK-126) are the only on-sheet
trace of a net continuation. When the renderer can't compute the
local-side anchor, the label is dropped silently and a reader
has no way to know the net continues on another page. E21 makes
the silent drop loud.

**Severity.** ERROR.

**Suppression.** Resolve the kernel escalation on the local-side
ref — typically by hand-authoring a `free`-slot entry in
`.layout.yml`, or by adding a missing component profile. For
intentionally unrouted pins, `meta.erc: { <NET>: { E21: off } }`.

**Catalog.** [`rules.json` → E21](../../../../src/circuitsmith/knowledge/rules.json).

## E22 — Excessive cross-page net count (EPIC-014, TASK-127)

**Trigger.** More than the configured threshold of distinct nets
cross a single page-pair boundary (default 6; override via
`meta.erc.cross-page-threshold`).

**Meaning.** Heuristic. Many cross-page nets between the same two
pages usually means a logical block was split across sheet
boundaries by accident; the cognitive cost of following many
labels exceeds the benefit of the split.

**Severity.** WARNING.

**Suppression.** Re-partition the offending placements so the
heavily-connected block lives on one page, or raise the
threshold via `meta.erc.cross-page-threshold`, or
`meta.erc: { E22: off }`.

**Catalog.** [`rules.json` → E22](../../../../src/circuitsmith/knowledge/rules.json).
