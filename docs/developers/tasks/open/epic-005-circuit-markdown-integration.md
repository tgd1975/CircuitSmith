---
id: EPIC-005
name: circuit-markdown-integration
title: Circuit Skill — Markdown Block Integration
status: open
opened: 2026-05-12
closed:
assigned:
branch: feature/circuit-markdown-integration
---

Seeded by IDEA-001 (Circuit-Skill — AI-Assisted Schematic Generation with ERC, BOM, and Netlist Export).

Phase 5 of IDEA-001. Wires ` ```circuit ` Markdown blocks into the
build pipeline so a `.circuit.yml` snippet inside a doc page renders to
an embedded SVG with hash-based staleness detection.

**Ordering with IDEA-022 (MkDocs site).** If IDEA-022 has landed when
this epic opens, the block is implemented as a `pymdownx.superfences`
custom formatter directly. If this epic ships first, a GitHub Actions
workflow (`generate-circuits.yml`) rewrites blocks to image embeds at
CI time; the workflow retires when IDEA-022 lands.

**Predecessor source.**
[IDEA-022 (MkDocs site)](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-022-mkdocs-documentation-site.md)
is an AwesomeStudioPedal idea — its landing status is tracked there, not here.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
