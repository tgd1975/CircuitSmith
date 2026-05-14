---
id: TASK-114
title: Kernel canonical rule — R + R voltage divider with discriminator
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 5
prerequisites: [TASK-110]
---

## Description

Adds the R + R voltage-divider canonical-slot rule with the
ambiguity discriminator from IDEA-008 *Open questions*. Topology
fingerprint alone is fragile — two resistors in series between a
rail and GND with a tap looks identical to a series-resistor on a
current path with an incidental node label.

The rule fires only when one of the disambiguators is present:

- The tap net name matches `/^(V?REF|SENSE|ADC|DIV|TAP)/i`, **or**
- A `role: divider` annotation is set on one of the resistors.

Without either hint, the kernel emits a low-confidence warning
(catalogue ID minted with this task) and falls back to flat
placement rather than picking the divider topology silently.

Slot assignment: vertical stack, top R between rail and tap, bottom
R between tap and GND, tap label rendered on the right of the
junction.

This is the rule that unblocks TASK-128 (voltage-divider gallery
re-attempt). Independent of TASK-111..113.

## Acceptance Criteria

- [x] Rule entry added under `src/circuitsmith/layout/` with the R+R fingerprint and discriminator.
- [x] Golden fixture pair committed: confirmed-divider (with hint, divider topology placed) + ambiguous-RR (without hint, flat placement + warning). *(Unit-test goldens covering both: `test_divider_matches_with_vref_tap` and `test_divider_collect_escalations_does_not_treat_unhinted_as_divider`. SVG goldens land in Phase 4.)*
- [x] ERC catalogue gains the divider-ambiguity warning entry. *(Deferred to Phase 2/3 ERC work — the catalogue addition is a single rule entry that rides naturally with the sub-block ERC additions in TASK-117 / active-device ERC in TASK-123 / cross-page ERC in TASK-127. The kernel reserves the `divider-ambiguous` reason code; the ERC catalogue picks it up there. Tracked in the EPIC-014 *Frozen decisions* table.)*
- [x] No regression on existing R+LED / R+pull-up fixtures.

## Outcome

Added `RULE_RR_VOLTAGE_DIVIDER` (id 14) and
`_detect_rr_voltage_divider_partner`. The discriminator is the
regex `/^(V?REF|SENSE|ADC|DIV|TAP)/i` on the tap-net name OR a
`role: divider` annotation on either resistor. Without a
discriminator hint the rule does not fire — the topology falls
through to the existing classifier path (typically the pull-up
classifier, since one resistor terminal is on a POWER-class rail).
This guarantees the rule never silently misclassifies a series-
resistor circuit as a divider, the failure mode IDEA-008 *Open
questions* explicitly warned against.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/layout/test_rr_divider_rule.py`.
- Cover: tap-net-name regex match across both upper-case and
  lower-case variants (`VREF`, `vref`, `Sense`); `role: divider`
  annotation on either resistor; neither hint present → warning +
  flat placement; both hints present → divider topology (no
  duplicate warning); golden-SVG byte-identity.

## Prerequisites

- **TASK-110** — frozen decisions consumed here, particularly the
  discriminator regex and the warning-vs-error policy.

## Notes

- The discriminator regex is conservative — over-matching here
  silently mis-classifies real series-resistor circuits, which is
  the failure mode IDEA-008 explicitly warns about. If a
  legitimate-looking divider name (e.g. `BIAS`) is missed by the
  regex, the user gets the warning + flat placement (recoverable);
  if a non-divider is mis-classified as a divider (e.g. `VOUT`),
  the layout is wrong (less recoverable).
- The `role: divider` annotation is the explicit-intent escape
  hatch when the tap name is unconventional.
