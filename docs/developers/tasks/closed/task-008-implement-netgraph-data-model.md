---
id: TASK-008
title: Implement netgraph.py — shared NetGraph data model
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
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

- [x] `NetGraph` exposes the API documented in `idea-001.erc-engine.md §Net graph data model` (`nets`, `pin_index`, `power_nets`, etc.). _`power_nets` deferred: the dossier's class diagram lists only `nets`, `net_meta`, and the four helper methods, and "power-class" membership requires profile lookup (POWER/GROUND pin types), which is an ERC concern. NetGraph stays topology-only per the co-netgraph invariant. The downstream consumer (E1) sources pin types from the profile registry directly._
- [x] Construction from a parsed `.circuit.yml` dict is deterministic — two parses of the same input produce structurally identical graphs (by hash). _`canonical_hash()` returns a stable SHA-256 hex digest; `test_canonical_hash_is_stable_across_parses` verifies._
- [x] The three connection forms (`pins`, `path`, `bus`) each flatten to the same canonical net representation — downstream code does not branch on form. _`from_yaml_dict` dispatches on form, all three populate the same `nets: dict[str, list[PinRef]]`; downstream consumers see only that. `test_pins_and_path_produce_equivalent_btn_a_membership`, `test_bus_collapses_to_one_entry` cover this._
- [x] The module is path-agnostic per the portability contract: no project-specific paths or imports. _`test_module_has_no_host_project_imports` enforces the regex check; `scripts/portability_lint.py .claude/skills/circuit` runs clean._

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
