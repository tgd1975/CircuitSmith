---
id: TASK-117
title: Sub-block ERC rules (4 rules)
status: open
opened: 2026-05-14
effort: Medium (2-8h)
complexity: Medium
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 8
prerequisites: [TASK-116]
---

## Description

Adds the four sub-block ERC rules from IDEA-008 *Implications for
ERC and renderer* to
[`src/circuitsmith/erc_engine.py`](../../../src/circuitsmith/erc_engine.py)
(see `co-erc-engine` reminder):

- **Sub-block port not wired** — an instance leaves a declared
  port floating with no top-level `connections:` entry. Error.
- **Sub-block declared but never instantiated** — YAML parses but
  the user almost certainly meant to use it. Warning.
- **Refdes collision after flatten** — internal invariant; fires
  only from a flattener bug or a user-supplied refdes override
  that breaks uniqueness. Error.
- **Instance port double-driven** — two top-level `connections:`
  entries assign different nets to the same `<instance>.<port>`.
  Error.

Rule IDs (`E18`, `E19`, …) are minted from the existing catalogue
when the work lands.

## Acceptance Criteria

- [ ] All four rules added with rule codes, catalogue entries, and error-message text.
- [ ] Each rule has a golden failing fixture *and* a golden negative fixture (`tests/fixtures/erc/sub-block-*/`).
- [ ] ERC catalogue documentation in [.claude/skills/circuit/docs/erc-checks.md](../../../.claude/skills/circuit/docs/erc-checks.md) gains rows for the four rules.
- [ ] No regression on existing ERC fixtures.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/erc/test_sub_block_rules.py`.
- Cover: each of the four rules with both a failing case and a
  negative (clean) case; rule-ordering determinism in the rendered
  report (`erc_report.py`).

## Prerequisites

- **TASK-116** — the flattener must exist and expose the
  invariants these rules check (port-wiring, refdes uniqueness,
  port-driver count).

## Notes

- The four rules are tightly related and share a fixture base
  (the same `rc_lowpass` sub-block definition, mutated in
  different ways per rule). One task keeps the fixture
  authoring coherent.
- Rule IDs are minted at merge time — do not hard-code `E18`
  etc. in this task body. Read the current ERC catalogue's
  highest assigned ID at task-active time and increment from
  there.
