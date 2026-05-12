---
id: TASK-026
title: Write knowledge/BACKLOG.md — remaining educational rules
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-erc
order: 5
prerequisites: [TASK-024]
---

## Description

Author `.claude/skills/circuit/knowledge/BACKLOG.md` — the authoring
queue for educational-only rules that are *not* enforced by an ERC
predicate but enrich the skill's "senior designer" mentor framing.

Per `idea-001.rule-catalog.md` the target is 30–50 entries across
five categories; the seeded 15 cover the enforced checks. BACKLOG.md
lists the remaining 15–35 as a prioritised queue with one-line
descriptions, so future maintainers can pick from it without
re-litigating the scope.

## Acceptance Criteria

- [ ] `BACKLOG.md` lists at least 15 candidate educational rules across the five categories.
- [ ] Each entry has a one-line description and an indicative priority (high/medium/low).
- [ ] The file documents the authoring workflow (one rule per PR, reviewer checks source-of-truth link).
- [ ] No deep specifications — this is a queue, not a design doc.

## Test Plan

No automated tests required — this is a planning artefact. Spot-verify Markdown renders correctly.

## Prerequisites

- **TASK-024** — the seeded catalog establishes the format and conventions BACKLOG entries will follow.

## Notes

The 30–50 ceiling is deliberate — the catalog is not an electronics
textbook (see "What This Idea Deliberately Excludes" in
`idea-001-circuit-skill.md`).
