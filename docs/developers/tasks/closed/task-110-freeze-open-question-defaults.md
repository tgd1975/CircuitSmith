---
id: TASK-110
title: Freeze open-question defaults for EPIC-014
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: XS (<30m)
effort_actual: XS (<30m)
complexity: Junior
human-in-loop: Main
epic: circuit-library-and-renderer-v2
order: 1
---

## Description

Walk the *Open questions* sections of both seed ideas and confirm or
override each proposed default. Decisions land in the epic body (or
in ADRs where they ripple beyond this epic). Once frozen, these
become epic-body invariants the implementation tasks consume — not
mid-task ADRs.

The questions to resolve:

**From IDEA-008** — refdes flattening scheme
(`<local>_<instance>`), port-naming convention (named ports map,
deprecate inputs/outputs aliases), sub-block-internal `connections:`
grammar (reuse top-level), voltage-divider rule discriminator
(tap-net-name regex or `role: divider`), nested sub-blocks (v1
disallows), renderer mode default (v1 inline-box, hierarchical
gated on IDEA-009).

**From IDEA-009** — bundle-vs-split is already resolved by this
epic's existence (single bundled epic). Remaining: BJT terminal-role
encoding (`pins.X.role:`, not `metadata.bjt_terminals`), 555 pin
keys (silkscreen `"1".."8"` per ADR-0010), op-amp pin keys
(symbolic — `IN+`/`IN-`/`OUT`/`V+`/`V-`), cross-page label glyph
(Schemdraw arrow), CLI shape (auto-suffix `<stem>-p<n>.svg`),
cross-page net detection (flattener inspects pin list, no YAML
declaration).

## Acceptance Criteria

- [x] Every open question from IDEA-008 has a recorded decision in the epic body or an ADR.
- [x] Every open question from IDEA-009 has a recorded decision in the epic body or an ADR.
- [x] The two idea bodies' *Open questions* sections are updated to mark the resolved defaults as Decided (with a back-pointer to the epic body or ADR).

## Outcome

All proposed defaults from both ideas were accepted verbatim. The
single override is IDEA-009's "split into 009a/009b" — resolved by
EPIC-014's existence as a single bundled epic. Recorded in the epic
body's *Frozen decisions* section; both archived idea Open-questions
sections now point back to the epic for the canonical answers.

## Test Plan

No automated tests required — change is documentation. Decisions
are validated by the downstream implementation tasks consuming them
without surprises.

Manual verification:

1. `markdownlint-cli2` passes on the edited files.
2. Each downstream task body can be read end-to-end without needing
   to re-derive a frozen decision.

## Notes

- The proposed defaults in each idea are the recommended answers.
  This task is about *commitment*, not re-litigation — only override
  a default when a new constraint surfaces during the prep phase.
- Decisions that ripple beyond this epic (e.g. the refdes-flattening
  scheme — affects all future flattener consumers) become ADRs.
  Decisions scoped to this epic stay in the epic body.
