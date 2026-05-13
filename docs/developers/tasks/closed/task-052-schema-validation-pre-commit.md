---
id: TASK-052
title: Schema-validation pre-commit hook for .circuit.yml
status: closed
closed: 2026-05-13
opened: 2026-05-12
effort: Small (<2h)
effort_actual: Small (<2h)
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

- [x] `scripts/pre-commit` (or a sibling script it calls) validates every staged `.circuit.yml` against `circuit.schema.json`.
- [x] Validation failure prints `<file>:<json-pointer>: <message>` and the commit is rejected.
- [x] Pre-commit succeeds with no output when no `.circuit.yml` files are staged.
- [x] The same validation runs in CI on PRs (TASK-048's workflow).
- [x] Self-test fixture: `tests/test_schema_pre_commit.py` feeds a deliberately-invalid `.circuit.yml` to the hook function and asserts rejection.

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

## Resolution

`scripts/check_circuit_schema.py` is the gate. Three modes:

- **Default (staged)** — reads `git diff --cached` for `*.circuit.yml`
  paths and validates each via `circuitsmith.schema.validate_file`.
  This is the pre-commit-hook code path.
- **Positional args** — explicit paths win over staged detection.
  Used by the test fixtures and by ad-hoc local invocations.
- **`--all`** — validates every committed `*.circuit.yml` under
  `data/` and `tests/fixtures/`. This is the CI code path: catches the
  case where the local hook was bypassed with `--no-verify` or run on
  a machine where hooks are not installed.

Wiring:

- `scripts/pre-commit` calls the script when any `.circuit.yml` is
  staged. The `CS_PYTHON` venv-or-system selector was promoted to the
  top of the hook so the schema gate (which depends on the
  `circuitsmith` package on `sys.path`) uses the same interpreter as
  the ERC and exporter gates further down.
- `.github/workflows/ci.yml` runs `python scripts/check_circuit_schema.py
  --all` as a step after `pytest`.
- `tests/test_schema_pre_commit.py` exercises valid / invalid /
  `--all` / explicit-paths / staged-detection paths. Fixtures live
  under `tests/fixtures/schema_check/`.
