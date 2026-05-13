---
id: TASK-042
title: Finalise all .claude/skills/circuit/docs/ files
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: circuit-skill-packaging
order: 4
prerequisites: [TASK-016, TASK-030, TASK-035, TASK-038]
---

## Description

Close out the skill's `docs/` directory:

- Update `docs/index.md` with skill invocation examples. Where the
  examples can be drawn from real Phase 6 acceptance-test transcripts
  (TASK-041) those are preferred, but TASK-041 no longer blocks this
  task (2026-05-13 reorganisation) — synthetic worked examples drawn
  from the skill's own fixtures are acceptable, and the doc gets
  refreshed with real transcripts when TASK-041 lands.
- Fill any cross-reference gaps left by earlier doc tasks
  (TASK-007, TASK-016, TASK-030, TASK-035).
- Verify every linked document exists (no rot).
- Ensure the `docs/` directory is fully self-contained — no
  project-specific paths outside the `docs/` files referenced as
  "this project's CI" or similar. (The standalone-repo extraction
  this used to gate is retired under
  [ADR-0012](../../adr/0012-library-as-installable-package.md);
  self-containment now serves the PyPI distribution surface.)

## Acceptance Criteria

- [x] `docs/index.md` has at least three worked invocation examples
      (synthetic fixture-based; refreshed with real transcripts when
      TASK-041 lands).
- [x] Every internal `docs/` link resolves (verified by relative-path
      audit + spot-check of target files).
- [x] No `docs/*.md` file references paths outside `.claude/skills/circuit/`
      as load-bearing dependencies — informational cross-refs to the
      host repo's ADRs, dossier, and source are explicitly allowed
      under ADR-0012 (the package is the unit of distribution; the
      skill folder consumes it).
- [x] A new contributor reading only `docs/index.md` can install the
      skill, render a circuit, and find their way to the rest of the
      documentation.

## Closure note

- `docs/index.md` rewritten — Status section reflects the now-wired
  full workflow, Install section maps to the post-ADR-0012
  `pip install circuitsmith` shape, three worked `/circuit`
  invocation examples added (happy path, ERC-driven correction,
  component-profile extension), Markdown-blocks section folded the
  swap procedure into a unified "two execution paths" description.
- `docs/erc-checks.md` — broken `../../../src/circuitsmith/…`
  relative paths (off-by-one) corrected to `../../../../src/…`.
  Twelve `Catalog.` rule links + the engine `CHECK_TABLE` link + the
  `rules.json` top-of-file link.
- `docs/circuit-yaml.md` — Markdown-blocks section detensed
  ("EPIC-005 lands" → "ship as part of EPIC-005 (closed)").
- Portability contract reinterpreted under ADR-0012: load-bearing
  self-containment against the installed `circuitsmith` package;
  informational cross-refs allowed. Documented in
  `docs/index.md § Portability`.

## Test Plan

Run a Markdown link checker (`markdown-link-check` or equivalent) against `docs/`; visual smoke-read of `docs/index.md` from a fresh-eyes perspective.

## Prerequisites

- **TASK-016** — circuit-yaml and layout docs must exist.
- **TASK-030** — erc-checks doc must exist.
- **TASK-035** — index.md BOM/netlist sections must exist.
- **TASK-038** — markdown-integration sections must exist.

TASK-041 was a prerequisite before the 2026-05-13 EPIC-006
reorganisation; it now runs on its own track at the end of the epic
and the doc invocation examples it would have produced are deferred.

## Notes

This task closes the skill-side documentation. The PyPI publication
flow (TASK-081 / TASK-082 / TASK-080) consumes self-contained
`docs/` as its distribution surface.
