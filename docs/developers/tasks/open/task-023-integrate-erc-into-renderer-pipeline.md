---
id: TASK-023
title: Integrate ERC into renderer pipeline (post-schema, pre-drawing)
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Medium
human-in-loop: No
epic: circuit-erc
order: 2
prerequisites: [TASK-022, TASK-012]
---

## Description

Wire `erc_engine.py` into `renderer.py` at its canonical pipeline
position: after schema validation, before any layout/geometry work.
ERROR-level findings abort the pipeline with a non-zero exit code and
the structured diagnostic from the engine.

WARNING-level findings produce report content but do not abort —
this is the path E9 takes on v0.1.

## Acceptance Criteria

- [ ] `renderer.py` calls `erc_engine.run(net_graph)` after schema validation, before kernel invocation.
- [ ] Any ERROR-level finding aborts the renderer with exit code 1 (or a documented code distinct from schema/rubric exits).
- [ ] WARNING-level findings are recorded in the report but do not abort.
- [ ] The pipeline order matches `idea-001-circuit-skill.md §Pipeline`.

## Test Plan

Extend `tests/test_renderer.py` (TASK-012) with fixtures triggering an ERROR-level finding (renderer exits non-zero, no SVG written) and a WARNING-level finding (renderer succeeds, report contains the warning).

## Prerequisites

- **TASK-022** — `erc_engine.py` must exist.
- **TASK-012** — the renderer pipeline must exist.

## Notes

Per `idea-001.erc-engine.md`, ERC is strictly pre-layout — never
reads `layout.yml`, never consumes geometry. The integration point is
fixed by the pipeline shape, not by convenience.
