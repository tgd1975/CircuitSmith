---
id: TASK-093
title: Scaffold docs/users/tutorial/ and docs/users/examples/ with indexes
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Junior
human-in-loop: Clarification
epic: tutorial-and-examples
order: 2
prerequisites: [TASK-092]
---

## Description

With the user-docs home decided in TASK-092, create the two
sub-directories that the rest of the epic will populate:

- `docs/users/tutorial/` — a linear walkthrough. Lay it out as a
  numbered series of files (`01-minimal-circuit.md`,
  `02-fan-out.md`, etc.) with a `README.md` that is the entry
  point and table of contents.
- `docs/users/examples/` — a flat gallery. Each example gets its
  own sub-directory (`voltage-divider/`, `common-emitter-amplifier/`,
  etc.); the parent `README.md` is the gallery index with one row
  per example.

Specifics:

- **Tutorial index** lists all six step files with their titles and
  one-line summaries. Step files themselves are empty placeholders
  (frontmatter + H1 only) — they fill up in TASK-094 and TASK-095.
- **Examples index** is a table: example name, what it demonstrates,
  link to the example's README. Empty example dirs are placeholders
  for TASK-096 through TASK-100.
- The `docs/users/README.md` (created in TASK-092) gets its links
  updated to point at the two indexes.

Naming conventions to lock in:

- **Tutorial step files**: `NN-slug.md` where `NN` is two-digit,
  matching the tutorial's step order. Two-digit gives us headroom
  if a step needs to split later.
- **Example directories**: kebab-case, descriptive (not
  `example-1/`; full `voltage-divider/`).

## Acceptance Criteria

- [ ] `docs/users/tutorial/` exists with `README.md` (index) and
      six empty step placeholders (`01` through `06`).
- [ ] `docs/users/examples/` exists with `README.md` (gallery index)
      and five empty example sub-directories.
- [ ] `docs/users/README.md` links to both indexes.
- [ ] `markdownlint-cli2` passes on the new files.

## Test Plan

No automated tests required — change is non-functional (scaffolding).

Manual verification:

1. Every link in the three new index files resolves.
2. The empty step placeholders are valid markdown (frontmatter +
   H1 only) — they should not trigger MD041 "first line H1" or
   MD025 "duplicate H1" issues.

## Prerequisites

- **TASK-092** — the `docs/users/` location must be decided before
  the sub-directories can be created.

## Notes

- The `NN-slug.md` numbering is deliberate. A flat index of named
  files works for a small list, but the tutorial *is* a linear
  sequence and the numeric prefix makes the order machine-derivable
  for any tooling that walks the directory.
- Empty placeholders are a compromise. They produce a slightly
  noisy `git status` between TASK-093 and TASK-094, but they let
  the index file be authored complete-with-links from the start,
  which is the bigger correctness win.
