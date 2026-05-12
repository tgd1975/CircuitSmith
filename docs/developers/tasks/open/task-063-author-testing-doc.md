---
id: TASK-063
title: Author docs/developers/TESTING.md describing test layers, conventions, and fixture layout
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: developer-docs-governance
order: 2
prerequisites: [TASK-047]
---

## Description

The senior-review pre-implementation audit surfaced a concrete gap:
[`pyproject.toml`](../../../../pyproject.toml) sets
`testpaths = ["scripts/tests"]`, but TASK-005, TASK-008, TASK-022,
TASK-050, TASK-052, TASK-053 all reference `tests/test_*.py` at repo
root or `.claude/skills/circuit/tests/…` — neither is configured or
scaffolded. A junior writing the first product-code test today will
have their test silently skipped by pytest.

This task decides the test layout, encodes it in
`docs/developers/TESTING.md`, and updates `pyproject.toml`'s
`testpaths` to match. Adjacent decision points to settle in the same
doc: pytest-style vs unittest-style (the existing
[`scripts/tests/`](../../../../scripts/tests/) uses `unittest.TestCase`;
the task plans say "pytest fixtures"), fixture-file location, golden-test
update policy, and the test-naming convention.

Model: AwesomeStudioPedal's
[`TESTING.md`](../../../../../AwesomeStudioPedal/docs/developers/TESTING.md)
(236 lines, three test layers: host unit / host integration / on-device).
CircuitSmith's analogous layers:

- **Pure unit** — pytest functions in `tests/unit/` against pure
  helpers (NetGraph construction, schema validation, ERC predicates).
- **Pipeline integration** — fixture-driven end-to-end through the
  YAML → schema → NetGraph → ERC → renderer pipeline using committed
  `.circuit.yml` fixtures.
- **Contract / golden** — boundary-import test (TASK-050), NetGraph
  golden hash (TASK-053), portability lint, schema-validation
  pre-commit hook self-tests.

## Acceptance Criteria

- [ ] `docs/developers/TESTING.md` exists and documents the three test layers above with one canonical example per layer.
- [ ] Test-layout decision is recorded: where do product-code tests live (`tests/` at repo root, `.claude/skills/circuit/tests/`, or both?), and where do fixtures live.
- [ ] `pyproject.toml` `testpaths` is updated to match the documented layout.
- [ ] Pytest-vs-unittest decision is recorded in the doc; if pytest is chosen, the migration path for existing `unittest.TestCase`-style files in `scripts/tests/` is named (rewrite, or coexist, or leave-as-is).
- [ ] "How to write a new test" section covers: a pure-unit example, a fixture-driven pipeline example, and how to update a golden hash (links to TASK-053 procedure).
- [ ] Coverage-tracking decision is recorded (whether `pytest-cov` is adopted now or deferred), with rationale.

## Test Plan

Verify by running `pytest` from repo root after the testpaths update —
the existing tests in `scripts/tests/` must still be picked up under
the new configuration. Add a single trivial smoke test at the new
documented location (`tests/test_smoke.py` or equivalent) and confirm
pytest picks it up too. Delete the smoke test before closing.

## Prerequisites

- **TASK-047** — pytest is configured; this task extends that configuration.

## Notes

The doc is **load-bearing** for TASK-005, TASK-008, TASK-022, TASK-050,
TASK-052, TASK-053 and every subsequent test-writing task. If those
tasks' test-plan sections name a file at a path the doc does not
sanction, the discrepancy must be reconciled before this task closes —
either by updating the task body or by updating the doc to accept the
already-planned location. Reconciliation choices land as ADR if
non-obvious.

## Sizing rationale

Medium because the doc is short but the decisions it codifies (test
layout, framework choice, coverage policy) ripple through every
subsequent test-writing task. The writing is fast; the deciding takes
the time.
