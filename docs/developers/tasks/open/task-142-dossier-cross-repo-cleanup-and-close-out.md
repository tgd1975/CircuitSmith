---
id: TASK-142
title: Cross-repo reference cleanup and walk-coverage verification
status: open
opened: 2026-05-15
effort: Small (<2h)
complexity: Medium
human-in-loop: Clarification
epic: dossier-gap-analysis
order: 9
prerequisites: [TASK-134, TASK-135, TASK-136, TASK-137, TASK-138, TASK-139, TASK-140, TASK-141]
---

## Description

The dossier walk is done by the time this task starts — every
sub-table in `docs/developers/_dossier-gap-analysis.md` has rows
from one of TASK-134..141. Two final steps close the epic:

1. **Cross-repo reference cleanup.** The dossier's relationship
   table cites AwesomeStudioPedal's IDEA-011, IDEA-018, IDEA-019,
   IDEA-022 — **not** this repo's IDEA-011 (which is unrelated).
   For each ASP reference the walk surfaced, open the file in the
   user's local AwesomeStudioPedal checkout and decide one of three
   verdicts:
   - **Relevant** — the ASP idea still maps to CircuitSmith work.
     Restate the relationship in CircuitSmith terms inside the
     row, drop the bare ASP reference.
   - **Superseded** — the ASP idea was archived there or rolled
     into something else. Drop the reference; no follow-up.
   - **Out-of-scope post-split** — the ASP idea is genuinely
     ASP-only (e.g. firmware-side concerns). Drop the reference; no
     follow-up.

   **Do not** spawn a CircuitSmith IDEA solely to mirror an ASP
   one — only spawn if CircuitSmith has work to do. This is the
   `human-in-loop: Clarification` point: ASP-repo access and the
   "still relevant?" judgment may need a user check-in.

2. **Coverage verification.** Walk every dossier file listed in
   the archived
   [`idea-012`](../../ideas/archived/idea-012-revisit-original-concept-vs-0-1-0.md)'s
   "Scope of the analysis" section and confirm against the working
   doc:
   - Every dossier file has a corresponding analysis sub-table in
     `_dossier-gap-analysis.md`.
   - Every sub-table has at least one row.
   - Every row meets its bucket's archival trigger (see the
     archived idea's "Deliverable shape" section): bucket 1 →
     one-line confirmation; bucket 2 → verdict or spawned IDEA
     link; bucket 3 → gate-condition + evidence; bucket 4 →
     spawned IDEA-NNN link.

   If any row fails its trigger, fix it before closing the epic.
   This is the **only** opportunity to catch missed coverage
   before the epic closes.

The idea itself is **not** archived by this task — IDEA-012 was
archived at the moment EPIC-015 was elevated, per the project's
"archive idea on elevation, not on close-out" rule. If the walk
spawned any bucket-4 IDEAs, `/housekeep` and `/commit` flow through
the normal channels.

## Acceptance Criteria

- [ ] Every ASP-repo cross-reference in the dossier has a verdict
      (relevant / superseded / out-of-scope) recorded in the
      affected analysis row.
- [ ] No analysis row consists solely of "see ASP IDEA-NNN" — all
      ASP refs are either re-stated in CircuitSmith terms or
      dropped.
- [ ] Coverage check confirms every dossier file in the archived
      idea's "Scope" section has a non-empty sub-table in
      `_dossier-gap-analysis.md`.
- [ ] Every analysis row meets its bucket's archival trigger.

## Test Plan

No automated tests required — change is documentation / analysis.

Manual verification:

1. `grep -c "see ASP" docs/developers/_dossier-gap-analysis.md`
   returns 0 (all ASP-only refs resolved).
2. Section count in the working doc matches the dossier-file count
   listed in the archived idea's "Scope of the analysis" section.

## Notes

- The ASP-repo path conventions are sketched in the archived
  IDEA-012's "Open questions" cross-repo bullet. If the user's
  local ASP checkout isn't at the expected path, ask before diving
  into a fallback hunt — per CLAUDE.md "Missing executables" rule,
  applied to missing repos.
- If the bucket-4 spawn count across TASK-134..141 exceeds five,
  surface that before closing — the archived idea explicitly
  flagged this as a signal that "something was missed in the
  original conversion". Don't silently land six new IDEAs.
- This task no longer carries an idea-archive step — IDEA-012's
  archive ride along with the elevation commit (the squash commit
  that opens this epic). The convention is documented in CLAUDE.md
  and in MEMORY.md's `feedback-archive-idea-on-elevation` entry.
