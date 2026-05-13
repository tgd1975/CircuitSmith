---
id: TASK-044
title: Extract skill commit history via git subtree split; push as main
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: XS (<30m)
complexity: Senior
human-in-loop: Main
epic: circuit-skill-packaging
order: 6
prerequisites: [TASK-043]
---

## Closure note (2026-05-13)

Retired under [ADR-0012](../../adr/0012-library-as-installable-package.md).
The standalone-skill-repo extraction path that this task implemented
is obsolete: under ADR-0012 the skill folder stays in this repo and
the library is published as a PyPI package. There is no separate
repo to push history to, so there is nothing to `git subtree split`.

Superseded by **TASK-080** (`publish-circuitsmith-to-pypi`), which
ships the library through PyPI instead. See
[EPIC-006](epic-006-circuit-skill-packaging.md) § "Retired tasks"
and [`idea-002`](../../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md)
for the full reckoning.

The acceptance criteria below are preserved as historical record; do
not act on them.

## Autonomy

`Main` kept per TASK-060 sweep. Cross-repo git plumbing
(`git subtree split` / `git filter-repo`) plus a remote push —
agent prepares the exact commands and verifies them against a local
clone; user runs the final push.

## Description

Use `git subtree split` (or equivalent) to preserve the commit history
for `.claude/skills/circuit/` and push it as `main` in the standalone
repo created by TASK-043.

The split produces a branch whose history contains only commits that
touched `.claude/skills/circuit/`. Push that branch as `main` in the
standalone repo. Tag the first commit on the standalone repo as
`v0.1.0` to anchor the release history.

## Acceptance Criteria

- [ ] Standalone repo's `main` branch contains the full subtree-split history.
- [ ] `git log` in the standalone repo shows only commits that touched the skill — no project-noise commits.
- [ ] `v0.1.0` tag points to the head of `main` in the standalone repo.
- [ ] A `git diff` between this project's `.claude/skills/circuit/` and the standalone repo's root is empty (modulo `.gitignore` and similar).

## Test Plan

Manual verification: `git log --oneline` in the standalone repo shows the expected history; `diff -r` between the two locations is empty.

## Prerequisites

- **TASK-043** — standalone repo must exist.

## Notes

`git subtree split` can be slow on large histories — budget extra
time if the project's history grows significantly between Phase 6 and
Phase 7.
