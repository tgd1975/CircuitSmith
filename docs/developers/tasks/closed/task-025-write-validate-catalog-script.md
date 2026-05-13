---
id: TASK-025
title: Write knowledge/validate_catalog.py
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: circuit-erc
order: 4
prerequisites: [TASK-024]
---

## Description

Author `.claude/skills/circuit/knowledge/validate_catalog.py` — the
CI-runnable validator for `rules.json`. Five checks:

1. **Format** — every entry has all six required fields populated;
   field types match the spec.
2. **`enforced_by` consistency** — every `enforced_by` value matches
   either a predicate name in `erc_engine.py`'s constant table or the
   literal string `schema` (for S4/S5).
3. **`source_of_truth` reachability** — every URL responds 2xx (with
   a configurable allowlist for known-flaky hosts).
4. **Precision disclaimer presence** — every `heuristic` field contains
   the configured disclaimer substring.
5. **`category`-invariant lint** — scan `erc_engine.py` (and any other
   module under `.claude/skills/circuit/` outside `layout_engine/`)
   for `category ==`, `category in`, `["category"]`, or `.category`
   comparisons. Fail if found. Rationale: the dossier's invariant
   ([idea-001.components.md §1](../../ideas/archived/idea-001.components.md#1-category--explicit-layout-engine-classification))
   is "category keys layout, not semantics" — any ERC predicate
   keying on `category` silently breaks the contract that lets a
   piezo buzzer ride on `category: resistor`. Today the rule is
   policed by prose; this lint makes it enforceable.

CI fails on any check failure. The script is CLI-invokable standalone
and importable from CI workflows.

## Acceptance Criteria

- [x] `validate_catalog.py` runs cleanly on the seeded `rules.json` from TASK-024.
- [x] Each of the five checks has a targeted failure fixture; deliberately breaking each one produces a clear error.
- [x] The `category`-invariant lint allows reads inside `layout_engine/` (the rule's intended scope) and flags reads anywhere else.
- [x] URL reachability check supports an env-var allowlist for offline CI runs (`CS_CATALOG_OFFLINE=1` skips URL checks).
- [x] CI integration: a new GitHub Actions step runs this validator and fails the build on errors. *(Wired in TASK-029.)*

## Test Plan

Add `tests/test_validate_catalog.py` covering: clean catalog passes, missing-field fixture fails check 1, unknown `enforced_by` fixture fails check 2, unreachable URL fixture fails check 3, heuristic without disclaimer fails check 4, deliberately-injected `if comp.category == "led"` snippet in `erc_engine.py` fails check 5.

## Prerequisites

- **TASK-024** — `rules.json` is the validator's input.

## Notes

URL reachability is the slowest check — cache results or skip in
fast-CI lanes. The default `CS_CATALOG_OFFLINE=0` (online) for nightly
runs; per-PR runs can skip.
