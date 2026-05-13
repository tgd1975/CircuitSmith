---
id: TASK-092
title: Decide docs/users/ structure and update README pointer
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Medium
human-in-loop: Main
epic: tutorial-and-examples
order: 1
---

## Description

The repo currently only has `docs/developers/`. The tutorial and the
example gallery are *user-facing* artefacts and need a home that
makes the audience split discoverable from the repo root.

Three options to consider:

1. **Add `docs/users/`** alongside `docs/developers/` and update
   `README.md` to point at both. Sibling structure, clear separation.
2. **Reshape `docs/`** with a top-level `docs/README.md` that splits
   the audiences, then nest `docs/developers/` and `docs/users/`
   underneath. More intrusive; touches existing paths.
3. **Fold under `docs/`** with a README that explains the audience
   split without subdirectories — tutorial at `docs/tutorial/`,
   gallery at `docs/examples/`, developer docs stay where they are.

Recommendation (defended in the task body, not pre-committed): **option 1**.
The `docs/users/` sibling is the smallest change consistent with how
the rest of the repo treats audience splits (`builders/`,
`developers/` are sibling folders); option 2 invents an indirection
the codebase does not otherwise use; option 3 produces an asymmetric
tree (one audience nested, one not).

Output: this task is `human-in-loop: Main` — the choice is
deliberately surfaced to the maintainer because it shapes every
subsequent task in this epic. Once decided, this task lands:

- The chosen directory structure created (empty stubs; content lands
  in TASK-093 and later).
- `README.md` learns to point at the new home with a single-line
  callout in the top-level "Documentation" section.
- An ADR if the decision is non-obvious or revisits an existing
  convention.

## Acceptance Criteria

- [ ] Directory structure exists with the chosen layout (empty stubs
      are fine).
- [ ] `README.md` has an updated documentation pointer.
- [ ] Decision rationale captured — either in the commit message or
      a short ADR under `docs/developers/adr/`.

## Test Plan

No automated tests required — change is non-functional (documentation
structure decision).

Manual verification:

1. `markdownlint-cli2` passes on the changed README.
2. From a clean clone, a reader of `README.md` can find the user
   docs in under 30 seconds (eyeball check; ask a fresh reader if
   one is available).

## Notes

- This task is `human-in-loop: Main` because every other task in the
  epic forward-references the chosen path; getting it wrong on the
  first pass forces a rename pass across 8+ tasks.
- The README pointer is intentional. The repo's README is the first
  thing GitHub visitors see; if user docs exist but the README does
  not link them, they functionally do not exist.
