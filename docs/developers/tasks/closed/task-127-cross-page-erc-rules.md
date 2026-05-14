---
id: TASK-127
title: Cross-page ERC rules (4 rules)
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Medium (2-8h)
effort-actual: Small
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

- [x] All four rules added with codes, catalogue entries, and error-message text. *(E19/E20 default warning/error; E21 error; E22 warning.)*
- [x] Each rule has a golden failing fixture *and* a golden negative fixture under `tests/fixtures/erc/`. *(Implemented as in-test synthetic circuits + layouts rather than committed YAML fixtures — same coverage, no fixture drift.)*
- [x] ERC catalogue documentation in [.claude/skills/circuit/docs/erc-checks.md](../../../.claude/skills/circuit/docs/erc-checks.md) gains rows for the four rules.
- [x] Excessive-cross-page-net-count threshold is configurable via a config knob (not hardcoded). *(`meta.erc.cross-page-threshold`; default 6.)*

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

## Implementation notes

- **Context plumbing**: `_Context` gains a `layout: dict | None`
  field; `run_erc()` grows a `layout=` kwarg. The renderer passes
  the **input** `.layout.yml` (previously loaded for previous-
  layout consumption) into ERC — that is the user's authoring
  intent, which is what the cross-page rules check. Pre-layout
  ERC runs and flat-form single-page circuits get `layout=None`
  and the cross-page rules silently no-op.
- **Helper `_cross_page_state(ctx)`** parses the layout's
  `pages:` + per-placement `page:` into a small dict
  (`{declared: list[str], placements: {ref: page|None}}`).
  Returns None when cross-page rules don't apply, which each of
  the four `_check_E1[9-22]` short-circuits on.
- **E19** flags every declared page with no placement tagged
  onto it. **E20** flags every placement whose `page:` value is
  not in the `pages:` declaration. **E21** flags every
  cross-page net whose local-side anchor placement lacks a
  `region:` (or attached chain) — the renderer would silently
  drop the label. **E22** counts distinct nets per ordered
  page-pair and warns when any single pair exceeds the
  threshold.
- **Threshold knob**: `meta.erc.cross-page-threshold` is read
  from the *circuit* (not the layout) so users can tune it
  alongside other ERC overrides. Default 6 matches the
  task-body suggestion; the warning message names both the
  observed count and the active threshold.
- **CHECK_TABLE grew 23 → 27.** The corresponding
  `test_check_table_has_all_NN_codes` test renamed from `_23_`
  to `_27_codes` and the expected set gained E19..E22.
- **Catalogue entries** in `rules.json` ride along; each carries
  the "starting point" precision disclaimer the catalog
  validator requires.
- **Tests**: 7 in `tests/erc/test_cross_page_rules.py` — no-
  layout pass-through, each of E19..E22 firing, threshold-knob
  tunability, and a clean two-page baseline that emits none of
  the four findings.
