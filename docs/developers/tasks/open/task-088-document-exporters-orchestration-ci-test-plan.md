---
id: TASK-088
title: Author the exporters, skill-orchestration, and CI-gates subsystem test plans
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Medium
human-in-loop: Clarification
epic: test-plan-and-coverage
order: 6
prerequisites: [TASK-084]
---

## Description

Fill in three chapters:

- `docs/developers/testing/exporters.md` — covers the BOM exporter
  (TASK-031) and the KiCad netlist exporter (TASK-033), plus the
  structural KiCad netlist test (TASK-049) and any round-trip checks.
- `docs/developers/testing/skill-orchestration.md` — covers
  `.claude/skills/circuit/` end-to-end behaviour and the
  Markdown-block integration (TASK-036, TASK-037).
- `docs/developers/testing/ci-gates.md` — covers the staleness
  guards (TASK-029, TASK-035), the schema-validation pre-commit
  (TASK-052), the portability lint (TASK-051), the boundary-import
  contract test (TASK-050), and the Phase 2b trigger gate
  (TASK-058, TASK-059).

Each chapter follows the canonical structure. Specific items to call
out:

- **Exporters chapter** — BOM round-trip into PartsLedger is a
  manual test today (no automation against the external repo).
  Document the manual procedure and the case for / against
  automating it once EPIC-012's PartsLedger round-trip example
  ships.
- **Skill-orchestration chapter** — distinguish "the agent prompt
  produces sensible output" (out of scope; agent behaviour is not
  test-pinnable) from "the skill's deterministic post-processing
  steps produce correct output" (in scope; pinnable). Be explicit
  about this boundary.
- **CI-gates chapter** — for each gate, document the failure mode
  (what it looks like to the contributor when the gate fires) and
  the bypass mechanism (if any, e.g. `CS_PHASE2B_BYPASS`,
  `CS_COMMIT_BYPASS`).

## Acceptance Criteria

- [ ] All three chapter files are filled in and follow the canonical
      structure.
- [ ] Exporters chapter documents the PartsLedger round-trip as a
      known manual step (not an uncovered gap).
- [ ] Skill-orchestration chapter draws the explicit boundary
      between agent-prompt behaviour (out of scope) and
      post-processing determinism (in scope).
- [ ] CI-gates chapter has one sub-section per gate listing failure
      mode and bypass mechanism.

## Test Plan

No automated tests required — change is non-functional (documentation).

Manual verification:

1. For each CI gate, trigger it intentionally in a throwaway commit
   and confirm the failure-mode description in the chapter matches
   what the contributor sees.
2. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-084** — the inventory is the raw material.

## Notes

- These three subsystems are batched into one task because each is
  small (one or two test files), and the chapter shapes are very
  similar. Splitting them would produce three tiny tasks that all
  forward-reference the same inventory.
- The CI-gates chapter is the one that contributors will read most
  often when a build fails on `main`. Keep the failure-mode prose
  oriented to "what does it look like and how do I fix it" rather
  than "what is the gate's design rationale" — the latter belongs in
  the relevant ADR or epic.
