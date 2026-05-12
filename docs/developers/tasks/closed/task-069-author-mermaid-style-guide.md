---
id: TASK-069
title: Author docs/developers/MERMAID_STYLE_GUIDE.md (diagram types, palette, edge conventions)
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: developer-docs-governance
order: 8
prerequisites: [TASK-068]
---

## Description

CircuitSmith's developer docs will accumulate mermaid diagrams as
ARCHITECTURE.md (TASK-068) lands and as subsequent epics document their
own module structures. Without a style guide, every author picks their
own diagram type, color, and edge convention, and the doc set drifts
into visual incoherence. Worth one doc up front.

Model: AwesomeStudioPedal's
[`MERMAID_STYLE_GUIDE.md`](../../../../../AwesomeStudioPedal/docs/developers/MERMAID_STYLE_GUIDE.md)
(229 lines, covers flowchart / sequence / class / state diagrams with
canonical examples). CircuitSmith's version is shorter (~120 lines)
because the project's diagram needs are simpler — primarily flowcharts
for pipelines and graphs for module boundaries, with occasional
sequence diagrams for hook flows.

## Acceptance Criteria

- [x] `docs/developers/MERMAID_STYLE_GUIDE.md` exists.
- [x] Diagram-type selector: a decision table mapping "I want to show X" to "use diagram type Y" (data flow → flowchart LR, module boundaries → graph, runtime sequence → sequenceDiagram, lifecycle states → stateDiagram-v2).
- [x] Palette: defined color codes for: data nodes, process nodes, output nodes, forbidden edges, conditional edges, deprecated nodes. Hex codes named, with the rationale per choice.
- [x] Edge conventions: solid for data flow, dashed for "via", dotted for optional, red for forbidden, bold for primary path.
- [x] Node-label conventions: nouns for data, verbs for process, ALL-CAPS for top-level subsystems.
- [x] Cross-reference: the first ARCHITECTURE.md diagrams (TASK-068) are cited as the reference example for each diagram type.
- [x] Accessibility note: every mermaid block includes a paragraph of prose summary above or below for screen-readers (mermaid is not natively screen-reader-friendly).

## Test Plan

No automated tests. Manual: each diagram in ARCHITECTURE.md is
re-checked against the style guide; deviations are fixed in
ARCHITECTURE.md or the rule is generalised in the style guide,
whichever is more defensible.

## Prerequisites

- **TASK-068** — ARCHITECTURE.md is the first consumer; its diagrams
  are the reference examples this guide cites. The two tasks land
  in this order so the style guide is informed by real
  diagram needs, not imagined ones.

## Notes

The style guide should be **prescriptive but not restrictive**: cover
the common cases authoritatively, allow deviation when the diagram
needs it but require a one-line rationale in the surrounding prose.
The failure mode of style guides is rigidity that drives authors to
skip diagrams; the rule is "follow the guide *or* explain why."
