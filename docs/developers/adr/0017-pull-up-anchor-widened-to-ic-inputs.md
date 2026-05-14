---
id: ADR-0017
title: Pull-up resistor anchor widened to IC SIGNAL_INPUT pins
status: Accepted
date: 2026-05-14
dossier-section: docs/developers/ideas/archived/idea-001.layout-engine-concept.md#17.3-remaining-risks
supersedes:
---

## Context

The day-one pull-up rule (`RULE_PULLUP_RESISTOR`, minted in
TASK-103) anchors the resistor to an MCU pin: `_shape_meta_pullup`
walks the resistor's nets looking for a `GPIO` or `INPUT_ONLY` pin
and falls back to escalation otherwise. The shape was minted from
button-and-LED tutorial circuits where every pull-up sits between
VCC and an MCU GPIO.

TASK-130's 555 monostable surfaced a real case the rule does not
cover: `R_TRIG` pulls the 555's `TRIG` pin (`U1.2`, profile-typed
`SIGNAL_INPUT`) high, with a pushbutton briefly grounding it to
fire the one-shot. Electrically this is the same canonical pull-up
shape; the anchor pin is just on an IC, not an MCU. Without
widening, `R_TRIG` escalates with `no-canonical-rule` and the
gallery entry cannot render in `--no-ai` mode.

The neighbouring options considered:

1. **Synthetic per-IC bias region** (mirror ADR-0016's BJT
   load/degen rules) — `RULE_IC_PULLUP` with region
   `ic-bias-<ic-ref>-<pin>`. Rejected: the existing pull-up's
   `path-of-<anchor>` region already captures the right placement
   semantics — a pull-up belongs on the path of the pin it pulls
   up, irrespective of whether that pin is on an MCU or an IC.
   Forking a parallel rule duplicates the slot vocabulary for no
   placement-shape gain.
2. **YAML `role:` override** (`role: ic_pullup`) — lightweight, but
   pushes the discrimination into authoring time. The shape is
   trivially detectable from profile metadata; making the user
   spell it out adds friction and a way to forget.
3. **Restructure the 555 monostable to omit the pull-up** — the
   pushbutton would have to drive `TRIG` low while floating it
   high otherwise. Electrically marginal (susceptible to noise);
   pedagogically misleading. Rejected.

## Decision

Widen `_shape_meta_pullup` to accept `SIGNAL_INPUT` as a valid
anchor pin type, in addition to `GPIO` and `INPUT_ONLY`. The
search is two-pass with priority order: MCU-side
(`GPIO` / `INPUT_ONLY`) first, then IC-side (`SIGNAL_INPUT`). This
preserves placement for any circuit that happens to have both an
MCU GPIO *and* an IC input on the same pull-up — the MCU anchor
wins, matching the day-one tutorial behaviour.

A second change tightens the net-walk: the search now restricts to
the resistor's *own two nets* and skips the rail net (identified by
the presence of any `POWER` or `POWER_INPUT` pin on the net). This
prevents an unrelated SIGNAL_INPUT pin coincident on the rail (e.g.
a 555 RESET tied high to VCC) from being mistaken for the
resistor's signal-side anchor. The pre-widening rule could not
exhibit this bug because no MCU pin types are POWER-typed; the
widening to SIGNAL_INPUT brings 555-class topologies into the rule
and surfaces the need for the rail-skip.

The placement region (`path-of-<anchor>.<pin>`) is unchanged — the
`anchor.ref` and `anchor.pin` already carry through the new IC-pin
form (e.g. `path-of-U1.2`).

## Consequences

**Easier:**

- TASK-130's 555 monostable gallery entry renders deterministically.
- Future IC-driven examples (LED driver enable pins, latch
  flip-flop set/reset inputs, etc.) inherit the widened rule
  without per-fixture kernel changes.
- The shape stays "one rule, one slot" — no new region pattern,
  no schema diff.

**Harder:**

- A net with *both* an MCU GPIO and an IC `SIGNAL_INPUT` on a
  pull-up's signal-side net now silently prefers the GPIO anchor.
  No known circuit hits this; if it shows up, the priority order
  is the natural place to revisit.
- `SIGNAL_INPUT` is now meaningful as a layout-anchor pin type in
  addition to its ERC role. Future component profiles that use
  `SIGNAL_INPUT` for a pin that is *not* a valid pull-up target
  (none in the day-one library) would need either a profile-side
  refinement or a `role:` override on the resistor.

## See also

- [ADR-0001](0001-slots-not-coordinates.md) — slot vocabulary
  the pull-up rule sits in.
- [ADR-0015](0015-transistor-canonical-slot-right-column.md) and
  [ADR-0016](0016-bjt-load-and-degeneration-resistors.md) — the
  prior pair of EPIC-014 kernel-rule additions; this ADR fills the
  analogous gap for the IC family.
- [TASK-103](../tasks/closed/task-103-rule-pullup-resistor.md)
  — the pull-up rule's original minting (anchor narrowed to MCU
  pins).
- [TASK-130](../tasks/active/task-130-gallery-reattempt-555-monostable.md)
  — the gallery re-attempt that surfaced the kernel-coverage gap.
