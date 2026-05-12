---
id: TASK-051
title: Portability lint for .claude/skills/circuit/
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: architecture-fitness-functions
order: 2
prerequisites: []
---

## Description

The dossier's
[portability contract](../../ideas/archived/idea-001-circuit-skill.md#architecture)
states that scripts inside `.claude/skills/circuit/` are path-agnostic:
they accept input and output paths as arguments and have no hardcoded
references to this project's directory layout. That contract is the
reason Phase 7 ([EPIC-006](epic-006-circuit-skill-packaging.md)
TASK-043–045) extraction is mechanical rather than a port.

Today the contract is enforced only by review. A single hardcoded path
inserted during Phases 1–6 would silently break standalone extraction
months later. This task adds the mechanical check:
`scripts/portability_lint.py` scans the skill directory and rejects
forbidden patterns at commit and CI time.

Forbidden patterns:

- Absolute paths that match the host project (`/home/`, `C:\`, `~/Dokumente`).
- Imports referencing top-level project modules (`from scripts.…`,
  `from data.…`, anything under the project root that is not the skill's
  own package).
- Hardcoded references to project-specific data paths
  (`docs/builders/`, `data/`, the project name `CircuitSmith`).
- Hardcoded references to sibling project names (`AwesomeStudioPedal`,
  `PartsLedger`) outside `docs/` files.

A `.portability-allow.txt` in the skill directory carries genuine
exceptions, each line a `<file>:<pattern>:<reason>` triple.

## Acceptance Criteria

- [ ] `scripts/portability_lint.py` exists, takes the skill directory as its argument, exits 0 if clean and non-zero with a list of findings if not.
- [ ] Runs as part of the pre-commit hook framework on staged changes inside the skill directory.
- [ ] Runs in CI (the GitHub Actions workflow from TASK-048) as an unconditional check.
- [ ] Allow-list mechanism (`.portability-allow.txt`) works and requires a per-entry reason.
- [ ] `tests/test_portability_lint.py` feeds a fixture directory with seeded violations and asserts the lint catches each.

## Test Plan

Fixture-based: `tests/fixtures/portability-bad/` contains files with
each forbidden pattern; the lint is run against the fixture and the
output is asserted to contain each expected finding. A second fixture
(`portability-good/`) asserts the clean path returns exit 0.

## Prerequisites

None — the lint can be authored before `.claude/skills/circuit/`
contains any code. On an empty tree it is a no-op. The point is to
have the guardrail in place *before* files arrive, not after.

## Notes

Pairs with [EPIC-006](epic-006-circuit-skill-packaging.md) Phase 7
(TASK-043–045). If this lint stays green throughout Phases 1–6, the
dossier's promise that extraction is "mechanical" holds.

Mechanical extraction is the test of whether the architecture's
"self-contained skill IS the library" pattern actually worked.
