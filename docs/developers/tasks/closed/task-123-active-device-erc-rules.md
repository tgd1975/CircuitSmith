---
id: TASK-123
title: Active-device ERC rules (BJT, op-amp, 555)
status: closed
closed: 2026-05-14
opened: 2026-05-14
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Medium
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 14
prerequisites: [TASK-120, TASK-121, TASK-122]
---

## Description

Adds the three active-device ERC rules from IDEA-009 *ERC — Half 1
(active devices)* to
[`src/circuitsmith/erc_engine.py`](../../../src/circuitsmith/erc_engine.py)
(see `co-erc-engine` reminder):

- **BJT pin-role unset** — a `bjt_npn` / `bjt_pnp` instance with
  no `role:` annotation on its three terminals can't be placed by
  the direction-sensitive layout rules. Error.
- **Op-amp power-pin floating** — `ic/opamp_dual_supply` instance
  where `V+` or `V-` has no `connections:` entry. Error. Analog
  ICs do not have safe floating-power-pin defaults the way some
  digital ICs do.
- **555 pin-naming drift** — a `.circuit.yml` `connections:` entry
  references `U1.GND` (silicon name) instead of `U1.1` (silkscreen
  pin number) on a `ic/555` instance. Warning, with a suggestion
  to use the alias from `pins["1"].alt`. The renderer accepts
  either form (renders the same); the warning catches the
  inconsistency before it spreads.

Rule IDs are minted from the existing ERC catalogue when the work
lands.

## Acceptance Criteria

- [ ] All three rules added with codes, catalogue entries, and error-message text.
- [ ] Each rule has a golden failing fixture *and* a golden negative fixture under `tests/fixtures/erc/`.
- [ ] ERC catalogue documentation in [.claude/skills/circuit/docs/erc-checks.md](../../../.claude/skills/circuit/docs/erc-checks.md) gains rows for the three rules.
- [ ] No regression on existing ERC fixtures.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/erc/test_active_device_rules.py`.
- Cover: each of the three rules with both failing and negative
  cases; rule-ordering determinism in the rendered report; the
  555 warning's suggestion text names the correct alias from the
  profile's `pins["N"].alt` field.

## Prerequisites

- **TASK-120** — bjt_npn / bjt_pnp profiles must exist for the
  pin-role-unset rule to fire against them.
- **TASK-121** — ic/555 profile must exist for the
  pin-naming-drift rule.
- **TASK-122** — ic/opamp_dual_supply profile must exist for the
  power-pin-floating rule.

## Notes

- The three rules are independent in terms of code paths but
  share a fixture base (the same active-device circuits with
  targeted defects). One task keeps the fixture authoring
  coherent.
- The 555 pin-naming-drift rule is the only *warning* of the
  three. Don't escalate it to an error — both pin-naming forms
  resolve to the same net, so the user's circuit is correct;
  the warning catches a style drift, not a defect.
