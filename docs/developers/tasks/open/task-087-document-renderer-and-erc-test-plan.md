---
id: TASK-087
title: Author the renderer and ERC-engine subsystem test plans
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: test-plan-and-coverage
order: 5
prerequisites: [TASK-084]
---

## Description

Fill in `docs/developers/testing/renderer.md` and
`docs/developers/testing/erc-engine.md`.

The renderer chapter covers `src/circuitsmith/renderer.py` and the
YAML→SVG via Schemdraw pipeline (TASK-012). Its test surface is
dominated by golden SVG fixtures and visual-diff considerations —
this chapter documents *what we accept as a regression-safe diff*
and *what counts as an intended visual change*.

The ERC chapter covers `src/circuitsmith/erc_engine.py`, the rule
catalog under `src/circuitsmith/knowledge/`, and the renderer-pipeline
integration (TASK-023). It also covers the ERC report writer and the
catalog-validation script's overlap with the ERC chapter.

Both chapters follow the canonical structure (inputs/outputs, unit,
integration, golden, property/fuzz, performance budget, known
uncovered, PR-time/nightly/release).

Renderer-specific items to call out:

- **Golden SVG comparison policy** — byte-exact vs semantic diff.
  What change classes do we allow without re-baselining? (font
  metrics drift, schemdraw upstream changes, etc.)
- **Page-break testing** — once EPIC-012's multi-page example
  exists, that fixture should be referenced here.

ERC-specific items to call out:

- **Rule catalog coverage** — every S1–S5 and E1–E10 rule should
  have a fixture that triggers it. Document which rules currently
  have triggering fixtures and which are advisory-only at the
  fixture level.
- **The E9 warning rationale** (TASK-028) — referenced from this
  chapter, not duplicated.
- **Catalog validation** — `knowledge/validate_catalog.py`
  (TASK-025) gets a short sub-section explaining what it pins down
  (well-formedness, no orphan rule IDs in reports).

## Acceptance Criteria

- [ ] `renderer.md` and `erc-engine.md` are no longer empty
      placeholders and follow the canonical chapter structure.
- [ ] Renderer chapter documents the golden-SVG diff policy
      (byte-exact vs allowed drift classes) in one paragraph.
- [ ] ERC chapter enumerates which S1–S5 / E1–E10 rules have
      triggering fixtures and which do not, with rationale for the
      gaps.
- [ ] Every "known uncovered" item has a one-sentence rationale.

## Test Plan

No automated tests required — change is non-functional (documentation).

Manual verification:

1. Cross-check the rule-coverage table in the ERC chapter against
   the fixtures actually present under `tests/fixtures/erc/` (or
   wherever they live in-repo).
2. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-084** — the inventory is the raw material.

## Notes

- These two are paired because they sit at the tail end of the
  pipeline (renderer is the visual sink; ERC is the validation sink)
  and the integration test that exercises both at once is naturally
  forward-referenced from both chapters.
- The rule-coverage table is the part most likely to drift. Consider
  adding a CI guard (TASK-091 territory) that re-derives the table
  from the fixture directory and fails the build if `erc-engine.md`
  is stale.
