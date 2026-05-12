---
id: EPIC-002
name: circuit-renderer-layout
title: Circuit Skill — Renderer and Layout Engine
status: open
opened: 2026-05-12
closed:
assigned:
branch: release/epic-002-circuit-renderer-layout
---

Seeded by IDEA-001 (Circuit-Skill — AI-Assisted Schematic Generation with ERC, BOM, and Netlist Export).

Phase 2 of IDEA-001, in two stages:

- **Phase 2a (kernel-only, v0.1)** — implement the YAML → SVG renderer, the
  shared `NetGraph` data model, the deterministic layout kernel with
  canonical-slot table, the Manhattan router, and the v0.1 structural
  rubric (`overlaps`, `labels_fit`, `wire_crossings`). Cut over the
  existing CI pipeline from the hand-coded generator to the new renderer
  in a single PR.
- **Phase 2b (AI placer, v1, contingent)** — add the AI placer, convergence
  loop, `--no-ai` fallback, and advisory-to-blocking rubric promotions.
  Opens only when Phase 2a accumulates concrete kernel-failure modes
  that a `§5.3` canonical-slot table addition cannot retire.

Companion design docs:
`docs/developers/ideas/archived/idea-001.yaml-format.md`,
`docs/developers/ideas/archived/idea-001.layout-engine-concept.md`,
`docs/developers/ideas/archived/idea-001.layout-engine-discussion.md`.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
