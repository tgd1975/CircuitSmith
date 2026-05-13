---
id: TASK-106
title: Tutorial alignment — audit reference docs against EPIC-012's tutorial and gallery
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Medium
human-in-loop: Clarification
epic: post-epic-006-doc-audit
order: 5
prerequisites: [TASK-104]
---

## Description

EPIC-012 ships a tutorial under `docs/users/tutorial/` and a gallery
under `docs/users/examples/`. Both tell stories about how to author
`.circuit.yml` and what each subsystem does. The reference docs
under `docs/developers/` (especially `circuit-yaml.md`, `layout.md`,
`erc-checks.md`) also tell those stories — at a lower level, but
the *terminology and behaviour claims* should match.

This task audits the reference docs against the tutorial and
gallery, looking for:

- **Terminology drift** — tutorial says "net", reference doc says
  "node" or "signal" interchangeably.
- **Behaviour claims that disagree** — tutorial step 4 demonstrates
  an ERC failure mode; `erc-checks.md` describes the same rule but
  with a slightly different name or scope.
- **Examples that disagree** — reference docs include code blocks;
  tutorial uses a different syntax for the same construct.
- **Missing pointers** — the reference docs do not learn to point
  at the tutorial / gallery as user-friendly entry points.

For each disagreement, **the tutorial wins** as the canonical
artefact (it's the version a reader actually runs end-to-end), and
the reference doc is fixed forward. Exception: where the tutorial's
simplification is misleading at the reference-level, file a
follow-up to clarify the tutorial — don't push complexity back
into a doc that's meant to be approachable.

This task does *not* require EPIC-012 to be fully closed — it
requires enough of EPIC-012 to be done that the canonical
terminology and behaviour claims are stable. In practice: TASK-093
(scaffolding) and TASK-094 (tutorial steps 1-3) is the minimum.

## Acceptance Criteria

- [ ] Every reference doc has been spot-checked against the
      relevant tutorial step or gallery example.
- [ ] Disagreements resolved in the reference doc (or filed as
      follow-up if the tutorial needs adjustment).
- [ ] Reference docs (`circuit-yaml.md`, `layout.md`,
      `erc-checks.md`) gain a "See also" pointer to the tutorial
      / gallery near the top.
- [ ] Terminology consistent: a glossary entry in
      `docs/developers/ARCHITECTURE.md` (or sibling) captures the
      canonical terms.

## Test Plan

No automated tests required — change is documentation.

Manual verification:

1. Read the tutorial cold; read each reference doc cold. List any
   terms that feel different. Reconcile.
2. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-104** — voice rewrite must close so we're not auditing
  about-to-be-rewritten text.
- **(Soft) EPIC-012 task progress** — at least TASK-093 and
  TASK-094 closed. This is *not* a hard prerequisite because the
  agent can audit against the existing tutorial scaffolding even
  if later steps are not yet written.

## Notes

- The "tutorial wins" rule is a deliberate choice. The alternative
  ("the reference doc wins because it's more authoritative") has
  the failure mode that the tutorial drifts away from what readers
  experience when they run it. The tutorial *is* the experience;
  the reference doc describes it.
- Don't fold this into TASK-107 (test-plan alignment). They sound
  similar but the failure modes are different — tutorial alignment
  is about *user-facing terminology*, test-plan alignment is about
  *test-surface accuracy*. Mixing them risks botching both.
