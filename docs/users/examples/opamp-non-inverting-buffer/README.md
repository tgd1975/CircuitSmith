---
example: opamp-non-inverting-buffer
status: blocked-on-component-profile
---

# Op-amp non-inverting buffer

## What it demonstrates

An op-amp wired as a unity-gain non-inverting buffer on a dual-rail
supply (`V+` / `V-`). The input signal goes to `IN+`, the output
feeds straight back to `IN-` through a wire (no resistor divider —
the gain is 1), and the output goes to the load. The example
teaches: op-amp pin conventions, dual-rail power supplies, and the
catalog's negative-feedback rules.

## The input

Not yet committed — see "Blocked on" below.

The intended `circuit.yml` would declare:

- `OA1: { type: ic/opamp_dual_supply, label: BUF }` (profile does
  not yet exist).
- A dual-rail power source providing `V+` and `V-`.
- Decoupling caps on each rail near the op-amp's power pins.
- An input signal source (or just a labelled net coming from
  outside).
- An output load (or a labelled net going elsewhere).

## Blocked on

> **v0.1 component-profile gap.** No `ic/opamp_dual_supply` profile
> in the day-one library. The five-pin op-amp (`IN+`, `IN-`, `OUT`,
> `V+`, `V-`) needs a profile entry, the renderer needs to know to
> draw the triangle symbol with the correct sign convention on the
> input pins, and the catalog needs at least one rule that fires on
> a missing feedback path or a power-rail mistake.
>
> Scheduled under
> [EPIC-014](../../../developers/tasks/open/epic-014-circuit-library-and-renderer-v2.md)
> (seeded by IDEA-009). This example lands when TASK-131 closes;
> the ic/opamp_dual_supply profile (TASK-122) is the direct
> unblocker.

## What makes it interesting

When this entry unblocks, it will be the gallery's first
**dual-rail supply** example. Every prior example uses a single
`VCC` rail from a 5 V USB-C source; the op-amp introduces the
`V+`/`V-` split-rail convention, the decoupling-pair pattern near
the IC power pins, and the schema vocabulary for negative-supply
nets. The triangle symbol with feedback path is the canonical
op-amp schematic.

## Next example

[Multi-page split](../multi-page-split/) — the largest gallery
entry, scheduled under EPIC-014 (TASK-132) — exercises the
renderer's page-break path.
