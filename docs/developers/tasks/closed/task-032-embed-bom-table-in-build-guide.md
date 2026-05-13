---
id: TASK-032
title: Embed BOM table in build guide
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-exporters
order: 2
prerequisites: [TASK-031]
---

## Description

Embed each target's `bom.md` content into the matching build guide at
`docs/builders/wiring/<target>/`. The embed is automatic (a doc
include directive or a CI-driven copy) so the table stays in sync
with the renderer output.

## Acceptance Criteria

- [x] `docs/builders/wiring/esp32/` and `docs/builders/wiring/nrf52840/` each show the BOM table inline.
- [x] Editing `.circuit.yml` and re-running the renderer updates the embedded BOM table without manual intervention.
- [x] If IDEA-022 (MkDocs) has landed, use MkDocs `pymdownx.snippets` or equivalent include syntax; otherwise use a simple CI copy step.

## Test Plan

No automated tests required beyond TASK-031's snapshot test. Manually spot-verify the rendered build guide after the next CI run.

## Prerequisites

- **TASK-031** — `bom.md` files must exist to embed.

## Notes

Once IDEA-022 lands, this task's mechanism may need an adjustment to
use MkDocs includes natively. Document the current mechanism inline
so the future swap is trivial.

## Predecessor source

The `docs/builders/wiring/<target>/` build guides are inherited from
[AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal/tree/main/docs/builders/wiring)
via TASK-001 / TASK-015.
[IDEA-022](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-022-mkdocs-documentation-site.md)
(MkDocs site) is an AwesomeStudioPedal idea — its landing status is tracked
there, not here.
