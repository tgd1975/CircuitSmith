---
example: 555-monostable
status: blocked-on-component-profile
---

# 555 monostable timer

## What it demonstrates

A single-IC gallery entry: a 555 timer wired as a one-shot
monostable. A trigger pulse on `TRIG` starts a timed `OUT` high
pulse whose duration is set by the external R-C network on `THRES`
and `DISCH`. The example teaches: how an integrated circuit
component participates in the schema (named pins, multi-pin
package), and how the catalog's analog-timing rules apply.

## The input

Not yet committed — see "Blocked on" below.

The intended `circuit.yml` would declare:

- `U2: { type: ic/555, label: TIMER }` (profile does not yet
  exist).
- One timing resistor `R_T`, one timing capacitor `C_T`.
- A control-pin decoupling cap `C_CTRL` on `CTRL`.
- A trigger pushbutton + pull-up.
- An output indicator LED + series resistor.

## Blocked on

> **v0.1 component-profile gap.** No `ic/555` profile in the day-one
> library. The eight-pin DIP/SOIC package and the canonical 555 pin
> names (`GND`, `TRIG`, `OUT`, `RESET`, `CTRL`, `THRES`, `DISCH`,
> `VCC`) need a profile entry before the schema validator will
> accept references to them.
>
> Filed as
> [IDEA-009](../../../developers/ideas/open/idea-009-active-device-profiles-and-multi-page-renderer.md).

## What makes it interesting

When this entry unblocks, it will be the gallery's first
**multi-pin IC** example. Every prior example uses two- or
three-terminal devices on a small dev-board MCU; the 555 introduces
the rectangular IC symbol, named pins on multiple sides, and
power-pin conventions distinct from the MCU's `VBUS`/`GND`/etc.
That's the new schema vocabulary the example introduces.

## Next example

[Op-amp non-inverting buffer](../opamp-non-inverting-buffer/) —
another IC-flavoured example, also blocked on IDEA-009.
