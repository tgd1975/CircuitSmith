---
id: TASK-037
title: Implement show_source flag for Markdown blocks
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-markdown-integration
order: 2
prerequisites: [TASK-036]
---

## Description

Add a `show_source` flag to the ` ```circuit ` block syntax. When set,
the rendered output wraps the SVG embed in a `<details>` / `<summary>`
block that reveals the source YAML on click — useful for tutorials
where readers want to see the input alongside the result.

Default behaviour (flag absent) is unchanged: SVG only, no source
visible.

## Acceptance Criteria

- [x] Block syntax accepts `show_source` as a flag (e.g. ` ```circuit show_source ` or YAML-frontmatter style).
- [x] When set, output includes a `<details>` block with the verbatim source YAML.
- [x] When absent, output is unchanged from TASK-036 baseline.
- [x] Flag is documented in `docs/circuit-yaml.md` with a worked example.

## Test Plan

Extend `tests/test_markdown_block.py` (TASK-036) with two fixtures: `show_source` on (`<details>` present), `show_source` off (no `<details>`).

## Prerequisites

- **TASK-036** — the block rewrite must exist.

## Notes

The `<details>` element is supported by GitHub Markdown rendering and
by MkDocs natively — no special handling needed for either build
mechanism.
