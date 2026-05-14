---
example: multi-page-split
status: blocked-on-renderer-page-break
---

# Multi-page split

## What it demonstrates

The gallery's stress-test entry: a circuit large enough that the
renderer must break it across multiple SVG pages. The example
teaches: how net labels at page boundaries cross-reference between
sheets, how `.layout.yml`'s page-assignment vocabulary works, and
how a contributor decides where the split goes.

## The input

Not yet committed — see "Blocked on" below.

The intended `circuit.yml` would declare a circuit the size of the
existing `data/esp32.circuit.yml` (an MCU plus a status-LED bank
plus a button matrix) but with one or two extra subsystems (e.g. a
small SPI bus to an external chip plus an I²C sensor) that push the
component count past whatever single-page threshold the renderer
chooses. A `.layout.yml` would carry `page: 1` / `page: 2`
assignments to direct the split.

## Blocked on

> **v0.1 renderer single-page only.** The CircuitSmith v0.1
> renderer emits one SVG per circuit. There is no `pages:` slot
> vocabulary, no inter-sheet net-label connector, no multi-output
> `--out` flag. Authoring a circuit that "needs" multiple pages
> wouldn't surface the split anywhere — the renderer would either
> cram everything onto one oversized sheet or refuse, depending on
> internal limits.
>
> Scheduled under
> [EPIC-014](../../../developers/tasks/open/epic-014-circuit-library-and-renderer-v2.md)
> (seeded by IDEA-009). This example lands when TASK-132 closes;
> the renderer multi-page driver (TASK-125), cross-page net labels
> (TASK-126), and cross-page ERC (TASK-127) are the direct
> unblockers. The example also uses the bjt_npn profile
> (TASK-120) for at least one stage of the audio chain.

## What makes it interesting

When this entry unblocks, it will be the only gallery example whose
*primary purpose* is to exercise a renderer code path rather than
teach a circuit-design concept. The committed pair of SVG sheets +
the layout sidecar with explicit page assignments will be the
canonical reference for how multi-page circuits look in
CircuitSmith.

## Next

This is the last gallery entry in the suggested reading order.
Once all five examples render, the
[CI regression-diff guard](../../../developers/tasks/closed/task-101-ci-regression-diff-for-gallery.md)
runs the full pipeline against every committed `.circuit.yml` and
fails the build on any drift.
