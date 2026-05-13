---
id: TASK-108
title: Annotate the archived IDEA-001 dossier with what shipped vs what didn't
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Medium
human-in-loop: Main
epic: post-epic-006-doc-audit
order: 7
prerequisites: [TASK-104]
---

## Description

The IDEA-001 dossier in
`docs/developers/ideas/archived/idea-001.*` is a 9-file design
document for a system that didn't exist at the time. EPICs 001-006
incrementally made it real, but the dossier is frozen in its
original "this is what we plan to build" voice. Anyone reading it
six months from now will struggle to tell which parts shipped as
designed, which shipped differently, and which were dropped.

This task adds light annotation to the dossier — *inline* in each
file, at the section level — answering for each design choice:

- **Shipped as designed** — annotate "✅ shipped in EPIC-NNN" with a
  TASK reference if the implementation is in one task.
- **Shipped differently** — annotate "🔀 shipped in EPIC-NNN with
  changes: one-line summary of the deviation" and point at the
  ADR that records the deviation if one exists.
- **Dropped** — annotate "❌ not implemented; superseded by
  [ADR-NNNN]" or "❌ not implemented; out of scope".
- **Still future work** — annotate "⏳ still future; tracked in
  [IDEA-NNN]" or "⏳ still future; not yet filed".

The annotation is **light**: one line per design choice, inline in
the original prose. The dossier remains in its original voice as a
historical artefact; the annotations are clearly delimited (use a
distinct prefix like `> [Audit note 2026-XX-XX]:` so they're
visually separable from the body text and could be stripped
mechanically if ever needed).

This task is `human-in-loop: Main` because mapping design choices
to shipped implementations requires judgment that the agent can
draft but the maintainer must verify — the dossier is the historical
contract and inaccuracies here would mislead future readers.

## Acceptance Criteria

- [ ] Every section in `idea-001.md` and the eight companion files
      has at least one audit annotation (or an explicit "no
      annotation needed: descriptive only" note).
- [ ] Annotations use a uniform `> [Audit note YYYY-MM-DD]:` prefix.
- [ ] Every "shipped in EPIC-NNN" claim resolves to an EPIC file
      that exists.
- [ ] Every "superseded by ADR-NNNN" claim resolves to an ADR file
      that exists.

## Test Plan

No automated tests required — change is documentation.

Manual verification:

1. The maintainer reads the annotated dossier cold and confirms
   the annotations are accurate and useful.
2. `markdownlint-cli2` passes on the annotated files.
3. Cross-check 5 random "shipped in EPIC-NNN" annotations against
   the closed-task list; confirm the EPIC actually shipped the
   claim.

## Prerequisites

- **TASK-104** — voice rewrite must close (we don't want to
  annotate text that's about to be rewritten elsewhere).

## Notes

- This is the only task in EPIC-013 that *adds* content to archived
  files. The general rule for archived material is "leave it
  alone" — archived ideas / dossiers are frozen for history. The
  exception here is that the IDEA-001 dossier has unusual ongoing
  read traffic (it's referenced from EPIC-001 through EPIC-006,
  the ADR seed task, and elsewhere); without annotation, those
  readers consume an out-of-date design doc as if it were
  authoritative.
- Don't annotate the other archived ideas (idea-002, etc.) by
  default — they're scoped narrowly enough that one-line "shipped"
  / "dropped" notes are unnecessary. Only annotate IDEA-001
  because of its load-bearing role.
