---
id: TASK-012
title: Implement renderer.py — YAML to SVG via Schemdraw
status: open
opened: 2026-05-12
effort: Large (8-24h)
complexity: Senior
human-in-loop: No
epic: circuit-renderer-layout
order: 5
prerequisites: [TASK-011, TASK-008]
---

## Autonomy

`Clarification` → `No` per TASK-060 sweep. Renderer style choices
are visually checkable in the SVG output; file an ADR for any
non-default that affects the public output contract.

## Description

Implement `.claude/skills/circuit/renderer.py` — the top-level entry
point that orchestrates the full pipeline:

1. Parse `.circuit.yml`.
2. Schema-validate (TASK-005).
3. Build `NetGraph` (TASK-008).
4. Run kernel (TASK-009) → produce/consume `layout.yml`.
5. Run router (TASK-010).
6. Evaluate rubric (TASK-011).
7. Emit SVG via Schemdraw.
8. Write `meta.yml` sidecar.

Renderer dispatches across the three connection forms — `pins` →
ground/power-symbol strategy, `path` → inline-chain strategy, `bus` →
backbone-and-stubs strategy. Each strategy is a separate function;
adding a new connection form is adding a new strategy, not modifying
existing ones.

## Acceptance Criteria

- [ ] `renderer.py` accepts input/output paths as CLI args (path-agnostic per portability contract).
- [ ] Pipeline halts on schema/ERC/rubric error with a structured diagnostic and non-zero exit code.
- [ ] Both shipped circuits (esp32, nrf52840) produce rubric-green SVGs at the "readable, not pretty" bar of `layout §16.2`.
- [ ] `meta.yml` sidecar is written alongside the SVG and records rubric scores plus advisory numeric checks.

## Test Plan

Add `tests/test_renderer.py` covering: full-pipeline run on both shipped `.circuit.yml` files produces matching `full-pedal` fixture SVGs (XML element count + `data-ref` attribute comparison, not pixel diff). End-to-end smoke test via CLI invocation.

## Prerequisites

- **TASK-008** — `NetGraph` is the renderer's internal data model.
- **TASK-011** — rubric gates SVG emission.

## Sizing rationale

Sized Large because it is the integration point. Splitting "parse + dispatch" from "SVG emission" produces a renderer that doesn't render — not a shippable intermediate.

## Notes

See `idea-001.yaml-format.md` for the three connection-form
strategies; `idea-001.layout-engine-concept.md §11` for the `meta.yml`
sidecar format.
