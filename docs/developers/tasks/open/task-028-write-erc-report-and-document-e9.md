---
id: TASK-028
title: Write erc-report.md for each target; document E9 WARNING rationale
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-erc
order: 7
prerequisites: [TASK-027]
---

## Description

Run the integrated renderer + ERC pipeline against both shipped
`.circuit.yml` files and commit the resulting `erc-report.md` outputs
alongside each target's SVG.

Both targets surface E9 as WARNING on v0.1 — document this in a
"Pending promotions" rationale block in each report so future readers
do not misread the warning as a transient diagnostic. The block
mentions the `diode`-category backlog as the promotion path.

## Acceptance Criteria

- [ ] `docs/builders/wiring/esp32/erc-report.md` exists and reflects current ERC findings.
- [ ] `docs/builders/wiring/nrf52840/erc-report.md` exists and reflects current ERC findings.
- [ ] Both reports contain the "Pending promotions" rationale block for E9.
- [ ] Reports are produced by the renderer (not hand-edited) — re-running the pipeline produces byte-identical output.

## Test Plan

CI staleness guard (extended in TASK-029) provides the regression test: any divergence between the committed `erc-report.md` and the renderer-produced one fails the build.

## Prerequisites

- **TASK-027** — the report writer must produce the enriched format these reports embody.

## Notes

E9 auto-promotes to ERROR when the `diode` category lands in the
component library (a backlog item in `idea-001.components.md`).

## Predecessor source

The `docs/builders/wiring/<target>/` directory tree is inherited from
[AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal/tree/main/docs/builders/wiring)
via TASK-001 / TASK-015. This task writes new `erc-report.md` files into that
tree once it lands in CircuitSmith.
