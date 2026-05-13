---
id: TASK-076
title: Write ADR-0012 (library as installable package) superseding ADR-0007
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Senior
human-in-loop: Main
epic: circuitsmith-package
order: 1
---

## Description

Phase 1 of EPIC-010. The only non-mechanical phase of the refactor —
sets the new delivery contract on paper before any code moves.

Three sub-deliverables, all documentation:

- **Write ADR-0012.** Status: Accepted. Supersedes ADR-0007.
  Decision: the library is `pip install circuitsmith`; the skill
  folder ships agent-facing prompts (and optional thin shims) only.
  The no-host-project-imports invariant survives, now scoped to
  `src/circuitsmith/` rather than `.claude/skills/circuit/`.
- **Mark ADR-0007 superseded.** Status field → `Superseded by ADR-0012`.
  Add a `## Supersession` section forward-linking to ADR-0012.
  Do not delete ADR-0007 — provenance matters.
- **Rewrite EPIC-006 in place.** Replace its Phase 7 (folder-copy
  extraction) with the PyPI publication path:
  `python -m build`, trusted publishing setup, write `RELEASING.md`,
  publish `0.1.0`. Add a new sub-task to EPIC-006 for the
  publication mechanics (scoped to land after this refactor's
  squash-merge). Retire TASK-045
  (`replace-skill-dir-with-pinned-copy`) — pinned folder copies are
  obsolete under ADR-0012. Drop the Phase 6 → Phase 7 prerequisite
  chain inherited from ADR-0007.
- **Update TASK-050 scope.** The "boundary" of the boundary import
  contract test is now `src/circuitsmith/`, not
  `.claude/skills/circuit/`. The contract itself is unchanged.

This task is the **stop-line for EPIC-010**. User sign-off on
ADR-0012 + the EPIC-006 rewrite decision is required before
TASK-077 (the atomic relocation) begins.

## Acceptance Criteria

- [x] `docs/developers/adr/0012-library-as-installable-package.md`
      exists, Status: Accepted, follows the ADR template.
- [x] [ADR-0007](../../adr/0007-skill-directory-is-the-library.md)
      is marked `Superseded by ADR-0012` with a `## Supersession`
      section forward-linking to the new ADR.
- [x] [EPIC-006](epic-006-circuit-skill-packaging.md) body is
      rewritten: Phase 7 reframed as PyPI publication; new
      publication sub-task (TASK-080) added; TASK-045 retired (and
      TASK-043 / TASK-044 by extension — all three named in
      EPIC-006 § "Retired tasks" with closure notes pointing at
      ADR-0012); Phase 6 → Phase 7 prerequisite chain dropped (the
      hard prereq; the soft "real-circuit use" gate survives on the
      `0.1.0.dev0 → 0.1.0` version bump only).
- [x] [TASK-050](../open/task-050-boundary-import-contract-test.md)
      body updated to scope the boundary as `src/circuitsmith/`.

## Test Plan

No automated tests required — change is documentation only.
Manual verification: `markdownlint-cli2 --fix` clean on all four
modified/created files; ADR cross-links resolve.

## Notes

The idea body in
[`docs/developers/ideas/archived/idea-002-consolidate-skill-python-into-central-module.md`](../../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md)
§ "ADR-0007 reckoning" and § "Phase 1" carries the full
rationale and the four bullet points the new ADR must capture.
