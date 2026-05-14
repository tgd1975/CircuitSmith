---
example: common-emitter-amplifier
status: blocked-on-component-profile
---

# Common-emitter amplifier

## What it demonstrates

The first analog-signal-flow gallery entry: a small-signal NPN
common-emitter amplifier. Biasing resistors set the quiescent
operating point, an input coupling capacitor blocks DC, an output
coupling capacitor delivers the amplified signal to the next stage,
and an emitter degeneration resistor stabilises gain across
temperature. The example teaches: how the catalog's analog-rule
chapter applies to a real biased active device.

## The input

Not yet committed — see "Blocked on" below.

The intended `circuit.yml` would declare:

- `Q1: { type: passives/bjt_npn, label: AMP }` (profile does not yet
  exist).
- Four resistors: `R_B1`, `R_B2` (base bias divider), `R_C`
  (collector load), `R_E` (emitter degeneration).
- Two capacitors: `C_IN` (input coupling), `C_OUT` (output
  coupling).
- A power source and a signal input/output pair.

## Blocked on

> **v0.1 component-profile gap.** The CircuitSmith day-one
> component library ships passives and MCU profiles only — no
> active devices. A `bjt_npn` profile, with role/direction metadata
> the layout kernel can read (which terminal is signal-in, which is
> signal-out), is the prerequisite for this example. Until it
> lands, authoring a `circuit.yml` here would only produce S5
> errors at schema time and mislead future contributors about what
> the library supports.
>
> The missing capability is scheduled under
> [EPIC-014](../../../developers/tasks/open/epic-014-circuit-library-and-renderer-v2.md)
> (seeded by IDEA-008 and IDEA-009). This example lands when
> TASK-129 closes; the bjt_npn profile (TASK-120) and the
> active-device ERC (TASK-123) are the direct unblockers.

## What makes it interesting

When this entry unblocks, it will be the first gallery example with
a *direction-sensitive* active device — every previous example uses
two-terminal passives whose orientation is electrically symmetric.
The layout kernel needs to know that `Q1.C` goes "up" (toward the
load) and `Q1.E` goes "down" (toward GND), and the renderer needs
to draw the transistor symbol with the correct arrow direction.
That's the new mental model the example introduces.

## Next example

[555 monostable](../555-monostable/) — single-IC example, also
scheduled under EPIC-014 (TASK-130).
