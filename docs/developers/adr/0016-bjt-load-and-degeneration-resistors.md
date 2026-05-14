---
id: ADR-0016
title: Collector-load and emitter-degeneration resistors land in synthetic per-BJT regions
status: Accepted
date: 2026-05-14
dossier-section: docs/developers/ideas/archived/idea-001.layout-engine-concept.md#17.3-remaining-risks
supersedes:
---

## Context

ADR-0015 minted the BJT canonical slot but only handled the
base-drive resistor (via `attached-to`). A real common-emitter
amplifier (TASK-129's gallery target) ships three further passives
the kernel must classify deterministically:

- `R_C` — collector load: rail → `R_C` → `Q.C`.
- `R_E` — emitter degeneration: `Q.E` → `R_E` → GND.
- (`R_B1`/`R_B2` are already covered by `RULE_RR_VOLTAGE_DIVIDER`
  via `role: divider`.)

In `--no-ai` mode (the gallery regression script's default),
`R_C` reaches the pull-up rule but fails its anchor check
(`Q.C` is `POWER_INPUT`, not `GPIO`/`INPUT_ONLY`). `R_E` has no
power-rail terminal so the pull-up rule never fires. Both
escalate. The dossier's §17.3 "extend canonical-slot table one row
at a time" pattern says: add a row.

Three alternatives considered:

1. **Re-attach to the BJT via `attach_step: 2`** — overload the
   attached-to slot mechanism. Rejected: the router does not
   honour `attach_step` (every attached child collapses to one
   grid offset from the anchor), so two attached resistors would
   visually overlap the BJT. Fixing that is a router change, not
   a kernel rule.
2. **Synthetic per-BJT regions** — same shape as
   `divider-<tap>` / `rc-low-pass-<pair>` / `cc-decoupling-<pair>`:
   the placement records a region name the v0.1 router treats as
   "uncoordinatised" so the resistor lands in the layout without
   being drawn. The schematic still emits the wire-level
   netlist via ERC + BOM; the SVG omits the symbol. This is the
   established v0.1 trade-off documented for divider/RC/CC pairs.
3. **Promote to AI placer** — leave `R_C` / `R_E` to the v0.2 AI
   path. Rejected: the CE amplifier is the canonical analog
   smoke fixture and ADR-0015 explicitly promised it would render
   deterministically.

## Decision

Two new kernel rules:

- **`RULE_BJT_LOAD`** (id 18). Fires when a resistor's two
  terminals are: (a) on a net containing a `POWER` pin (the rail)
  AND (b) on a net containing a BJT pin with `role: collector`.
  Placement: synthetic region `bjt-load-<bjt-ref>`, row 0,
  `label: bjt-load`.
- **`RULE_BJT_DEGENERATION`** (id 19). Fires when a resistor's
  two terminals are: (a) on a GND-named net AND (b) on a net
  containing a BJT pin with `role: emitter`. Placement:
  synthetic region `bjt-degen-<bjt-ref>`, row 0,
  `label: bjt-degeneration`.

Both rules sit *above* the pull-up fallback in `_classify`'s
resistor branch, so a CE amplifier's `R_C` no longer reaches the
pull-up anchor check (which would fail) and `R_E` no longer falls
through to escalation.

The layout schema gains region patterns `^bjt-load-…` and
`^bjt-degen-…` mirroring the existing synthetic-region
alternatives (`divider-…`, `rc-low-pass-…`, etc.).

## Consequences

**Easier:**

- TASK-129's CE-amplifier gallery entry renders in `--no-ai` mode.
- The kernel's coverage of "BJT-with-passive-stack" shapes is
  closed under a single readable rule pair; future regulator /
  buffer fixtures with the same topology reuse them.
- The discriminator is shape-only — no hint regex, no `role:`
  override needed in `circuit.yml`. Matches the
  `RULE_RESISTOR_WITH_BJT` / `RULE_BJT_TO_GND` style.

**Harder:**

- The v0.1 router/renderer does not draw the load/degeneration
  resistor symbol (same trade-off as the divider/RC/CC pairs).
  A future task that coordinatises synthetic regions for the
  renderer picks these up automatically — no schema or kernel
  diff needed at that point.
- Multi-stage amplifiers (cascade, Darlington) still escalate;
  the rules match exactly one BJT per resistor terminal. The
  growth path remains ADR-0015's "split when push-pull / current
  mirror appear in real circuits".

## See also

- [ADR-0001](0001-slots-not-coordinates.md) — slot vocabulary
  this decision adds two rows to.
- [ADR-0015](0015-transistor-canonical-slot-right-column.md) —
  the prior decision that minted the BJT canonical slot and the
  base-drive attach mechanism. This ADR is its continuation for
  the load + degeneration resistors.
- [TASK-129](../tasks/active/task-129-gallery-reattempt-common-emitter-amplifier.md)
  — the gallery re-attempt that surfaced the kernel-coverage gap.
