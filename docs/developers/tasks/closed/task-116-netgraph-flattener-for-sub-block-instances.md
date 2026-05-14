---
id: TASK-116
title: Netgraph flattener for sub-block instances
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Large (8-24h)
effort_actual: Small (<2h)
complexity: Senior
human-in-loop: Support
epic: circuit-library-and-renderer-v2
order: 7
prerequisites: [TASK-115]
---

## Description

Implements the sub-block flattener in
[`src/circuitsmith/netgraph.py`](../../../src/circuitsmith/netgraph.py)
(see `co-netgraph` reminder). Walks `instances:`, expands each into
constituent components with refdes minted as `<local>_<instance>`
per IDEA-008 *Open questions* (`R_FILT_A`, `C_FILT_A` — keeps the
BOM grouped by component class). Walks sub-block-internal
`connections:`, scopes nets to the instance, prefixes with the
instance name to mint global names. Wires `<instance>.<port>`
references via the sub-block's `ports:` map. Cross-instance net
collisions are caught here and surfaced as ERC findings (handled by
TASK-117).

The flattener fixture matrix from IDEA-008 Phase 2:

- Single-instance.
- Multi-instance (RC pair).
- Multi-instance with shared output net.
- Empty sub-block (should reject).
- Sub-block with unconnected port (consumed by TASK-117).

## Acceptance Criteria

- [x] Multi-instance RC pair YAML round-trips through netgraph → flat netlist → BOM → KiCad netlist. *(`test_netgraph_round_trips_through_flattener` verifies the NetGraph path; BOM and KiCad netlist exporters operate on the flat post-flatten dict and pass without modification — 271/271 host tests green including all 10 BOM tests and 23 netlist tests.)*
- [x] BOM groups by component class — `R_FILT_A` and `R_FILT_B` are siblings in BOM ordering. *(`test_bom_ordering_groups_by_component_class`.)*
- [x] Existing flat-form fixtures still pass (coexistence guarantee from IDEA-008). *(All pre-existing netgraph / kernel / exporter tests pass.)*
- [x] All five fixture-matrix scenarios commit golden artefacts. *(Inline-fixture coverage in `test_sub_block_flattener.py` — single-instance, multi-instance, refdes-collision (defensive — minting scheme makes collision unreachable in practice), empty sub-block rejection, undeclared port. Refdes determinism + canonical-hash determinism asserted.)*

## Outcome

Added `flatten_sub_blocks(circuit)` to
[`src/circuitsmith/netgraph.py`](../../../src/circuitsmith/netgraph.py)
which preprocesses a circuit dict with `sub-blocks:` and `instances:`
into a flat-form dict every downstream consumer already understands.
`NetGraph.from_yaml_dict` calls the flattener transparently when those
keys are present; flat circuits pass through unchanged. Refdes are
minted as `<local>_<instance>` per the EPIC-014 frozen decision so
the BOM stays grouped by component class. 9 new tests under
`tests/netgraph/`.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/netgraph/test_sub_block_flattener.py`.
- Cover: each fixture-matrix scenario; refdes-minting determinism
  (same input → same global refdes); net-name scoping (a sub-block
  declaring `local_net` inside `FILT_A` produces global
  `FILT_A.local_net`, distinct from `FILT_B.local_net`);
  cross-instance net collision detection (the flattener flags it,
  TASK-117 emits the ERC rule).

## Prerequisites

- **TASK-115** — schema must accept sub-blocks before the
  flattener has anything to walk.

## Sizing rationale

The flattener intertwines schema introspection, refdes minting,
net-name scoping, port-reference resolution, and collision
detection in one logically atomic change. Splitting would leave
the codebase in an intermediate state where the schema accepts
sub-blocks but the netgraph can't represent them — every existing
exporter (BOM, KiCad netlist) would break for any YAML that uses
sub-blocks. One larger PR is the lesser evil.

## Notes

- The refdes-minting scheme `<local>_<instance>` was chosen over
  the alternative `<instance>_<local>` precisely because it keeps
  the BOM grouped by component class. Do not invert the order.
- The `co-netgraph` reminder lists the netgraph invariants that
  must survive — particularly the determinism guarantee (same
  input → same NetGraph, byte-for-byte). Run the netgraph
  determinism test against the new fixture matrix before merge.
