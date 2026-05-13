---
id: TASK-084
title: Inventory the existing test surface and tag every test by subsystem and layer
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Medium
human-in-loop: Clarification
epic: test-plan-and-coverage
order: 2
prerequisites: [TASK-083]
---

## Description

Before any subsystem chapter can be authored, we need a flat list of
every test that currently exists in the repo, tagged with the
subsystem it covers (schema / netgraph / layout-kernel / router /
renderer / erc / exporters / skill-orchestration / ci-gates) and the
layer it lives at (unit / integration / golden / property / e2e).

Output of this task is a single working artefact —
`docs/developers/testing/_inventory.md` (prefixed with `_` so the
README does not link to it as a chapter) — that lists, for each
`tests/test_*.py` file and each on-device or fixture-based test:

- File path.
- The subsystem(s) it exercises (one or more).
- The test layer (unit / integration / golden / property / e2e).
- A one-line summary of what it pins down (taken from the test's
  docstring or its `def test_*` names).
- Whether it runs at PR time, nightly, or only on release.

The inventory is **input** to TASK-085 through TASK-088 (per-subsystem
chapters) and TASK-089 (top-level matrix). It is not user-facing and
can be deleted once the matrix is authoritative — but keeping it
around as a working document is cheap and makes the audit re-runnable.

## Acceptance Criteria

- [ ] `_inventory.md` exists and lists every test file currently in
      the repo.
- [ ] Each entry has at least one subsystem tag and one layer tag.
- [ ] PR-time vs nightly vs release classification is filled in for
      every entry (defer to "PR-time" unless the test is gated behind
      a CI variable or fixture marker).

## Test Plan

No automated tests required — change is non-functional (working
document).

Manual verification:

1. Cross-check the inventory against the output of
   `find tests/ -name 'test_*.py'` (or the equivalent for any
   on-device test directories) and confirm no test file is missing.
2. Spot-check 3-4 entries by reading the source file and confirming
   the subsystem/layer tags are accurate.

## Prerequisites

- **TASK-083** — provides the directory the inventory lives in.

## Notes

- This task is deliberately separate from the per-subsystem chapters
  because the inventory is a *cross-cutting* artefact — splitting it
  across chapters would lose the "every test in one place" view that
  is the matrix's raw material.
- If the inventory exposes tests whose subsystem is ambiguous (e.g.
  an end-to-end test that exercises the whole pipeline), tag with
  multiple subsystems and let TASK-089 resolve overlap in the matrix.
- The `_` prefix on the filename is deliberate. `housekeep.py` does
  not touch testing/, but the README chapter index will iterate
  alphabetically; underscore-prefixed files are conventionally hidden
  from such indexes.
