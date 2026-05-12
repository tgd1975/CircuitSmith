---
id: TASK-027
title: Wire catalog into ERC report writer
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: circuit-erc
order: 6
prerequisites: [TASK-022, TASK-024]
---

## Description

Extend `erc_engine.py`'s report writer so every non-OK finding (WARNING
or ERROR) gets a "Why / Senior's tip / Source" block appended,
sourced from the catalog entry whose `enforced_by` matches the
finding's check code.

The block format and tone are specified in
`idea-001.erc-engine.md §Enriched report format`. The lookup is
strictly by check code — no fuzzy matching, no LLM in the loop.

Findings without a matching catalog entry surface as a fail-loud
diagnostic (every shipped check is supposed to have a catalog row).

## Acceptance Criteria

- [ ] Every non-OK finding in `erc-report.md` carries the three-paragraph enrichment block.
- [ ] Lookup by check code; no fallback to keyword/fuzzy matching.
- [ ] A finding without a matching catalog row produces a fail-loud diagnostic naming the missing check code.
- [ ] The enrichment block formatting matches the spec in `idea-001.erc-engine.md §Enriched report format` (verified by snapshot test).

## Test Plan

Add `tests/test_erc_report_enrichment.py` with a fixture triggering one of each: WARNING-level finding (block appended), ERROR-level finding (block appended), missing-catalog-row finding (fail-loud).

## Prerequisites

- **TASK-022** — engine produces the findings.
- **TASK-024** — catalog provides the enrichment.

## Notes

See `idea-001.erc-engine.md §Enriched report format` for the canonical
block shape.
