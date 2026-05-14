---
id: TASK-124
title: Schema + layout-engine — pages partition
status: open
opened: 2026-05-14
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Support
epic: circuit-library-and-renderer-v2
order: 15
prerequisites: [TASK-110]
---

## Description

Adds the `pages:` partition from IDEA-009 Half 2 to two places:

- **Schema**:
  [`src/circuitsmith/schema/layout.schema.json`](../../../src/circuitsmith/schema/layout.schema.json)
  (see `co-schema` reminder) gains a top-level `pages:` block
  (declarations) and a per-placement `page:` field. Schema
  rejects: a placement whose `page:` is not declared in `pages:`,
  a `pages:` block with duplicate names.
- **Layout engine**:
  [`src/circuitsmith/layout/kernel.py`](../../../src/circuitsmith/layout/kernel.py)
  carries the page assignment through `Placement` without using
  it for layout decisions — `page` is a rendering concern; slot
  assignment happens within a page's region/slot vocabulary as
  today. Per [ADR-0001](../adr/0001-slots-not-coordinates.md),
  pages are a *partition* of the slot vocabulary, not a
  replacement.

A `.layout.yml` without a `pages:` block continues to render as
today (one SVG, no `-p1` suffix). The `pages:` block is opt-in;
existing tutorial fixtures and gallery YAML continue to parse and
render byte-identical.

## Acceptance Criteria

- [ ] Schema accepts a `pages:` block with named pages and rejects the two named invariant violations.
- [ ] `Placement` carries the page assignment through layout output (the field appears in serialised `.layout.yml`).
- [ ] Existing fixtures with no `pages:` block validate byte-identical (coexistence guarantee).
- [ ] Schema docs section drafted (consumed by TASK-133 for final wording).

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/schema/test_pages_schema.py` and
  `tests/layout/test_page_propagation.py`.
- Cover: positive case (two pages, two placements, one per
  page), each rejection case independently, single-page
  coexistence (no `pages:` block → existing output preserved),
  page-assignment determinism (same input → same Placement.page).

## Prerequisites

- **TASK-110** — frozen decisions: `pages:` shape, page-as-partition (not slot-replacement).

## Notes

- This task is the foundation for TASK-125 (renderer driver) and
  TASK-126 (cross-page labels). Keep it tightly scoped — schema +
  Placement propagation only. Do **not** touch the renderer here;
  the schema landing without the renderer is a defensible
  intermediate state (the kernel produces page-annotated
  Placements, the renderer ignores them, output is unchanged from
  v0.1).
