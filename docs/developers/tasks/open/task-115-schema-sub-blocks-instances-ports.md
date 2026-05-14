---
id: TASK-115
title: Schema extension — sub-blocks, instances, ports
status: open
opened: 2026-05-14
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Support
epic: circuit-library-and-renderer-v2
order: 6
prerequisites: [TASK-110]
---

## Description

Adds the first-class sub-block syntax from IDEA-008 Half 2 to
[`src/circuitsmith/schema/circuit.schema.json`](../../../src/circuitsmith/schema/circuit.schema.json)
(see `co-schema` reminder). Two new top-level blocks:

- `sub-blocks:` — definition map. Each entry has `components:`,
  `ports:` (named map per IDEA-008 *Open questions* — e.g.
  `ports: { signal_in: R.1, signal_out: R.2, gnd: C.2 }`), and
  `connections:` (reusing the top-level grammar verbatim).
- `instances:` — instantiation map. Each entry has `sub-block:
  <name>`. Top-level `connections:` reference instance ports as
  `<instance>.<port>` (e.g. `FILT_A.signal_in`).

Schema invariants enforced:

- A `sub-blocks` definition whose `components.*.type` references
  another sub-block name is rejected (nested sub-blocks disallowed
  in v1).
- An `instances` entry referencing an undeclared sub-block is
  rejected.
- A top-level `connections` entry referencing
  `<instance>.<undeclared-port>` is rejected.

The flat-YAML form keeps working unchanged — sub-block syntax is
opt-in. Existing tutorial fixtures and gallery YAML continue to
parse byte-identical.

## Acceptance Criteria

- [ ] Schema accepts a worked RC-pair example (`sub-blocks.rc_lowpass:` with two `instances:` and shared inputs).
- [ ] Schema rejects: nested-sub-block reference, undeclared sub-block instance, undeclared port reference.
- [ ] Every existing fixture in `tests/fixtures/` still validates.
- [ ] Schema docs section drafted (consumed by TASK-119 for final wording).

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/schema/test_sub_blocks_schema.py`.
- Cover: positive case (single sub-block, multi-instance), each
  rejection case independently, mixed flat + sub-block YAML in one
  circuit (a sub-block instance side by side with flat
  components).

## Prerequisites

- **TASK-110** — frozen decisions: named-ports map (not
  `inputs:`/`outputs:`), nested-sub-blocks-disallowed, reuse
  top-level `connections:` grammar.

## Notes

- Schema rejection messages must name the offending sub-block /
  instance / port — the IDEA-008 plan calls this out for the
  nested-sub-block case specifically, but it applies to all three
  rejections.
- The schema is the contract; the flattener (TASK-116) is the
  enforcer downstream. Splitting them across two tasks lets the
  schema land independently and gives a clean acceptance gate.
