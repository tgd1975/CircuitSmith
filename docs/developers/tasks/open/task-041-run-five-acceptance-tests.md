---
id: TASK-041
title: Run the five Phase 6 acceptance tests
status: open
opened: 2026-05-12
effort: Large (8-24h)
complexity: Senior
human-in-loop: Main
epic: circuit-skill-packaging
order: 13
prerequisites: [TASK-040]
---

## Autonomy

`Main` kept per TASK-060 sweep. Interactive five-test acceptance
session requires the user driving the skill end-to-end — agent
stops here, user runs the session.

**Non-blocking within EPIC-006 (2026-05-13 reorganisation).** This
task ran at order 3 originally and gated TASK-042 / TASK-080 — that
ordering kept the entire epic stalled behind a Main-HIL interactive
session that the user runs on their own cadence. Under the reshuffle,
no other task in this epic depends on TASK-041; it lives at the end
of the order list and is closed when the user has time to run the
five-test session. The soft "real-circuit-use" gate documented in the
EPIC-006 body still applies to the `0.1.0.dev0 → 0.1.0` version bump
in TASK-080, but TASK-041's formal ceremony does not gate the publish
step itself.

## Description

Run the five acceptance tests defined in
`idea-001.skill-packaging.md` end-to-end via the registered skill.
Each test exercises a distinct capability and must pass for Phase 6
to close:

1. **Happy path** — author a minimal LED-blinker circuit from a
   natural-language prompt; ERC green; SVG renders.
2. **ERC error** — introduce a missing LED resistor; ERC fires E5;
   skill explains the finding using the catalog enrichment.
3. **New component (BME280 over I2C)** — add a sensor profile from a
   prompt; ERC activates E7 (I2C pull-up); skill resolves with 4.7 kΩ
   pull-ups grounded in the catalog.
4. **Controller swap to Raspberry Pi with analog sensor** — must
   surface `HW-RPI-01` from the catalog and route the sensor through
   an external ADC, not directly to GPIO.
5. **Incremental layout stability** — add a sixth LED to the happy
   path; `layout.yml` diff is one added line; kept components' slots
   are byte-identical; SVG diff localised to the new LED column.

Per Phase 6 acceptance under v0.1 kernel-only: tests must pass whether
or not Phase 2b has shipped.

## Acceptance Criteria

- [ ] All five tests pass in a single recorded session, captured as a transcript in `tests/acceptance/phase6-session.md`.
- [ ] Test 4 surfaces `HW-RPI-01` and routes through an external ADC; the proposed circuit is electrically correct.
- [ ] Test 5's `layout.yml` diff is verified by `diff` (not by eyeball) — exactly one added line.
- [ ] Any test failure is filed as a new task under the appropriate epic, not patched into TASK-041 itself.

## Test Plan

Each acceptance test is itself the test plan — run the skill against the documented prompts, capture results, verify acceptance criteria. The transcript is the regression artefact going forward.

## Prerequisites

- **TASK-040** — skill must be registered to be invokable.

## Sizing rationale

Sized Large because the five tests cover the full skill surface; running them, capturing transcripts, and triaging failures is the dominant cost. Splitting per-test produces fragile dependencies — test 5 needs test 1's output as input.

## Notes

If test 4 stalls with a `no-canonical-rule` escalation under v0.1
kernel-only, the resolution is a hand-authored `free`-slot entry in
`layout.yml` plus a `§5.3` table follow-up (a new task in EPIC-002),
not a Phase 2b blocker.
