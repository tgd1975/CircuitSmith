---
id: TASK-118
title: Renderer — inline-box mode for sub-block instances
status: open
opened: 2026-05-14
effort: Medium (2-8h)
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

- [ ] Multi-instance RC pair renders with two labelled boxes side by side, slot-aligned with the rest of the schematic.
- [ ] `--rule-trace` output names the sub-block path for every constituent placement.
- [ ] Golden SVG fixtures committed (single-instance + multi-instance pair) under `tests/fixtures/`.
- [ ] No regression on existing fixtures; flat-form circuits render byte-identical.

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
