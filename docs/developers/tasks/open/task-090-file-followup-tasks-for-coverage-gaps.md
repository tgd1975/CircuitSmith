---
id: TASK-090
title: File concrete follow-up tasks for every coverage gap exposed by the plan
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Medium
human-in-loop: Main
epic: test-plan-and-coverage
order: 8
prerequisites: [TASK-089]
---

## Description

By the time TASK-089 closes, the matrix exposes every "known
uncovered" item that the per-subsystem chapters flagged. This task
converts that list of gaps into concrete follow-up tasks (or filed
ideas, where the gap is exploratory).

For each gap:

- **Tractable, scope-defined** → file as `/ts-task-new`, with the
  matrix cell linked from the task body. The task lands in whichever
  epic owns the subsystem (usually a future maintenance epic;
  short-term, "no epic, open" is fine).
- **Exploratory, scope-uncertain** → file as `/ts-idea-new` with the
  matrix cell linked from the idea body.
- **Acceptable gap with rationale** → no task filed; the chapter's
  "known uncovered" entry is the artefact.

This task is `human-in-loop: Main` because the triage decision
(tractable vs exploratory vs acceptable) is judgment-heavy and
benefits from a single human pass rather than per-gap clarification
loops.

## Acceptance Criteria

- [ ] Every "known uncovered" item across the seven chapter files
      has one of three states: filed as TASK-NNN, filed as
      IDEA-NNN, or annotated "acceptable" with rationale.
- [ ] The matrix's "Notes" column links to the filed task/idea
      where applicable, so a reader of the matrix can navigate from
      gap to follow-up.
- [ ] No "known uncovered" item is left unannotated.

## Test Plan

No automated tests required — change is task-system / documentation.

Manual verification:

1. `grep -i "known uncovered" docs/developers/testing/*.md` — every
   listed item should resolve to one of the three states above.
2. `python scripts/housekeep.py --apply` runs clean after the new
   tasks/ideas land.

## Prerequisites

- **TASK-089** — the matrix exposes the gaps this task triages.

## Notes

- Don't file more than ~5 new tasks in this pass. If the gap list is
  longer, file an idea per *group* of related gaps rather than per
  individual gap — gap-filing should not flood the open-task queue.
- This task is intentionally placed at order 8 (before the CI
  guardrail at order 9). The reason: the staleness CI check should
  only land *after* the matrix is in a stable state with all gaps
  resolved one way or another, so the check is not constantly
  red-flagging known-uncovered items as missing-from-plan.
