---
id: ADR-0014
title: User-facing docs live at `docs/users/`, a sibling of `developers/` and `builders/`
status: Accepted
date: 2026-05-13
---

## Context

EPIC-012 ships a linear tutorial and a curated example gallery — both
user-facing artefacts. The repo today carries developer docs under
`docs/developers/` and per-target wiring artefacts under
`docs/builders/`, both sibling folders at `docs/`'s top level. With
TASK-092, the user-docs home had to be decided before tutorial
content (TASK-093 onwards) could land, because every later task in
the epic forward-references the chosen path. Three options were on
the table (recorded in [TASK-092](../tasks/active/task-092-decide-docs-users-structure.md)):

1. Add `docs/users/` alongside `developers/` and `builders/`.
2. Reshape `docs/` with a top-level `docs/README.md` audience
   splitter, nesting both developer and user docs underneath.
3. Fold the tutorial and gallery directly under `docs/`
   (`docs/tutorial/`, `docs/examples/`) without a `users/` parent.

## Decision

Option 1. User-facing docs live at `docs/users/` with
`docs/users/tutorial/` and `docs/users/examples/` as the two seed
subdirectories. The repo's `README.md` learns a top-level
"Documentation" pointer that names all three audiences (users,
builders, developers).

The decision mirrors how the repo already splits audiences — the
existing `developers/` ↔ `builders/` sibling pair sets the
convention, and a third sibling extends it the same way. Option 2
invents an indirection (`docs/README.md` audience splitter) the
codebase does not otherwise use; option 3 produces an asymmetric
tree (one audience nested, one not) that obscures the split that
exists.

## Consequences

**Easier:**

- The audience split is discoverable at one `ls docs/` glance.
- Tutorial / gallery paths in later EPIC-012 tasks land at the
  natural `docs/users/tutorial/...` / `docs/users/examples/...`
  prefix without forward-reference juggling.
- EPIC-013 (post-EPIC-006 doc audit) gains a stable target tree to
  reconcile reference docs against, per
  [TASK-106](../tasks/open/task-106-tutorial-alignment-with-epic-012.md).

**Harder:**

- A future MkDocs migration (AwesomeStudioPedal IDEA-022's
  equivalent here) will need a navigation tree that surfaces all
  three folders. This is judged a non-issue: MkDocs's `nav:` block
  handles it directly.
- Onboarding docs (`CONTRIBUTING.md`, top-level `README.md`) must
  keep all three sibling pointers in sync. Acceptable cost; the
  README's "Documentation" section is the canonical pointer.

## See also

- [TASK-092](../tasks/active/task-092-decide-docs-users-structure.md) — the task this decision closes.
- [EPIC-012](../tasks/active/epic-012-tutorial-and-examples.md) — the umbrella epic.
- [docs/users/README.md](../../users/README.md) — the audience-facing entry point this decision created.
