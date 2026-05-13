---
id: TASK-089
title: Write the top-level coverage matrix with the PR-time/nightly/release axis
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: test-plan-and-coverage
order: 7
prerequisites: [TASK-085, TASK-086, TASK-087, TASK-088]
---

## Description

The per-subsystem chapters give a depth-first view. The matrix gives
the breadth-first view: every test in the inventory mapped to (a) the
subsystem(s) it covers, (b) the layer it lives at, and (c) the cadence
it runs at. The matrix is the *answer-in-one-page* artefact — a
contributor reading it should be able to spot redundancy ("two tests
cover the same case at different layers — is the slow one necessary?")
and gaps ("nothing covers the renderer at the property-test layer").

Output of this task is `docs/developers/testing/README.md` getting its
matrix table filled in (currently a placeholder from TASK-083) and a
short prose section explaining how to read the matrix and how to
update it.

Matrix shape — one row per test file, columns:

| Test file | Subsystems | Layer | PR | Nightly | Release | Notes |

Subsystems is a comma-separated list of the chapter slugs
(`schema`, `netgraph`, etc.); Layer is one of `unit`,
`integration`, `golden`, `property`, `e2e`. The cadence columns are
checkboxes (`PR ✓ / nightly ✓ / release ✓`). The Notes column is for
things that don't fit the schema — performance budgets, manual-only
caveats, "advisory" status.

The PR-time / nightly / release axis is the load-bearing part. It
should reflect:

- **PR-time** — what every contributor runs locally and what CI
  blocks on. Budget: under 5 minutes total.
- **Nightly** — what runs on a schedule and surfaces in the next
  morning's CI dashboard. Property tests with large iteration counts
  live here.
- **Release** — what runs only at `/release` time. KiCad
  spot-checks, PartsLedger round-trips, and other slow / manual
  steps.

The "hand-maintained vs generated from pytest markers" question
deferred from TASK-083 resolves here. **Default to hand-maintained
for v1**; revisit if the matrix grows past ~80 rows.

## Acceptance Criteria

- [ ] `docs/developers/testing/README.md` has a filled-in matrix
      with every test file from the inventory listed.
- [ ] PR-time / nightly / release cadence is set for every row,
      consistent with the per-subsystem chapters.
- [ ] A short prose paragraph at the top of the matrix explains the
      column conventions and the cadence policy (budgets per
      cadence, which gate runs which subset).
- [ ] The "hand-maintained for v1" decision is documented in the
      matrix's prose so future contributors don't reinvent the
      question.

## Test Plan

No automated tests required — change is non-functional (documentation).

Manual verification:

1. Cross-check the matrix row count against the inventory's test
   file count.
2. Pick three rows at random and verify the subsystem/layer tags
   match what the corresponding chapter says.
3. `markdownlint-cli2` passes; the wide table renders correctly
   under MD033 (HTML allowance) if any cells need `<br>` for
   wrapping.

## Prerequisites

- **TASK-085** — schema and netgraph chapter contents feed the matrix.
- **TASK-086** — layout kernel and router chapter contents feed the matrix.
- **TASK-087** — renderer and ERC chapter contents feed the matrix.
- **TASK-088** — exporters, orchestration, and CI-gates chapter contents feed the matrix.

## Notes

- The matrix is the artefact most likely to be referenced from the
  README and the ARCHITECTURE doc going forward — keep its top
  paragraph short and link-friendly.
- If the matrix exposes redundancy or gaps that warrant
  test-suite changes, **do not change tests in this task** — log
  them and let TASK-090 file them as concrete follow-up tasks.
