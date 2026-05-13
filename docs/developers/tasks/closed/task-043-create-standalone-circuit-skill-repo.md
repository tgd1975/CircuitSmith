---
id: TASK-043
title: Create circuit-skill standalone GitHub repository
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Small (<2h)
effort_actual: XS (<30m)
complexity: Medium
human-in-loop: Main
epic: circuit-skill-packaging
order: 5
prerequisites: [TASK-041, TASK-042]
---

## Closure note (2026-05-13)

Retired under [ADR-0012](../../adr/0012-library-as-installable-package.md).
The standalone-skill-repo extraction path that this task implemented
is obsolete: under ADR-0012 the library is published as a PyPI
package (`circuitsmith`) from this repo, and the skill folder at
`.claude/skills/circuit/` stays here as the agent-facing surface.
There is no separate skill repo to create.

Superseded by **TASK-080** (`publish-circuitsmith-to-pypi`), which
ships the library through PyPI instead. See
[EPIC-006](epic-006-circuit-skill-packaging.md) § "Retired tasks"
and [`idea-002`](../../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md)
for the full reckoning.

The acceptance criteria below are preserved as historical record; do
not act on them.

## Autonomy

`Main` kept per TASK-060 sweep. Standalone-repo creation is a
cross-system action with remote-push effects — auto-prepare the
directory contents; user creates the GitHub repo and runs the
initial push.

## Description

Create a new GitHub repository for the standalone circuit skill.
Per `idea-001-circuit-skill.md §Phase 7`:

- **Prerequisite**: Phase 6 acceptance passes AND the skill has been
  used on at least one real circuit addition in this project.
- **Naming**: `circuit-skill` is the working name; the user picks the
  final repo name (TBD per the idea).
- **Initial state**: empty repo with default README placeholder; no
  history yet (TASK-044 imports history).

## Acceptance Criteria

- [ ] Repository created on GitHub under the user's namespace with a chosen name.
- [ ] Repository description matches the skill's `SKILL.md` `description` field.
- [ ] License is set to MIT in the repo metadata.
- [ ] Repository visibility decision (public/private) recorded in `RELEASING.md` (TASK-045).

## Test Plan

Manual verification: repo exists, settings are correct, the user has admin access. No automated test.

## Prerequisites

- **TASK-041** — Phase 6 acceptance tests must pass.
- **TASK-042** — docs must be self-contained.

## Notes

The pre-flight "real-world use" prerequisite is not strictly testable
— the maintainer decides when "at least one real circuit addition"
has happened, based on PR history since TASK-041 closure.
