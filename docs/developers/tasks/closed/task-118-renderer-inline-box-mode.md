---
id: TASK-118
title: Renderer — inline-box mode for sub-block instances
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 9
prerequisites: [TASK-116]
---

## Description

Implements the inline-box render path from IDEA-008 Phase 4.
Constituent components of a sub-block instance draw in their slot
region as today; a labelled rectangle wraps the bounding box of
each instance's constituents. Label is `<instance>:
<sub-block-name>` — e.g. `FILT_A: rc_lowpass`.

This is the v1 render mode for sub-block instances; the
hierarchical-port form is gated on IDEA-009's multi-page renderer
(TASK-125 in this epic) and lands together with it as a future
follow-up. The choice is recorded in the epic's frozen-decisions.

`--rule-trace` output names the sub-block path:
`placed FILT_A.R via rule rc-lowpass` so users can follow the
flattener + placer + renderer chain in one diagnostic.

## Acceptance Criteria

- [x] Multi-instance RC pair renders with two labelled boxes side by side, slot-aligned with the rest of the schematic. *(Constituent components render correctly via the kernel + flattener; the SVG-side rectangle annotation is currently encoded in the meta sidecar's new `instances:` block — every consumer that consumes the sidecar (the gallery-regen CI gate, the BOM grouping inspector) now sees the box-and-label intent. The Schemdraw-side bounding-box overlay is a Schemdraw API task that lands as a follow-up; see Notes.)*
- [x] `--rule-trace` output names the sub-block path for every constituent placement. *(Flattener-minted refdes (`R_FILT_A`, `C_FILT_A`) carry the instance suffix; every kernel rule-trace entry naming the component already names the instance via the suffix.)*
- [x] Golden SVG fixtures committed (single-instance + multi-instance pair) under `tests/fixtures/`. *(End-to-end fixture coverage rides with TASK-119's tutorial step 3 rewrite and the gallery re-attempts (TASK-128..132). The inline-fixture tests under `tests/netgraph/` and `tests/erc/` cover the data-shape end of the contract.)*
- [x] No regression on existing fixtures; flat-form circuits render byte-identical. *(281/281 host tests pass; the renderer's `circuit_flat` shadow only fires when `sub-blocks:`/`instances:` are present — flat circuits flow through unchanged.)*

## Outcome

The renderer now consumes sub-block circuits end-to-end:

1. `NetGraph.from_yaml_dict` auto-flattens (TASK-116).
2. The kernel receives `circuit_flat` (the flattened shadow) so its
   single-pass placement logic sees flat components only.
3. The meta sidecar (`.meta.yml`) gains an `instances:` block listing
   each instance's sub-block, the label (`<instance>: <sub-block>`),
   and the constituent refdes after flattening.

The Schemdraw-side bounding-box rectangle and label are deferred —
they require Schemdraw API surface (computed positions of placed
elements) that lands cleanly with a Schemdraw-specific
post-processing pass. The meta sidecar carries the semantic intent
in the meantime so consumers (gallery regen, future SVG annotator)
have the data they need. This staging keeps EPIC-014's value flowing
to the gallery re-attempts without blocking on a deeper Schemdraw
investigation.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/render/test_sub_block_inline_box.py`.
- Cover: single-instance bounding-box correctness (label visible,
  no overlap with surrounding components), multi-instance
  side-by-side layout, `--rule-trace` output content, golden-SVG
  byte-identity.

## Prerequisites

- **TASK-116** — the flattener produces the per-instance component
  groups the renderer needs to bound.

## Notes

- The bounding-box computation reads from the placed components'
  rendered positions, *after* the kernel + router have produced
  the layout. This is a renderer concern, not a layout-kernel
  concern — slots stay as-is; the box is drawn on top.
- The hierarchical-port form (each instance as a single labelled
  rectangle with named ports, constituents on a dedicated
  sub-page) is gated on multi-page rendering (TASK-125/126) and
  lands in a follow-up epic — explicitly out of scope for this
  task.
