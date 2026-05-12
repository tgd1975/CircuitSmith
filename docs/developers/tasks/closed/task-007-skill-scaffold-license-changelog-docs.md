---
id: TASK-007
title: Skill scaffolding — LICENSE, CHANGELOG, docs/index, docs/components
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-components
order: 7
---

## Description

Bootstrap the skill directory with the four non-code artefacts that the
standalone-repo extraction (EPIC-006 Phase 7) will require:

- `.claude/skills/circuit/LICENSE` — MIT, project copyright line.
- `.claude/skills/circuit/CHANGELOG.md` — initial entry recording v0.1
  scope from this epic.
- `.claude/skills/circuit/docs/index.md` — overview + install + link
  to the format reference.
- `.claude/skills/circuit/docs/components.md` — Phase 1 library
  reference and the profile authoring guide.

These ship from day one so the skill directory is self-contained and
portable to another project from the start (per the portability
contract in `idea-001-circuit-skill.md`).

## Acceptance Criteria

- [x] `LICENSE` (MIT) is present with the correct copyright holder. (Mirrors the host project's `LICENSE` — `Copyright (c) 2026 tgd1975` — so the skill directory remains internally consistent when extracted in EPIC-006.)
- [x] `CHANGELOG.md` has a v0.1 stub entry describing scope.
- [x] `docs/index.md` covers: what the skill is, how to install (clone or copy directory), and a one-paragraph "Hello, circuit" example.
- [x] `docs/components.md` documents the library shipped by TASK-001..004 and the profile authoring workflow.

## Test Plan

No automated tests required — these are documentation and licence artefacts. Visual smoke-check that the Markdown renders correctly in a GitHub preview.

## Notes

The full SKILL.md system prompt is a Phase 6 deliverable (EPIC-006
TASK-039) — this task ships only the supporting docs, not the prompt
itself.
