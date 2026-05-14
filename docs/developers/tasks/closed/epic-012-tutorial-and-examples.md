---
id: EPIC-012
name: tutorial-and-examples
title: Tutorial and Example Gallery
status: open
opened: 2026-05-13
closed:
assigned:
branch: release/epic-012-tutorial-and-examples
---

Seeded by IDEA-004 (Tutorial and examples to show what CircuitSmith is capable of).

CircuitSmith today reads as a set of subsystems and a task plan.
A new contributor (or future-me reopening this in six months) has
no fast path to *seeing* what it produces. This epic ships the
"in-between" layer: a linear tutorial that walks from a minimal
`.circuit.yml` to a BOM-round-trip, and a curated gallery of
worked examples that double as regression fixtures.

Deliverables:

- **Tutorial** under `docs/users/tutorial/` — a six-step walkthrough,
  ~30 minutes end-to-end, split across two tasks (steps 1–3 and 4–6)
  to keep each commit's review surface manageable.
- **Example gallery** under `docs/users/examples/<name>/` — one
  directory per example with `.circuit.yml`, `.layout.yml`,
  `meta.yml`, the rendered SVG, and a short README explaining what
  makes the example interesting. Five seed examples: voltage divider,
  common-emitter amplifier, 555 monostable, op-amp non-inverting
  buffer, multi-page split.
- **CI regression diff** — examples are regenerated in CI; output
  drift fails the build. Both a contributor signal ("you changed
  something that affects rendering") and a regression net.
- **Docs structure decision** — where do user-facing docs live? The
  repo only has `docs/developers/` today. TASK-092 resolves this
  before anything else lands.

Cross-references with neighbouring epics:

- **EPIC-011 — test plan**: the example gallery is one of the
  regression-test layers documented in the renderer chapter
  (TASK-087) and the orchestration chapter (TASK-088).
  TASK-091 (staleness check) and TASK-101 (gallery diff) share the
  same job-naming convention.
- **EPIC-013 — post-EPIC-006 doc audit**: this epic supplies the
  worked-example layer that EPIC-013's TASK-106 (tutorial
  alignment) audits against the reference docs.

Ordering follows natural authoring sequence: structure decision →
scaffolding → tutorial halves → gallery items (smallest to largest
in complexity) → CI gate.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
