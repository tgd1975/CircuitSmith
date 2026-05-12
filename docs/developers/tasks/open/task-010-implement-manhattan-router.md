---
id: TASK-010
title: Implement layout_engine/router.py — Manhattan router
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Senior
human-in-loop: No
epic: circuit-renderer-layout
order: 3
prerequisites: [TASK-009]
---

## Description

Implement `.claude/skills/circuit/layout_engine/router.py` — the
Manhattan router that turns placed components into wire geometry. Reads
the kernel's slot assignments plus the `NetGraph`, emits orthogonal
wire paths in the SVG coordinate system.

The router is deterministic and does not attempt global optimisation —
it routes each net in a fixed traversal order with simple
right-angle paths. Wire crossings are recorded in the rubric (TASK-011)
rather than avoided; v0.1 accepts crossings as long as the rubric stays
green.

## Acceptance Criteria

- [ ] `router.py` produces orthogonal-only wire paths (no diagonals).
- [ ] Two runs against the same kernel output produce byte-identical wire geometry.
- [ ] Wire crossings are detected and counted (consumed by TASK-011 rubric).
- [ ] No wire intersects a component body (only pin anchors).

## Test Plan

Add `tests/test_router.py` covering: orthogonality check on a minimal circuit, byte-identity across two runs, wire-crossing count matches the manually-counted expected number for the `full-pedal` fixture.

## Prerequisites

- **TASK-009** — `kernel.py` produces the slot assignments the router consumes.

## Notes

See `idea-001.layout-engine-concept.md §9` (router) and
`idea-001.layout-engine-discussion.md` for why a global optimiser is
deliberately rejected at v0.1.
