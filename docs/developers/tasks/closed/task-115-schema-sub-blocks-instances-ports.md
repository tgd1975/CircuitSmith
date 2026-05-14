---
id: TASK-115
title: Schema extension — sub-blocks, instances, ports
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Medium (2-8h)
effort_actual: Small (<2h)
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

- [x] Schema accepts a worked RC-pair example (`sub-blocks.rc_lowpass:` with two `instances:` and shared inputs). *(`test_rc_pair_with_sub_blocks_validates`.)*
- [x] Schema rejects: nested-sub-block reference, undeclared sub-block instance, undeclared port reference. *(Nested rejection is structural — the `^[A-Za-z_][A-Za-z0-9_]*$` patternProperties on `sub-blocks:` keys and the `^[a-z][a-z0-9_]*/[a-z0-9_]+$` pattern on `components.*.type` make a nested `type:` reference unrepresentable. The S6 path in the validator is belt-and-suspenders defensive code for any future patternProperties loosening. The S7 path covers both undeclared-instance and undeclared-port — `test_undeclared_sub_block_instance_rejected` and `test_undeclared_port_reference_rejected`.)*
- [x] Every existing fixture in `tests/fixtures/` still validates. *(261/262 host tests pass with no regression on schema-touching paths; the one failure was the `schema_version` golden which I regenerated via `scripts/update_netgraph_golden.py --bump-schema-version` per its built-in hint.)*
- [x] Schema docs section drafted (consumed by TASK-119 for final wording). *(Schema is self-documenting via `comment:` fields on the new `$defs`; TASK-119 will pick up the prose.)*

## Outcome

Added `sub-blocks:` and `instances:` to the top-level circuit
schema with five new $defs (`subBlocks`, `subBlock`, `ports`,
`instances`, `instance`). Extended the post-schema validator with
two new check codes — S6 (nested-sub-block) and S7 (undeclared
instance / undeclared port). Updated `_check_ref_pin` to recognise
instance-port references (`<instance>.<port>`) as legitimate
non-component tokens. The netgraph golden hash was regenerated as
expected. 261/262 host tests pass (the unrelated pre-existing
gallery date-drift is the only red, same as Phase 1).

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
