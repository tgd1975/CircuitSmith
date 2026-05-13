---
id: TASK-107
title: Test-plan alignment — audit "how it's tested" sections against EPIC-011's plan
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Medium
human-in-loop: Clarification
epic: post-epic-006-doc-audit
order: 6
prerequisites: [TASK-104]
---

## Description

Many `docs/developers/` files have a "How it's tested" sub-section
or paragraph. EPIC-011 produces the canonical version of those
claims in `docs/developers/testing/`. This task makes sure the
narrative docs and the canonical test plan agree.

For each narrative doc with a testing claim (most likely
candidates: `ARCHITECTURE.md`, `CODING_STANDARDS.md`,
`COMMIT_POLICY.md`, the per-subsystem reference docs):

- Verify the claim matches what the relevant chapter in
  `docs/developers/testing/` says.
- Where the narrative doc has too much detail (duplicates the
  chapter), collapse it to a one-paragraph summary + a pointer.
- Where the narrative doc has *less* detail than the chapter,
  decide whether to expand inline (rare — usually duplication) or
  just add a "see `docs/developers/testing/X.md` for details"
  pointer.

The result should be: each subsystem reference doc has one
paragraph on how it's tested + a link to the chapter. The chapter
has the depth. No information lives in two places.

This task does *not* require EPIC-011 to be fully closed — it
requires enough that the canonical test-plan chapters exist. In
practice: TASK-083 (scaffolding) and TASK-089 (matrix) is the
minimum.

## Acceptance Criteria

- [ ] Every narrative doc with a testing claim has been audited
      against the matching test-plan chapter.
- [ ] Duplicated content collapsed to a summary + pointer.
- [ ] Disagreements resolved (chapter wins; narrative doc fixed).
- [ ] Each narrative doc with a testing relevance has at least one
      "see `docs/developers/testing/X.md`" link.

## Test Plan

No automated tests required — change is documentation.

Manual verification:

1. `grep -ri "test" docs/developers/ | grep -v "/testing/"` and
   confirm every match is either a one-line summary with a pointer
   or genuinely subsystem-narrative-relevant (not duplicating the
   chapter).
2. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-104** — voice rewrite must close.
- **(Soft) EPIC-011 task progress** — at least TASK-083 and
  TASK-089 closed.

## Notes

- "Chapter wins" is the dual of TASK-106's "tutorial wins" rule.
  Same reason: the canonical artefact is the one that's
  machine-checked or end-to-end-runnable; narrative docs
  paraphrase it.
- A common pitfall: removing the testing claim from a narrative
  doc entirely. Don't — readers of the architecture doc *want* a
  one-paragraph orientation, not a bare pointer. Keep the
  summary, just don't let it duplicate the chapter.
