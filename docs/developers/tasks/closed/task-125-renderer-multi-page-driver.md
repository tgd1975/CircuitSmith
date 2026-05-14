---
id: TASK-125
title: Renderer — multi-page driver
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Large (8-24h)
effort-actual: Medium
complexity: Senior
human-in-loop: Support
epic: circuit-library-and-renderer-v2
order: 16
prerequisites: [TASK-124]
---

## Description

Implements the multi-page render driver from IDEA-009 Phase 3.
One Schemdraw `Drawing` per declared page; walks `pages:` in
declaration order, populates each from its placements, serialises
to `<stem>-p<n>.svg`.

CLI semantics for [`--out` in renderer.py:676](../../../src/circuitsmith/renderer.py):

- Single-page circuit (`pages:` absent or one page declared) →
  emit `<stem>.svg` (no `-p1` suffix, preserves v0.1 behaviour).
- Multi-page circuit (≥ 2 pages declared with placements on each)
  → emit one file per page: `<stem>-p1.svg`, `<stem>-p2.svg`, …
- Single sidecar `.layout.yml` and `.meta.yml` per circuit, not
  per page (these describe the whole circuit, not one sheet).

Schemdraw's `Drawing` is one figure; multi-page output is achieved
by constructing one `Drawing` per page and serialising each
independently. There is no built-in Schemdraw page-break primitive
to plumb through; the work is the multi-`Drawing` loop and the
auto-suffix logic.

Cross-page net labels are **not** rendered by this task — TASK-126
adds the second pass. This task delivers the per-page rendering
infrastructure with nets that span pages left bare; TASK-126 then
annotates the boundaries.

## Acceptance Criteria

- [x] Two-page golden fixture renders byte-identical across runs (deterministic per-page output).
- [x] Single-page fixtures emit `<stem>.svg` (no `-p1` suffix); v0.1 behaviour preserved.
- [x] Three-page fixture renders with shared rail across all pages (label rendering on TASK-126).
- [x] Two-page fixture with no cross-page nets (independent subsystems) renders.
- [x] CLI invocation guidance updated in renderer help text.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/render/test_multi_page_driver.py`.
- Cover: each fixture-matrix scenario from IDEA-009 Phase 3
  (single-page, two-page minimal, three-page with shared rail,
  two-page independent), CLI auto-suffix behaviour, layout.yml /
  meta.yml singleton output, golden-SVG byte-identity per page.

## Prerequisites

- **TASK-124** — `pages:` schema + Placement page propagation
  must exist for the renderer to consume.

## Sizing rationale

The driver intertwines per-page Drawing construction, slot-region
partitioning, and CLI auto-suffix logic. Splitting risks shipping
a half-state where the schema accepts `pages:` but the renderer
can't honour it, which breaks every existing single-page fixture
in CI. One larger PR keeps the change atomic.

## Notes

- The cross-page label work (TASK-126) is deliberately split off.
  Bare nets that span pages will look wrong in the rendered SVG
  until TASK-126 lands — that's acceptable for the intermediate
  state because the fixtures landing in *this* task are
  multi-page circuits with no cross-page nets (independent
  subsystems on each page, or rails that don't span pages).
- Schemdraw multi-figure was investigated up front: there's no
  built-in page-break, so the driver manages multiple Drawing
  instances. Don't try to plumb a hypothetical Schemdraw
  multi-page primitive — it doesn't exist.

## Implementation notes

- **Page partitioning in the renderer** lives in two small
  helpers: `_emit_pages_or_single` is the driver (decides
  single-vs-multi based on `LayoutResult.pages`); `_filter_to_page`
  builds a per-page LayoutResult + RouterResult, dropping
  cross-page wires whose two endpoint refs don't live on the same
  page. Each page reuses the existing `_emit_svg` — no SVG
  emission code duplication.
- **`RenderResult.svg_paths`** lists every SVG written, in
  declaration order. `RenderResult.svg_path` aliases the first
  entry for backwards compatibility (single-page callers
  unchanged).
- **Singleton sidecars**: `.layout.yml` and `.meta.yml` describe
  the whole circuit and are emitted once after the per-page
  loop. Per-page sidecars would split provenance and break the
  re-render staleness gate.
- **Cross-page wires are dropped (not labelled) here.** TASK-126
  is the second pass: it walks the filtered-out routes,
  identifies the page boundary each wire crosses, and draws a
  Schemdraw arrow + page-stub label on both sides. The
  intermediate state lands here because the schema-accepts-but-
  renderer-ignores split would block every single-page fixture
  in CI.
- **CLI help** for `--out` documents the auto-suffix. The
  single-vs-multi behaviour key on `len(declared_pages)` ≥ 2
  (so a one-page `pages:` block stays at `<stem>.svg`, matching
  the IDEA-009 frozen-decision row "single-page output keeps
  `main.svg`").
- **Tests**: `tests/render/test_multi_page_driver.py` covers the
  four fixture scenarios, the singleton-sidecar invariant, and
  determinism (two-pass byte-equality). The two/three-page
  layouts are constructed by augmenting the kernel's emitted
  layout.yml — exercising the same authoring path users will
  take.
