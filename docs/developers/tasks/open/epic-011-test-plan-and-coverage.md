---
id: EPIC-011
name: test-plan-and-coverage
title: Test Plan and Coverage Matrix
status: open
opened: 2026-05-13
closed:
assigned:
branch: release/epic-011-test-plan-and-coverage
---

Seeded by IDEA-003 (Detailed test plan for every part of CircuitSmith).

Convert today's organically grown test suite into a deliberate matrix
where coverage gaps are visible and intentional, not accidental. The
test code already exists; what is missing is a single document a
contributor can read to answer *"how is the router tested? what cases
are deliberately uncovered? what's an acceptable PR-time check?"*

The epic ships one structured directory under
`docs/developers/testing/` — a per-subsystem set of plans plus a
top-level coverage matrix — and the CI guardrail that prevents the
plan from drifting away from the actual test surface.

Scope and shape:

- **One section per subsystem.** Schema validation, netgraph build,
  layout kernel, Manhattan router, renderer, ERC engine, BOM/netlist
  exporters, skill orchestration, CI gates. Each captures inputs and
  outputs, unit/integration/golden/property-test layers, performance
  budgets where they exist, and *known uncovered cases with rationale*.
- **A top-level matrix.** Every test mapped to the subsystem it covers
  and the layer it lives at — useful for spotting redundancy and gaps
  in the same view. Includes the PR-time / nightly / release axis so
  the fast feedback loop is explicit.
- **Coverage-gap triage.** The plan exposes gaps; the epic files them
  as concrete follow-up tasks rather than burying them inline.
- **CI staleness guard.** New test files that appear in the tree
  without a corresponding plan entry fail the gate. Same shape as the
  existing erc-report staleness check (TASK-029).

Relationships to neighbouring epics:

- **EPIC-012 — tutorial and gallery** cross-references the example
  gallery from the test plan, since the gallery doubles as a
  regression suite. Coordination happens at TASK-101 (CI regression
  diff) ↔ TASK-091 (staleness check).
- **EPIC-013 — post-EPIC-006 doc audit** picks up the
  "how it's tested" sections in narrative docs and verifies they match
  the plan written here (TASK-107).

Ordering inside the epic mirrors the natural pipeline: scaffold →
inventory → per-subsystem plans → matrix → gap triage → CI guard.
TASK-090 (gap triage) is deliberately last among the documentation
work because it can only happen *after* the plans expose the gaps.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
