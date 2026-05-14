---
id: TASK-093
title: Scaffold docs/users/tutorial/ and docs/users/examples/ with indexes
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
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

- [x] `docs/users/tutorial/` exists with `README.md` (index) and
      six empty step placeholders (`01` through `06`).
- [x] `docs/users/examples/` exists with `README.md` (gallery index)
      and five empty example sub-directories.
- [x] `docs/users/README.md` links to both indexes.
- [x] `markdownlint-cli2` passes on the new files.

## Outcome

Tutorial scaffold landed at `docs/users/tutorial/`: index `README.md`
with the full six-step roadmap (each row links to the corresponding
TASK-094 / TASK-095 step), plus six placeholder step files
(`01-minimal-circuit.md` through `06-layout-iteration.md`) carrying
only frontmatter (`status: placeholder`) + H1, ready for TASK-094 /
TASK-095 to fill.

Gallery scaffold landed at `docs/users/examples/`: index `README.md`
with the five-example gallery table linking each example to its
source task (TASK-096 through TASK-100), plus five placeholder
subdirectories with stub READMEs. Example directory names settled on
the kebab-case forms in the task body: `voltage-divider/`,
`common-emitter-amplifier/`, `555-monostable/`,
`opamp-non-inverting-buffer/`, `multi-page-split/`.

The audience landing page at `docs/users/README.md` already pointed
at both indexes from TASK-092; left untouched.

Lint: `markdownlint-cli2 "docs/users/**/*.md"` reports 0 errors
against the repo's `.markdownlint.json` config — the criterion the
task body specifies. The IDE's markdown extension warns about MD025
independently (it does not honour the repo config in the same way),
but the project's commit-hook and CI rely on cli2, which passes.

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
