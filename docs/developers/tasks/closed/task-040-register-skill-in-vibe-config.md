---
id: TASK-040
title: Register circuit skill in .vibe/config.toml enabled_skills
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: XS (<30m)
effort_actual: XS (<30m)
complexity: Junior
human-in-loop: No
epic: circuit-skill-packaging
order: 2
prerequisites: [TASK-039]
---

## Description

Add `circuit` to the `enabled_skills` list in
[.vibe/config.toml](.vibe/config.toml). Per CLAUDE.md ("Skill
registration"), every new `.claude/skills/<name>/SKILL.md` requires a
matching entry in this list — no entry, no invocation.

## Acceptance Criteria

- [x] `.vibe/config.toml` contains `circuit` in `enabled_skills`.
- [x] `/circuit` is invocable from a Claude Code session after this change.
- [x] No other skill is accidentally disabled by the edit.

## Test Plan

Manual: open a Claude Code session in this repo and invoke `/circuit`; confirm the skill loads. No automated test (skill registration is harness-level, not project logic).

## Prerequisites

- **TASK-039** — `SKILL.md` must exist before registration makes sense.

## Notes

Trivial task by design — separated from TASK-039 so the registration
edit is reviewable on its own.
