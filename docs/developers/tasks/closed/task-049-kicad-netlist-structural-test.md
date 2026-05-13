---
id: TASK-049
title: Structural test for KiCad netlist output (S-expression grammar)
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: circuit-exporters
order: 6
prerequisites: [TASK-033]
---

## Description

TASK-034 is a manual KiCad GUI spot-check on a single target. It catches
import-time warnings but does not catch (a) malformed S-expressions that
KiCad happens to tolerate, (b) tstamp non-uniqueness, (c) drift between
the generated `.net` and the source `NetGraph`. Those are what this task
covers, automatically.

Add `tests/test_netlist_structure.py` (host) that parses every committed
`.net` with a real S-expression parser (`sexpdata` or equivalent — choose
something already on PyPI rather than rolling our own) and asserts:

1. The top-level form is `(export ...)` with the expected `version` and `source` fields.
2. Every `(comp ...)` block has `ref`, `value`, `footprint`, and `tstamp` children. `tstamp` values are unique across all components.
3. Every `(net ...)` block has a unique `code` integer and a unique `name` string. Net `name` matches the source `.circuit.yml` net name (or the content-addressed form for path-segment nets per yaml-format §Form 2).
4. The set of `(comp ref ...)` references equals the set of components in the source `.circuit.yml`'s `components:` block (no extras, no missing).
5. Round-trip: re-serialise the parsed tree and re-parse it — the second parse must equal the first by structural equality.

Run against both shipped targets (esp32, nrf52840) and against any
fixture circuits added by EPIC-002 (TASK-014's `.circuit.yml` pairs).
The test is parametrised over the netlist files committed under
`docs/builders/wiring/<target>/main-circuit.net`.

This task is the regression guard TASK-034 cannot be — KiCad imports
do not run in CI; this parser-level test does.

## Acceptance Criteria

- [x] `tests/test_netlist_structure.py` exists and asserts the five properties above.
- [x] Test is parametrised over all committed `.net` files (discovered, not hard-coded).
- [x] Test fails loudly when fed a deliberately-mangled netlist (mutation test in the test file: a fixture with a duplicate tstamp asserts the test catches it).
- [x] CI runs this test in TASK-048's workflow.

## Test Plan

Mutation testing: ship one `.net` fixture with a duplicated `tstamp` and one with a missing `(comp ref ...)` and confirm both fail the test for the right reason. Keep these as `tests/fixtures/malformed-*.net`.

## Prerequisites

- **TASK-033** — the netlist exporter must produce `.net` files for the test to consume.

## Notes

S-expression grammar parity with KiCad is the contract this test enforces. The KiCad grammar itself is documented in the KiCad `eeschema_legacy.cpp` source and the `Schematic.NetClasses` reference; if a future KiCad version changes the grammar, this test is where the breakage surfaces first.
