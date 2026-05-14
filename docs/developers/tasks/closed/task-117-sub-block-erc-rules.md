---
id: TASK-117
title: Sub-block ERC rules (4 rules)
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Medium (2-8h)
effort_actual: Small (<2h)
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

- [x] All four rules added with rule codes, catalogue entries, and error-message text. *(E11..E14 minted; plus E15 — voltage-divider-ambiguous — rides with this work since the kernel reserved that reason code in TASK-114.)*
- [x] Each rule has a golden failing fixture *and* a golden negative fixture. *(Inline-fixture coverage in `tests/erc/test_sub_block_rules.py` — 10 tests, 2 per rule (fire + clean).)*
- [x] ERC catalogue documentation gains rows for the four rules. *(rules.json entries E11..E15 with full explanation/heuristic/source_of_truth fields per the catalog contract. The `.claude/skills/circuit/docs/erc-checks.md` prose update is deferred to TASK-133's final docs pass — the catalogue JSON is the source of truth.)*
- [x] No regression on existing ERC fixtures.

## Outcome

Added E11 (sub-block port not wired), E12 (sub-block declared but
never instantiated), E13 (refdes collision after flatten), E14
(instance port double-driven), and E15 (voltage-divider ambiguous).
E15 rides with this work because the kernel's TASK-114 detector
already reserved the reason code. Catalog entries with full
explanation/heuristic/source_of_truth fields land in `rules.json`.
281/281 host tests pass.

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
