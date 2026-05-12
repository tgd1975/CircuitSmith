---
id: TASK-044
title: Extract skill commit history via git subtree split; push as main
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Main
epic: circuit-skill-packaging
order: 6
prerequisites: [TASK-043]
---

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
