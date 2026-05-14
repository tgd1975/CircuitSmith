---
id: TASK-127
title: Cross-page ERC rules (4 rules)
status: open
opened: 2026-05-14
effort: Medium (2-8h)
complexity: Medium
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 18
prerequisites: [TASK-126]
---

## Description

Adds the four cross-page ERC rules from IDEA-009 *ERC — Half 2
(multi-page)* to
[`src/circuitsmith/erc_engine.py`](../../../src/circuitsmith/erc_engine.py)
(see `co-erc-engine` reminder):

- **Page declared but empty** — a `pages:` entry with no
  components assigned to it. Warning — the YAML parses, but the
  user almost certainly meant to populate it.
- **Page referenced but undeclared** — a placement carries `page:
  p3` but `pages:` only declares `p1` / `p2`. Error.
- **Cross-page net invisible on one side** — a net whose pins
  appear on multiple pages but whose label would render
  off-canvas (bounding-box overflow) on at least one of them.
  Error — the label is the only thing keeping the cross-page
  reference traceable.
- **Excessive cross-page net count** — heuristic warning; if more
  than ~6 nets cross any single page boundary, the page split is
  probably in the wrong place. Threshold tunable, default 6.

Rule IDs are minted from the existing ERC catalogue when the work
lands.

## Acceptance Criteria

- [ ] All four rules added with codes, catalogue entries, and error-message text.
- [ ] Each rule has a golden failing fixture *and* a golden negative fixture under `tests/fixtures/erc/`.
- [ ] ERC catalogue documentation in [.claude/skills/circuit/docs/erc-checks.md](../../../.claude/skills/circuit/docs/erc-checks.md) gains rows for the four rules.
- [ ] Excessive-cross-page-net-count threshold is configurable via a config knob (not hardcoded).

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/erc/test_cross_page_rules.py`.
- Cover: each of the four rules with both failing and negative
  cases; threshold tuning for the heuristic warning; the
  off-canvas-label rule reads from the actual renderer output
  (this rule runs *after* layout but verifies *rendering*
  feasibility).

## Prerequisites

- **TASK-126** — the cross-page label rendering must be in place
  for the off-canvas-overflow rule to test against actual glyph
  positions.

## Notes

- The four rules are tightly related (all about page-boundary
  invariants) and share a fixture base (multi-page circuits with
  targeted defects). One task keeps the fixture authoring
  coherent.
- The excessive-cross-page-net-count warning is the only
  *heuristic* of the four — it's advisory, not load-bearing. The
  threshold (~6) is a starting point; gallery use will tune it.
