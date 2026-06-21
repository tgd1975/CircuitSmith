# Test plan and coverage matrix

This directory is CircuitSmith's **deliberate** test plan: one chapter
per subsystem plus a top-level coverage matrix, so a contributor can
answer *"how is the router tested? what cases are deliberately
uncovered? what is an acceptable PR-time check?"* from a single place.

It is the breadth-and-depth companion to
[`../TESTING.md`](../TESTING.md), which covers the *conventions* — test
layers, framework choice, fixture layout, how to write and run a test.
Read `TESTING.md` to learn **how** we test; read this directory to learn
**what** is tested, **where**, and **what is intentionally not**.

> **Status.** Seeded by EPIC-011. The chapters below are authored across
> TASK-085..088; the matrix is filled in by TASK-089; the CI staleness
> guard that keeps this plan honest lands in TASK-091.

## How this directory is organised

- **One file per subsystem.** Multi-subsystem files balloon and attract
  drift; one file per subsystem keeps each plan independently ownable
  and reviewable.
- **Filename slug equals the subsystem identifier**, mirroring the
  Python module layout under [`../../../src/circuitsmith/`](../../../src/circuitsmith/)
  so a reader can navigate from code to plan by changing a path prefix
  (`src/circuitsmith/netgraph.py` → `testing/netgraph.md`).
- **The matrix lives here, at the index.** It is the entry point;
  chapters are referenced from it, not the other way around.

Each chapter carries a small frontmatter block declaring the subsystem
slug and the code it covers, followed by an H1 and the canonical
chapter structure:

```yaml
---
subsystem: <slug>
covers: <module path(s) the chapter pins down>
---
```

The canonical chapter structure (every chapter uses these headings,
noting "none" explicitly rather than omitting a heading):

1. Inputs / outputs the tests pin down
2. Unit tests
3. Integration tests
4. Golden / snapshot tests
5. Property / fuzz tests
6. Performance budget
7. Known uncovered cases (each with a one-sentence rationale)
8. PR-time / nightly / release cadence

## Subsystem chapters

| Subsystem | Chapter | Covers |
|---|---|---|
| Schema validation | [`schema.md`](schema.md) | `src/circuitsmith/schema/` + rule-catalog validation |
| NetGraph | [`netgraph.md`](netgraph.md) | `src/circuitsmith/netgraph.py` |
| Layout kernel | [`layout-kernel.md`](layout-kernel.md) | `src/circuitsmith/layout/{kernel,rubric,ai_placer}.py` |
| Manhattan router | [`router.md`](router.md) | `src/circuitsmith/layout/router.py` |
| Renderer | [`renderer.md`](renderer.md) | `src/circuitsmith/renderer.py` |
| ERC engine | [`erc-engine.md`](erc-engine.md) | `src/circuitsmith/erc_engine.py` + `knowledge/` |
| Exporters | [`exporters.md`](exporters.md) | `src/circuitsmith/export/` |
| Skill orchestration | [`skill-orchestration.md`](skill-orchestration.md) | `.claude/skills/circuit/` + `markdown.py` |
| CI gates | [`ci-gates.md`](ci-gates.md) | `scripts/check_*.py`, pre-commit, CI workflow |

The working inventory the chapters are built from lives at
[`_inventory.md`](_inventory.md) (underscore-prefixed so it is not a
chapter). It is a cross-cutting list of every test file tagged by
subsystem, layer, and cadence — raw material for the chapters and the
matrix, safe to delete once the matrix is authoritative.

## Coverage matrix

<!-- MATRIX:START — filled in by TASK-089. -->

*Placeholder.* The top-level matrix — every test file mapped to the
subsystem(s) it covers, the layer it lives at, and the cadence it runs
at (PR-time / nightly / release) — is authored in TASK-089 once the
per-subsystem chapters exist. The column shape will be:

| Test file | Subsystems | Layer | PR | Nightly | Release | Notes |
|---|---|---|---|---|---|---|

<!-- MATRIX:END -->
