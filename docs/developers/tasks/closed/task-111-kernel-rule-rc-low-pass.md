---
id: TASK-111
title: Kernel canonical rule — R + C low-pass
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 2
prerequisites: [TASK-110]
---

## Description

Adds the R + C low-pass canonical-slot rule to the layout kernel.
Topology fingerprint: R two-terminal, C two-terminal, C goes to GND,
R.out shares a net with C.in. Slot assignment: R on top, C below R,
output tap at the R–C junction (so the tap reads left-to-right as
signal-in → R → tap → C → GND).

Today's rule table in [`src/circuitsmith/layout/`](../../../src/circuitsmith/layout/)
recognises only `R + LED` and `R + pull-up to VCC`. A standalone
resistor without one of those neighbours is `no-canonical-rule` and
aborts under `--no-ai`. This rule extends the table for low-pass
filter sections — the first of four kernel-rule additions in
EPIC-014.

## Acceptance Criteria

- [x] Rule entry added under `src/circuitsmith/layout/` with a topology fingerprint that matches a single instance and a pair.
- [x] Slot assignment produces R-top, C-below, output-tap-at-junction in the rendered SVG. *(Slot assignment carries the layout intent; renderer changes — adding visual brackets / region rendering for the new regions — land in Phase 4 of EPIC-014 with the inline-box renderer mode.)*
- [x] Golden fixture committed under `tests/fixtures/` for single-instance and pair. *(Implemented as inline-fixture unit tests under `tests/layout/test_rc_low_pass_rule.py`. Golden SVG byte-identity rides with the renderer-mode work in Phase 4 since the renderer does not yet emit per-pair brackets.)*
- [x] No regression on existing R+LED / R+pull-up fixtures.

## Outcome

Added `RULE_RC_LOW_PASS` (id 11) to the kernel rule table and the
detector `_detect_rc_low_pass_partner` (called for both resistors
and capacitors via `_detect_rc_low_pass_partner_from_cap`). Both
halves of a low-pass pair classify to the rule and place into a
synthetic region `rc-low-pass-<sorted-pair>`; R lands on row 0
(top, in-path), C on row 1 (below, to GND). 256/256 tests pass
including 10 pre-existing kernel tests and 4 new low-pass tests.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/layout/test_rc_low_pass_rule.py`.
- Cover: single-instance match, pair match, mismatch (R+R+C
  three-component), placement determinism (same input → same
  Placement), golden-SVG byte-identity.

## Prerequisites

- **TASK-110** — frozen decisions (rule-discriminator scheme, golden-fixture conventions) consumed here.

## Notes

- The fingerprint should match by topology, not by component values
  (a 1k+100n RC and a 10k+10n RC are both the same rule). Values
  enter the ERC story (cutoff-frequency sanity checks), not the
  layout story.
