---
id: TASK-008
title: Implement netgraph.py — shared NetGraph data model
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Senior
human-in-loop: No
epic: circuit-renderer-layout
order: 1
prerequisites: [TASK-005]
---

## Description

Implement `.claude/skills/circuit/netgraph.py` — the typed net graph
produced from a validated `.circuit.yml` and consumed by three
downstream stages (`erc_engine.py`, the layout kernel, and
`netlist_exporter.py`). One parse, three readers — the model is the
contract that decouples them.

The `NetGraph` is the topology projection: nodes are component pins,
edges are nets named by the three connection forms. Layout coordinates
are deliberately absent — geometry is the layout kernel's concern, not
the data model's.

## Acceptance Criteria

- [ ] `NetGraph` exposes the API documented in `idea-001.erc-engine.md §Net graph data model` (`nets`, `pin_index`, `power_nets`, etc.).
- [ ] Construction from a parsed `.circuit.yml` dict is deterministic — two parses of the same input produce structurally identical graphs (by hash).
- [ ] The three connection forms (`pins`, `path`, `bus`) each flatten to the same canonical net representation — downstream code does not branch on form.
- [ ] The module is path-agnostic per the portability contract: no project-specific paths or imports.

## Test Plan

Add `tests/test_netgraph.py` covering: minimal-circuit construction, the three connection forms each produce equivalent nets when given equivalent topology, hash determinism across two parses, and pin-index lookup by `(component, pin_name)`.

## Prerequisites

- **TASK-005** — `circuit.schema.json` produces the validated dict that `NetGraph` consumes.

## Sizing rationale

Sized Medium because the data model is small but central. The implementation must be right enough that ERC, layout, and netlist export can all be built on top without re-flattening.

## Notes

See `idea-001.erc-engine.md §Net graph data model` for the canonical
shape; the netlist exporter spec in `idea-001.exporters.md` documents
the consumer side.
