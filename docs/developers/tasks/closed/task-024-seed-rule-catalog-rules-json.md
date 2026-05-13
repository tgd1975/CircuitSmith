---
id: TASK-024
title: Seed knowledge/rules.json with 15 entries (S1–S5 + E1–E10)
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Medium
human-in-loop: Support
epic: circuit-erc
order: 3
prerequisites: [TASK-022]
---

## Autonomy

`Main` → `Support` per TASK-060 sweep. Rule-catalog prose is
content-heavy and benefits from a maintainer-eyes pass — auto-prepare
the seed rules, pause for review at the commit stop-line. The
catalog is the ERC engine's authoritative source (ADR-0006) so
content quality is load-bearing.

## Description

Seed `.claude/skills/circuit/knowledge/rules.json` with one entry per
shipped ERC check (15 total: S1–S5 + E1–E10). Each entry declares
`rule`, `explanation`, `heuristic`, `source_of_truth` (URL),
`keywords`, `enforced_by` (matching the check code).

All prose is **reformulated in English** from
elektronik-kompendium.de, manufacturer datasheets, or other linked
sources — no copied text. The catalog format and licensing policy are
specified in `idea-001.rule-catalog.md`.

Every `heuristic` field carries a precision-disclaimer substring (per
TASK-025 validation): "this is a starting point, not an exact answer"
or equivalent. This prevents the skill from presenting heuristics as
authoritative.

## Acceptance Criteria

- [x] 15 entries seeded, one per shipped check code (S1–S5 + E1–E10).
- [x] Every entry has all six required fields populated.
- [x] Every `source_of_truth` URL is reachable at seed time (validated manually before commit).
- [x] Every `heuristic` carries a precision disclaimer (validated by TASK-025).
- [x] No copied text from sources — every entry is a reformulation.

## Test Plan

Manual review by the maintainer (HIL: Main) — confirm prose accuracy and source attribution. TASK-025 then provides automated structural validation.

## Prerequisites

- **TASK-022** — `erc_engine.py` defines the 15 check codes the catalog references.

## Notes

S4 and S5 are schema-generated findings (no `erc_engine.py` predicate
fires), but they get catalog rows so the report writer can look them
up under the same pipeline. `enforced_by` for these two is set to
`schema` (not a predicate function name).
