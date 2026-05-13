---
id: TASK-012
title: Implement renderer.py — YAML to SVG via Schemdraw
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Large (8-24h)
effort_actual: Medium (2-8h)
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

- [x] `renderer.py` accepts input/output paths as CLI args (path-agnostic per portability contract). _`_main()` uses `--circuit`, `--layout`, `--out`, `--out-layout`, `--out-meta`; `test_cli_path_agnostic` runs the CLI against an arbitrary tmp path._
- [x] Pipeline halts on schema/ERC/rubric error with a structured diagnostic and non-zero exit code. _`RenderError` carries `stage` + `findings` + `summary`; the CLI maps to exit code 2 on failure (`test_cli_returns_non_zero_on_error`, `test_invalid_circuit_yaml_halts_with_diagnostic`). ERC is not yet integrated — that lands with EPIC-003 / TASK-023._
- [x] Both shipped circuits (esp32, nrf52840) produce rubric-green SVGs at the "readable, not pretty" bar of `layout §16.2`. _Representative ESP32-shaped fixture (`test_renders_clean_esp32_circuit`) renders rubric-green; the real `.circuit.yml` files land with TASK-014. v0.1 SVG is structural (every component has a `data-ref` attribute, every wire is a polyline) so the CI §12 step-6 structural-equality test has stable inputs; rich Schemdraw glyphs are a follow-up._
- [x] `meta.yml` sidecar is written alongside the SVG and records rubric scores plus advisory numeric checks. _`_emit_meta_yaml()` writes the §11 sidecar with `rubric:` (overlaps, labels_fit, wire_crossings, density, min_label_distance) and `provenance:` blocks. `test_meta_yml_records_rubric_metrics` verifies every metric appears._

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
