---
id: TASK-086
title: Author the layout-kernel and Manhattan-router subsystem test plans
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: test-plan-and-coverage
order: 4
prerequisites: [TASK-084]
---

## Description

Fill in `docs/developers/testing/layout-kernel.md` and
`docs/developers/testing/router.md`.

These two subsystems carry the bulk of the layout-engine's complexity
and the bulk of its property-test surface area. The router in
particular operates on randomised netlists; the chapter must capture
which property invariants are checked (no self-crossing, all nets
routable, Manhattan grid alignment) and which are *intentionally not*
checked (asymptotic optimality, aesthetic quality).

Same structural template as TASK-085 (inputs/outputs, unit,
integration, golden, property/fuzz, performance budget, known
uncovered, PR-time/nightly/release).

Additional specifics for these two chapters:

- **Layout kernel** — the v0.1 structural rubric tests (TASK-011)
  are layout-kernel territory; reference them from this chapter and
  document the rubric's role as "structural correctness post-place".
- **Router** — performance budget is real and worth pinning down.
  The router has a known degenerate input class (high-fan-out nets
  on small grids); document it as a known-uncovered or
  known-slow-path case rather than pretending it doesn't exist.
- **AI placer convergence loop** (TASK-017) — this is layout-kernel
  territory; include a sub-section on how convergence is tested and
  how reason-code emission is verified.

## Acceptance Criteria

- [ ] `layout-kernel.md` and `router.md` are no longer empty
      placeholders and follow the canonical chapter structure.
- [ ] Property tests are enumerated with their invariants spelled out.
- [ ] Router chapter includes the performance budget (current runtime
      on the canonical fixtures + the budget we refuse to exceed).
- [ ] AI placer convergence testing is documented under
      `layout-kernel.md` (reason-code emission, convergence iteration
      cap, --no-ai fallback path from TASK-018).
- [ ] Every "known uncovered" item has a one-sentence rationale.

## Test Plan

No automated tests required — change is non-functional (documentation).

Manual verification:

1. Spot-check 2-3 property tests by reading the source and confirming
   the invariant list in the chapter matches the assertions.
2. Run the router on the canonical fixtures and confirm the
   "current runtime" number in the chapter is accurate to within ~20%.
3. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-084** — the inventory is the raw material.

## Notes

- The layout kernel and the router are split into two chapters
  because they have meaningfully different test shapes (kernel is
  mostly golden tests; router is mostly property tests). Combining
  them would hide that asymmetry.
- The AI placer is a sub-system of the layout kernel from the
  pipeline-stage perspective but has its own complexity profile
  (LLM-call-dependent, convergence-driven). The chapter explicitly
  flags this and notes which tests are deterministic vs which need
  the `--no-ai` fallback to be PR-time-safe.
