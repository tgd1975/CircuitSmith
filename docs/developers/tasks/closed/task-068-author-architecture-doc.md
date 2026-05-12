---
id: TASK-068
title: Author docs/developers/ARCHITECTURE.md as the explicit top-down architecture page
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: developer-docs-governance
order: 7
prerequisites: [TASK-054]
---

## Description

CircuitSmith's architecture lives in two places today:
[`README.md`](../../../../README.md) (overview, pipeline ASCII, target
directory tree) and the [IDEA-001 dossier's nine files](../../ideas/archived/)
(authoritative depth). Neither is an explicit "this is the
architecture" page — the README is a marketing-tier overview that
mentions architecture in passing, the dossier is research-tier depth
spread across files designed to be read together. A new contributor
who wants the *one-page* architectural view has nowhere to go.

This task creates that page: a deliberately top-down doc that names
the modules, the data flow, the decoupling boundaries, and the
load-bearing properties (AI containment, exporter decoupling, the
NetGraph as shared contract, the skill-directory as the library). The
doc links *out* to the ADRs for the decisions and to the dossier for
the depth — it does not duplicate them.

Model: AwesomeStudioPedal's
[`ARCHITECTURE.md`](../../../../../AwesomeStudioPedal/docs/developers/ARCHITECTURE.md)
(163 lines, mermaid class diagrams, component table, hardware seam
description). CircuitSmith's version uses mermaid for the pipeline and
the module-boundary graph; the component table maps modules to their
ADR.

## Acceptance Criteria

- [x] `docs/developers/ARCHITECTURE.md` exists and is linked from `README.md`'s architecture section (which is repointed to be a summary that defers to this doc for the depth).
- [x] A mermaid flowchart shows the pipeline (YAML → schema → NetGraph → ERC → layout → render → exporters) with one-line annotations per stage.
- [x] A mermaid graph shows the module-boundary structure: `renderer`, `netgraph`, `erc_engine`, `bom_exporter`, `netlist_exporter`, `layout_engine/{kernel,router,ai_placer}`, `schema/`, `components/`, `knowledge/` — with the three forbidden edges (TASK-050) marked as red dashed lines.
- [x] A component table names each module, its file path under `.claude/skills/circuit/`, the ADR(s) that govern it, the code-owner skill (if any), and one-line responsibility.
- [x] Decoupling section names the four load-bearing seams: NetGraph contract (ADR-0003), exporter decoupling (ADR-0004), ERC pre-layout (ADR-0005), skill-directory portability (ADR-0007). Each links to its ADR.
- [x] AI-containment property is documented: where AI runs (authoring time only, layout placer), where it does *not* run (runtime hardware rules — see ADR-0006).
- [x] The doc closes with a "where to go next" map: ADR index for decisions, dossier index for depth, code-owner skills for the per-file invariants.

## Test Plan

No automated tests. Manual: walk a hypothetical new contributor
through the doc and verify they can answer five questions without
external context — (1) what does this project produce, (2) what are
the named subsystems, (3) which subsystem owns which file, (4) which
edges are forbidden, (5) where do I read deeper.

## Prerequisites

- **TASK-054** — ADRs 0001–0008 exist and are linkable.

## Notes

This is the most-linked doc in the developer-docs set — every other
TASK-062..072 doc references it. Treat it as a hub, not a destination:
short, navigable, link-heavy. Aim for ~200 lines.

Mermaid diagrams should follow the MERMAID_STYLE_GUIDE conventions
(TASK-069). The two tasks are paired: ARCHITECTURE.md is the first
consumer of the style guide, and its diagrams are the reference
examples the style guide cites.

The README's existing architecture section is **summarised down**, not
duplicated — the README owns the "what is CircuitSmith" framing,
ARCHITECTURE.md owns the "how is it structured" depth.

## Sizing rationale

Medium because the writing itself is ~3h, but the diagram design (two
mermaid graphs + a component table) and the cross-referencing audit
(every ADR / dossier link verified) add a structured ~3h.
