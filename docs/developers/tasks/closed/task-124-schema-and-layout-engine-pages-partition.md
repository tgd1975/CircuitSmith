---
id: TASK-124
title: Schema + layout-engine — pages partition
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Medium (2-8h)
effort-actual: Small
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

- [x] Schema accepts a `pages:` block with named pages and rejects the two named invariant violations.
- [x] `Placement` carries the page assignment through layout output (the field appears in serialised `.layout.yml`).
- [x] Existing fixtures with no `pages:` block validate byte-identical (coexistence guarantee).
- [x] Schema docs section drafted (consumed by TASK-133 for final wording).

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

## Implementation notes

- **Schema additions**: top-level `pages:` array (each entry
  `{name, title?}`) plus a per-placement `page:` field with the
  same pattern as the placement key. Cross-checks
  (`layout-pages-duplicate-name`, `layout-page-undeclared`) live
  in [`layout_validator.py`](../../../src/circuitsmith/schema/layout_validator.py)
  rather than in JSON Schema — JSON Schema can't enforce
  derived-key uniqueness cleanly.
- **`Placement.page` round-trip**: `Placement` gains an optional
  `page: str | None` field; `LayoutResult` carries `pages:
  list[dict]`. `_parse_previous_placements`,
  `_parse_previous_pages`, `_attach_fingerprint`, and the
  attached-to-anchor branch all preserve it. Crucially, page
  survives a topology-fingerprint mismatch — the fingerprint
  mechanism controls *slot* re-classification, but pages are
  user-authored rendering metadata and must survive the re-run.
  A final preserve-page pass on the new-refs branch handles this.
- **Anchor-page inheritance**: when the kernel rewrites an
  attached-to placement to inherit the anchor's region (line
  ~222), it also inherits the anchor's `page`. A current-limit
  resistor never splits from its LED across pages; a base-drive
  resistor never splits from its BJT. The user can override by
  setting `page:` on the attached entry in the previous
  `.layout.yml`.
- **Byte-identical coexistence**: `render_layout_yaml` emits
  `pages:` only when `result.pages` is non-empty, and emits the
  per-placement `page:` field only when `placement.page is not
  None`. A circuit re-rendered without a `pages:` declaration
  produces identical output to v0.1.
- **Docs**: [`layout.md`](../../../.claude/skills/circuit/docs/layout.md)
  gains a "Pages partition (multi-page layouts)" section,
  marked as TASK-125/126/127's consumer. TASK-133 will edit for
  final tone.
- **Tests**: 7 schema tests in
  [`tests/schema/test_pages_schema.py`](../../../tests/schema/test_pages_schema.py)
  (positive, two rejection cases, empty-list rejection, pattern
  rejection on both `pages.name` and `placement.page`,
  coexistence). 4 layout tests in
  [`tests/layout/test_page_propagation.py`](../../../tests/layout/test_page_propagation.py)
  (coexistence, round-trip, determinism, anchor-page
  inheritance).
