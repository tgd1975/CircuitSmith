---
id: EPIC-007
name: project-bootstrap
title: Project Bootstrap — Python Project Config and CI
status: open
opened: 2026-05-12
closed:
assigned:
branch: main
---

Phase 0 of the project: machine-readable Python project configuration and CI
scaffolding that the rest of the work assumes is in place.

Today the skill-packaging dossier declares dependencies (`schemdraw`,
`matplotlib`, `jsonschema`, `ruamel.yaml`) in prose, the `scripts/tests/`
test files run on whatever Python happens to be on PATH, and there is no
CI workflow. This epic closes that gap before EPIC-001 starts producing
the first real Python code.

Scope is deliberately narrow: project metadata + test runner config + a
minimal CI workflow that runs the same checks the pre-commit hook does.
Anything beyond that (release tagging, docs publishing, KiCad runners,
etc.) lives in later phases.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
