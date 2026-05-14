---
id: IDEA-008
title: First-class sub-block authoring + kernel rules for non-LED passive groupings
description: Add explicit sub-block syntax in .circuit.yml and canonical kernel rules for RC/RC-low-pass/decoupling-pair groupings
category: 🛠️ tooling
---

## Motivation

Tutorial step 3 (TASK-094, EPIC-012) wanted to demonstrate an RC
filter as a *repeated sub-block* — two copies of the same
"resistor + capacitor to ground" pattern, side by side, with the
placer treating them as identical sub-systems. The v0.1 layout
kernel rejects this: it only has canonical rules for R+LED (status
indicator) and R+pull-up (button pull). A standalone resistor
without an LED or pull-up is `no-canonical-rule` and aborts under
`--no-ai`.

The tutorial falls back to *three* R+LED status indicators instead,
which exercises the "repeated sub-block" pedagogy correctly but
misses the broader point: real-world circuits routinely repeat RC
filter sections, decoupling capacitor pairs, voltage-divider
networks. Those are the next layer of "repeated sub-blocks" the
user expects after they understand the LED-bank case.

## Two halves of the fix

Both halves are independent and can land in either order; they
multiply each other.

### Half 1 — kernel canonical rules for the common non-LED groupings

Today's rule table (`src/circuitsmith/layout/`) recognises:

- `R + LED` → right-column stack, R attached-to LED.
- `R + pull-up to VCC` → on-path inline with button.

The minimal additions to cover the textbook patterns:

- `R + C (low-pass)` — RC pair where the cap goes to GND and the
  output is taken at the R-C junction. Place vertically with the
  cap below the R.
- `R + C (high-pass)` — RC pair where the cap is in series and the
  R goes to GND. Mirror of low-pass.
- `C + C (decoupling pair)` — two caps in parallel from one rail
  to GND, sometimes seen as `100 nF || 10 µF`. Stack tightly with
  shared GND.
- `R + R (voltage divider)` — two Rs in series between a rail and
  GND with a tap. Place vertically; the tap label is the net name.

Each rule needs a topology-fingerprint match in the kernel and a
slot assignment for the constituent components.

### Half 2 — `.circuit.yml` sub-block syntax

Today the user must repeat the pattern by hand:

```yaml
R3a: { type: passives/resistor, value: 10000 }
C3a: { type: passives/capacitor, value: 100n }
R3b: { type: passives/resistor, value: 10000 }
C3b: { type: passives/capacitor, value: 100n }
```

That works but doesn't *say* "these two pairs are the same
sub-block." A first-class form:

```yaml
sub-blocks:
  rc_lowpass:
    components:
      R: { type: passives/resistor, value: 10000 }
      C: { type: passives/capacitor, value: 100n }
    connections:
      - net: filtered
        path: [R.1, R.2, C.1]
      - net: GND
        pins: [C.2]
    inputs: [R.1]
    outputs: [R.2]

instances:
  FILT_A: { sub-block: rc_lowpass }
  FILT_B: { sub-block: rc_lowpass }

connections:
  - net: SIGNAL_A
    path: [U1.D2, FILT_A.input]
  - net: SIGNAL_B
    path: [U1.D4, FILT_B.input]
```

The instance names (`FILT_A`, `FILT_B`) become the placer's
slot-assignment unit; the kernel knows each instance is one
sub-block and can stack them in the right-column region the same
way it stacks LED branches today.

## Acceptance shape

A future task / epic that closes this idea will probably split
into:

- One task per kernel canonical rule (Half 1).
- One task for the schema extension + netgraph builder support
  (Half 2 syntax + flattening).
- One task for tutorial step 3's full rewrite to use the new
  sub-block form once it lands.
- One renderer-chapter doc update.

## Cross-references

- [TASK-094](../tasks/open/task-094-tutorial-steps-1-3-minimal-and-fan-out.md)
  — the task whose fallback path filed this idea. Its closure
  references this file as the source of the missing capability.
- [ADR-0001](../adr/0001-slots-not-coordinates.md) — the slot
  vocabulary kernel canonical rules write into. Half 1 extends this
  vocabulary; Half 2 doesn't change it but feeds new compositions
  into it.
- [`src/circuitsmith/layout/`](../../../src/circuitsmith/layout/) —
  the directory where Half 1's rule additions land.
