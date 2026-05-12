---
id: TASK-043
title: Create circuit-skill standalone GitHub repository
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Medium
human-in-loop: Main
epic: circuit-skill-packaging
order: 5
prerequisites: [TASK-041, TASK-042]
---

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
