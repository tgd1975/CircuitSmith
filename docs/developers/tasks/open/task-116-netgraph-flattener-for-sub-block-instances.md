---
id: TASK-116
title: Netgraph flattener for sub-block instances
status: open
opened: 2026-05-14
effort: Large (8-24h)
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

- [ ] Multi-instance RC pair YAML round-trips through netgraph → flat netlist → BOM → KiCad netlist.
- [ ] BOM groups by component class — `R_FILT_A` and `R_FILT_B` are siblings in BOM ordering.
- [ ] Existing flat-form fixtures still pass (coexistence guarantee from IDEA-008).
- [ ] All five fixture-matrix scenarios commit golden artefacts.

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
