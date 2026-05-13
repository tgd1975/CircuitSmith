---
id: TASK-104
title: Voice unification — pick canonical voice and rewrite earlier docs forward
status: open
opened: 2026-05-13
effort: Large (8-24h)
complexity: Senior
human-in-loop: Main
epic: post-epic-006-doc-audit
order: 3
prerequisites: [TASK-103]
---

## Description

The largest single task in this epic. The inventory (TASK-102) and
drift sweep (TASK-103) have identified what needs to change. This
task does the actual rewriting.

Decisions to make first:

- **Canonical voice.** Pick the voice used in the most recent
  EPIC-005 / EPIC-006 docs as the target. Capture it as a short
  style note (one paragraph) at the top of
  `docs/developers/CODING_STANDARDS.md` or a sibling doc — *the
  decision must be discoverable*, not folklore. A reader of any
  pre-EPIC-001 doc should be able to identify "this isn't the
  canonical voice" by reference to that note.
- **Scope discipline.** Voice rewrites *should* incidentally fix
  drift items from TASK-103 — they're the same files. But this
  task does **not** rewrite content that's stale-but-out-of-scope
  (e.g. fundamental architecture changes). If a section needs
  more than a voice pass to fix, log it as a follow-up task
  (with a TASK reference in the doc) rather than expanding scope.

Execution order:

- Walk pre-EPIC-001 freshness files first (highest drift, biggest
  voice gap).
- Then mid-epic freshness files (medium drift, narrowed scope).
- Skip epic-006 and post-epic-006 files (already canonical).

For each file:

1. Read the current state.
2. Cross-check the drift catalogue for items that touch this file.
3. Rewrite in canonical voice; fix the drift items inline.
4. Update the inventory's freshness column to `post-epic-006`.

This task is `human-in-loop: Main` because voice is judgment-heavy.
The agent should produce drafts; the maintainer reviews them.
Splitting the work across review batches (e.g. 5 files per review
pass) is the right tempo.

## Acceptance Criteria

- [ ] Canonical voice captured in a short style note in
      `docs/developers/CODING_STANDARDS.md` (or sibling).
- [ ] Every pre-EPIC-001 and mid-epic doc identified in TASK-102's
      inventory has been rewritten or explicitly skipped (with a
      one-line "skipped because…" in the inventory).
- [ ] Drift items from TASK-103 that touched rewritten files are
      resolved (the drift doc gets the items struck through with
      the resolving commit reference).
- [ ] No new content invented during rewriting — voice-pass only,
      not architecture revision.

## Test Plan

No automated tests required — change is documentation.

Manual verification:

1. After each review batch, the maintainer reads the rewritten
   files cold and signs off on voice.
2. `markdownlint-cli2` passes on every rewritten file.
3. Spot-check 3 drift items that touched rewritten files; confirm
   they no longer appear in the rewritten prose.

## Prerequisites

- **TASK-103** — the drift catalogue is the input. Without it, this
  task re-derives the same data and the audit/rewrite split blurs.

## Sizing rationale

Voice-unifying ~30-50 documents that span pre-EPIC-001 through
EPIC-005 is genuinely large, and splitting by file-batch turns out
to be the natural rhythm anyway (the Main HIL review boundary).
Keeping it whole captures the *commitment* to a uniform voice pass;
splitting would invite half-finishing the rewrite at some arbitrary
midpoint.

## Notes

- This is the task where the temptation to "while I'm here, let's
  also refactor this section" is highest. Resist. Voice-pass scope
  is the discipline; out-of-scope rewrites get filed as follow-ups
  and tackled in a separate epic if they prove necessary.
- The "skipped because…" exit clause exists for files whose voice
  is acceptable but whose content is too entangled with current
  work to safely rewrite. Don't over-use it; if more than ~10% of
  the inventory ends up skipped, the canonical voice was probably
  too narrow.
