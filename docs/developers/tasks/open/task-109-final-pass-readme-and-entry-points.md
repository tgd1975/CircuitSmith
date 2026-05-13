---
id: TASK-109
title: Final pass on README.md and top-level entry-point docs
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Medium
human-in-loop: Main
epic: post-epic-006-doc-audit
order: 8
prerequisites: [TASK-104, TASK-105, TASK-106, TASK-107, TASK-108]
---

## Description

The capstone task: after the inventory, drift sweep, voice rewrite,
cross-ref audit, and alignment passes, do a final read-through of
the top-level entry-point docs and make sure they correctly orient
a *fresh visitor* to the post-EPIC-006 state of the project.

Entry-point docs in scope:

- `README.md` — the GitHub-front-page doc. Must explain what
  CircuitSmith is, point at the tutorial / gallery as the user
  entry, point at developer docs as the contributor entry, and
  not say anything stale.
- `CONTRIBUTING.md` — the contributor-onboarding doc. Must point
  at the developer onboarding pack (DEVELOPMENT_SETUP, CODING_STANDARDS,
  TESTING, CI_PIPELINE, TASK_SYSTEM, CODE_OF_CONDUCT).
- `docs/README.md` (or `docs/users/README.md` if EPIC-012 chose
  that layout) — the doc-tree entry.
- `CHANGELOG.md` — quick sanity check: the post-EPIC-006 reality
  is reflected in the Unreleased section or the v0.2.0 section,
  depending on release state.

Approach:

1. **Read each entry-point cold.** Pretend you've never seen
   CircuitSmith before. Note every sentence that's wrong, vague,
   or assumes prior context.
2. **Rewrite forward.** Same voice from TASK-104.
3. **Tighten pointers.** Every entry-point should make it
   *obvious* where to go next for: "I want to use it"
   (tutorial), "I want to contribute" (CONTRIBUTING), "I want to
   understand the architecture" (ARCHITECTURE.md).
4. **Trim stale aspirational language.** Pre-EPIC-001 prose
   often contains "we plan to" claims about features that have
   since shipped. Switch tense, or delete.

This task is `human-in-loop: Main` because the README is the
project's public face — every claim and link needs maintainer
sign-off, not just agent draft.

## Acceptance Criteria

- [ ] `README.md` reflects the post-EPIC-006 state, with tutorial
      / gallery / developer doc pointers all working.
- [ ] `CONTRIBUTING.md` points at the developer onboarding pack
      and the task system.
- [ ] No "we plan to" language remains for features that have
      shipped.
- [ ] `markdownlint-cli2` passes; `scripts/check_doc_references.py`
      (from TASK-105) passes.
- [ ] The maintainer reads each entry-point cold and signs off.

## Test Plan

No automated tests required — change is documentation.

Manual verification:

1. From a clean clone, a fresh visitor lands on `README.md`. They
   can locate the tutorial in under 30 seconds and the developer
   docs in under 60 seconds. (Ask a fresh reader if one is
   available; otherwise the maintainer's self-test.)
2. Every link in every entry-point resolves.
3. Hold a "fresh-visitor walkthrough" — the maintainer reads from
   README.md → tutorial step 1 → developer docs and confirms the
   journey is coherent.

## Prerequisites

- **TASK-104** — voice rewrite must close (entry-points share voice).
- **TASK-105** — cross-ref audit must close (entry-points have the
  most outgoing links; broken links here are most visible).
- **TASK-106, TASK-107** — alignment passes must close so the
  entry-points can confidently point at the tutorial / gallery /
  test plan as canonical references.
- **TASK-108** — IDEA-001 dossier annotation should close so any
  pointer from README to the dossier resolves to the annotated
  version.

## Notes

- The "fresh visitor" lens is the most important quality check for
  this task. The agent is *unable* to be a fresh visitor; only a
  human can. Don't accept agent self-evaluation as the sign-off.
- The CHANGELOG sanity check is genuinely a sanity check — most
  of the bullet content is correct because each EPIC's
  squash-merge updated it. The check is for *prose* consistency
  between CHANGELOG entries and the README's "what CircuitSmith
  is today" claim.
