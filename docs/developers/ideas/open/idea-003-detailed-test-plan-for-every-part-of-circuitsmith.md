---
id: IDEA-003
title: Detailed test plan for every part of CircuitSmith
description: Detailed test plan covering every CircuitSmith subsystem
category: 🛠️ tooling
---

A single, structured test plan that enumerates **what** to test, **how**
to test it, and **at what layer** for every subsystem in CircuitSmith.
The aim is to convert today's organically grown test suite into a
deliberate matrix where coverage gaps are visible and intentional, not
accidental.

## Motivation

The codebase is currently a set of subsystems — schema, netgraph,
layout kernel, Manhattan router, renderer, ERC engine, BOM, future
plugins — wired together by skill scripts and CI. Each has its own
notion of "tested": some have unit tests, some have golden fixtures,
some are exercised only end-to-end. There is no single place a
contributor can read to answer *"how is the router tested? what cases
are deliberately uncovered? what's an acceptable PR-time check?"*

This idea is to write that document — and then close the gaps it
exposes.

## Rough approach

- One section per subsystem (schema validation, netgraph build,
  layout kernel, router, renderer, ERC, BOM export, skill orchestration,
  CI gates).
- For each subsystem, capture:
  - **Inputs / outputs** the test must pin down.
  - **Unit-level tests** (pure functions, edge cases, error paths).
  - **Integration-level tests** (subsystem + its immediate neighbours).
  - **Golden / snapshot tests** (canonical `circuit.yml` ↔ rendered
    `layout.yml` / SVG pairs).
  - **Property / fuzz tests** where the input space is large
    (router on randomised netlists, layout on stress topologies).
  - **Performance budget** if any (e.g. router runtime on N-component
    circuits).
  - **Known uncovered cases** with rationale.
- A top-level matrix that maps every test to the subsystem it covers
  and the layer it lives at — useful for spotting redundant tests and
  missing coverage in the same view.
- A "PR-time vs nightly vs release" axis: not every test belongs in
  the fast feedback loop.

## Open questions

- Where does this live? A single `docs/developers/TEST_PLAN.md`, or
  one file per subsystem under `docs/developers/testing/`?
- Should the plan be hand-maintained, or generated from
  pytest markers / fixture metadata?
- How do we keep the plan from drifting? CI check that flags new
  test files not referenced in the plan?
- Relationship to the v0.1 structural rubric — the rubric is a
  *quality* check on generated layouts; this is a *correctness* check
  on the code that generates them. They should cross-reference.
