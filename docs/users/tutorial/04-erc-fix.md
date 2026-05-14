---
status: complete
---

# Step 4 — Fixing an ERC failure

## What you'll do

Author a button circuit *with a deliberate mistake* — an MCU input
that has no defined idle level — then read the ERC report to find
the rule that flagged it, look up the rule's rationale, and fix the
YAML. By the end you'll know how to round-trip an ERC complaint
without leaving the `.circuit.yml`.

## The broken `.circuit.yml`

[`04-erc-fix.broken.circuit.yml`](04-erc-fix.broken.circuit.yml) is
the simplest possible button circuit: a pushbutton on `U1.D13`,
sourced from `J1`. The catch — the net does not declare a pull. The
button-to-GND wiring assumes *something* will hold the GPIO at a
defined level when the button is open, but neither a hardware
pull-up nor a `pull: firmware` declaration is present, so the input
will float.

## Running the skill (and reading the failure)

```bash
python -m circuitsmith.renderer \
  --circuit docs/users/tutorial/04-erc-fix.broken.circuit.yml \
  --out    docs/users/tutorial/04-erc-fix.broken.svg \
  --out-layout      docs/users/tutorial/04-erc-fix.broken.layout.yml \
  --out-meta        docs/users/tutorial/04-erc-fix.broken.meta.yml \
  --out-erc-report  docs/users/tutorial/04-erc-fix.broken.erc-report.md \
  --no-ai
```

The render succeeds (you still get an SVG), but the ERC report
[`04-erc-fix.broken.erc-report.md`](04-erc-fix.broken.erc-report.md)
now contains two warnings:

```text
| ⚠️ WARNING | U1 | D13 | E1 Floating input  | BTN_USER | signal input U1.D13 on net 'BTN_USER' could not be classified …
| ⚠️ WARNING | J1 | VBUS | E9 Reverse-polarity unprotected | VCC      | power input pin J1.VBUS … (WARNING at v0.1 pending the `diode` category.)
```

The second line is the expected pending-promotion warning from steps
1-3 (it appears on every USB-C-powered circuit until the `diode`
component category lands). The new finding is **E1 — Floating input
on `U1.D13`** — exactly the deliberate mistake.

Note: E1's intended severity is ERROR. The v0.1 engine downgrades it
to WARNING when it cannot classify the pin's role with full
confidence; the pending-promotion note in the report explains. The
tutorial reader sees a WARNING-level finding and a clear teaching
narrative; future versions will surface this as ERROR.

## Reading the rule

Each finding in the report is followed by a *Why*, a *Senior's tip*,
and a *Source* link. The body of the E1 finding tells you:

> An MCU input pin that is neither driven nor pulled floats. Its
> measured voltage swings on capacitive coupling from neighbouring
> traces and the input reads as random bits.

And the tip points at the fix:

> For a typical button-to-GND wired on an MCU GPIO, enable
> `INPUT_PULLUP` in firmware and declare `pull: firmware` on the
> net — that is the cheapest defined idle state.

The catalog entry behind those lines lives in
[`src/circuitsmith/knowledge/rules.json`](../../../src/circuitsmith/knowledge/rules.json)
as the `E1` record. The reference catalog itself is summarised in
[`erc-checks.md`](../../../.claude/skills/circuit/docs/erc-checks.md)
for the `/circuit` skill.

## The fix

Add the one line the tip names:

```diff
   - net: BTN_USER
     path: [U1.D13, SW1.1, SW1.2, GND]
+    pull: firmware
```

The fixed circuit lives at
[`04-erc-fix.fixed.circuit.yml`](04-erc-fix.fixed.circuit.yml). Run
the renderer again on the fixed file (same flags, just point at the
`.fixed.` files), and the new ERC report
[`04-erc-fix.fixed.erc-report.md`](04-erc-fix.fixed.erc-report.md)
no longer contains the E1 line — only the expected E9 pending-
promotion warning remains.

## What just happened

Two subsystems exercised:

- **The ERC engine** classified `U1.D13`'s role as a signal input
  (it sits on a path that terminates at a GND-tied button) and
  applied rule E1. The fix changed the net's declared pull mode,
  which the engine reads as "the firmware owns this input's idle
  level," and the rule passes.
- **The catalog-enriched report writer** rendered each finding with
  its rationale, tip, and source link — the report is the same
  shape every time, so the round-trip ("see warning → read tip →
  fix YAML → re-run") is mechanical.

## Next

[Step 5 — Exporting the BOM](05-bom-export.md) — what the BOM
artefact looks like, where it lands, and the manual PartsLedger
round-trip.
