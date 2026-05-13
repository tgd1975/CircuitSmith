---
id: TASK-083
title: Scaffold docs/developers/testing/ directory and top-level index
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Junior
human-in-loop: Clarification
epic: test-plan-and-coverage
order: 1
---

## Description

The test plan needs a home before any of its per-subsystem chapters
can be authored. This task creates the directory structure, writes
the top-level index page (`docs/developers/testing/README.md`) with
the table of contents that subsequent tasks will fill in, and decides
the file-naming convention for subsystem chapters.

Decision to capture in the index:

- **One file per subsystem.** Multi-subsystem files balloon and
  attract drift; one file per subsystem keeps each plan independently
  ownable and reviewable.
- **Filename slug equals subsystem identifier.** `schema.md`,
  `netgraph.md`, `layout-kernel.md`, etc. — mirrors the Python module
  layout under `src/circuitsmith/` so a reader can navigate from code
  to plan by changing a path prefix.
- **Top-level matrix lives at the index.** The matrix is the entry
  point; chapters are referenced from it, not the other way around.

The index page is created with the structure but **empty chapter
placeholders**. Subsequent tasks fill those placeholders.

## Acceptance Criteria

- [ ] `docs/developers/testing/README.md` exists and links to placeholder
      chapter files (one per subsystem).
- [ ] Empty chapter files exist with frontmatter and an H1 only —
      `schema.md`, `netgraph.md`, `layout-kernel.md`, `router.md`,
      `renderer.md`, `erc-engine.md`, `exporters.md`,
      `skill-orchestration.md`, `ci-gates.md`.
- [ ] Index documents the naming convention and the "one file per
      subsystem" decision in a short prose paragraph.

## Test Plan

No automated tests required — change is non-functional (documentation
scaffolding).

Manual verification:

1. `markdownlint-cli2` passes on the new directory.
2. Every link in `README.md` resolves (verify with the project's
   existing link-check, or by visual inspection — the file count is
   small).

## Documentation

- `docs/developers/testing/README.md` — created here.
- `docs/developers/ARCHITECTURE.md` — should learn to point at the
  testing/ directory in its "How it's tested" sub-section. Defer the
  edit to TASK-107 (test-plan alignment in EPIC-013) to avoid double
  edits during the audit pass.

## Notes

- The decision on whether the plan is hand-maintained or generated
  from pytest markers is **deferred** to TASK-089 (the matrix task).
  Hand-maintained is the simpler default; the matrix task is where
  any generation tooling would attach.
- This task does not block on EPIC-006 closure — the testing/
  directory can exist even if the package surface keeps shifting,
  because individual chapters land later.
