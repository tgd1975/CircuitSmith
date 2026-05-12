---
id: TASK-052
title: Schema-validation pre-commit hook for .circuit.yml
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: architecture-fitness-functions
order: 6
prerequisites: [TASK-005, TASK-046]
---

## Description

Extend the existing pre-commit framework
([`scripts/pre-commit`](../../../../scripts/pre-commit)) to validate
every staged `.circuit.yml` against
`.claude/skills/circuit/schema/circuit.schema.json` before the commit
lands.

Today the architecture relies on the renderer to reject malformed
circuits — that is too late. A schema-non-conforming `.circuit.yml` can
be committed and only fails when someone runs the pipeline. Catching
it at staging time is one `jsonschema.validate(...)` call per staged
file.

The hook iterates over staged `.circuit.yml` paths, loads each with
`ruamel.yaml`, validates against the schema, and rejects the commit on
any failure with a structured error: file, JSON pointer, human message.

The same check runs in CI on PRs (in case a contributor bypasses the
local hook via `--no-verify` or works on a machine where hooks are not
installed).

## Acceptance Criteria

- [ ] `scripts/pre-commit` (or a sibling script it calls) validates every staged `.circuit.yml` against `circuit.schema.json`.
- [ ] Validation failure prints `<file>:<json-pointer>: <message>` and the commit is rejected.
- [ ] Pre-commit succeeds with no output when no `.circuit.yml` files are staged.
- [ ] The same validation runs in CI on PRs (TASK-048's workflow).
- [ ] Self-test fixture: `tests/test_schema_pre_commit.py` feeds a deliberately-invalid `.circuit.yml` to the hook function and asserts rejection.

## Test Plan

Unit-test the validator function (separate from the hook wrapper) with
two fixtures: `tests/fixtures/circuit-valid.yml` and
`tests/fixtures/circuit-invalid.yml`. The hook wrapper itself is
covered by an integration test that stages a fixture file via a
throwaway repo and asserts the hook exits non-zero.

## Prerequisites

- **TASK-005** — `circuit.schema.json` is the schema being validated against.
- **TASK-046** — `jsonschema` is declared in `pyproject.toml` so the hook has its dependency.

## Notes

This complements the renderer's own schema check (TASK-012) — they
catch the same class of error at two different points. The pre-commit
check is the early, cheap one; the renderer's check is the
defence-in-depth fallback for code paths that did not go through a
commit (e.g. ad-hoc renderer invocations during development).
