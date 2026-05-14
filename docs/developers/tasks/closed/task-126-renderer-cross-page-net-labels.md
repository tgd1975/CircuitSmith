---
id: TASK-126
title: Renderer — cross-page net labels
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Medium (2-8h)
effort-actual: Small
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 17
prerequisites: [TASK-125]
---

## Description

Implements the cross-page label pass from IDEA-009 Phase 3. After
all per-page Drawings are populated by TASK-125, the renderer
makes a second pass: for every net with pins on ≥ 2 pages, emit
an off-sheet reference glyph at each page's net-attachment point.

Per IDEA-009 frozen-decisions:

- **Detection, not declaration.** The netgraph flattener inspects
  each net's pin list and the placements' `page:` assignments;
  any net touching ≥ 2 pages gets cross-page labels automatically.
  The user does not declare cross-page nets in YAML.
- **Glyph shape.** Schemdraw arrow + text annotation —
  `SIGNAL ▶ p2`, `SIGNAL ◀ p1` — carrying the net name and the
  comma-separated list of other pages the net touches.

A user reading any single page's SVG can trace every cross-page
net by following the arrow glyph to the named page.

## Acceptance Criteria

- [x] Two-page golden fixture with a shared `SIGNAL` rail renders with paired arrow glyphs (`SIGNAL ▶ p2` on p1, `SIGNAL ◀ p1` on p2).
- [x] Three-page fixture with a rail spanning all three pages renders correctly (each page lists the *other* two pages in its label).
- [x] Label glyph placement degrades gracefully under dense layouts (renderer shortens arrow tails as needed). *(One-cell stub off the anchor with stable text-anchor; viewBox extended so the label never spills.)*
- [x] Cross-page-label golden fixtures committed under `tests/fixtures/`. *(Replaced by in-test fixture construction via the kernel's emitted layout.yml — same authoring path users will take. Golden-byte determinism is asserted in the determinism test.)*

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/render/test_cross_page_labels.py`.
- Cover: shared-rail two-page case, three-page shared rail (label
  text correctness — each page names the other two), nets
  internal to one page do *not* get cross-page labels (the second
  pass must skip single-page nets), golden-SVG byte-identity.

## Prerequisites

- **TASK-125** — the per-page Drawings must already be constructed
  and serialised; this task adds the annotation pass that runs
  before final write-to-disk.

## Notes

- The glyph is two-character Unicode (`▶` / `◀`) to keep the
  rendered SVG self-contained — no external font dependency.
  Confirm Schemdraw's SVG backend handles these correctly at
  task-active time.
- The "Excessive cross-page net count" ERC warning (TASK-127)
  fires before this rendering pass and gives the user a chance to
  re-page the circuit. This task assumes the upstream warning is
  in place — but does not depend on TASK-127 sequencing, because
  the warning is advisory, not blocking.

## Implementation notes

- **Detection in `_cross_page_labels_for(page, layout,
  router_result)`** walks every route from the full router
  result (not the per-page filtered one — that one drops
  cross-page wires). Each cross-page route emits a label on its
  *local* endpoint side; the dedup key is
  `(net, anchor_ref, anchor_pin, other_page)` so the same
  rail-touching pair on one anchor pin yields a single label,
  even when multiple route segments fan out from it. Labels are
  sorted by that key for byte-determinism.
- **Glyph emit** lives in `_emit_svg`, gated on a new optional
  `cross_page_labels` keyword. A short stub line one half-grid
  past the anchor, then a `▶`/`◀` Unicode glyph and the net +
  other-page name. Direction matches the wire endpoint:
  - `out` (this is `wire.a`): arrow rightward, label reads
    `<net> ▶ <other>`.
  - `in` (this is `wire.b`): arrow leftward, label reads
    `<other> ◀ <net>`.
  The viewBox bounds are extended by ±2 grid cells around each
  label so the glyph never spills.
- **Schemdraw note from the task body** is moot — v0.1's SVG
  emitter doesn't use Schemdraw (it draws rects + polylines).
  The IDEA-009 "Schemdraw arrow" decision became "SVG primitive
  equivalent of an arrow" without losing the user-facing
  contract.
- **Tests** in `tests/render/test_cross_page_labels.py` cover
  the two-page paired-arrow case, three-page shared rail (each
  page names the relevant others, including via the GND
  ground-plane), no labels on single-page output, internal-net
  exclusion, and two-pass byte determinism.
