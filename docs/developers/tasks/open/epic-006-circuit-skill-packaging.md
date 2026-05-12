---
id: EPIC-006
name: circuit-skill-packaging
title: Circuit Skill — Skill Packaging and Standalone Extraction
status: open
opened: 2026-05-12
closed:
assigned:
branch: release/epic-006-circuit-skill-packaging
---

Seeded by IDEA-001 (Circuit-Skill — AI-Assisted Schematic Generation with ERC, BOM, and Netlist Export).

Phases 6 and 7 of IDEA-001, paired because the second consumes the
first:

- **Phase 6** — write `.claude/skills/circuit/SKILL.md` with the full
  system prompt and `allowed-tools` frontmatter, register in
  `.vibe/config.toml`, run the five acceptance tests (happy path, ERC
  error, BME280 over I2C, controller-swap to Raspberry Pi, incremental
  layout stability).
- **Phase 7** — extract `.claude/skills/circuit/` to its own GitHub
  repository, preserve commit history via `git subtree split`, replace
  the skill directory in this project with a pinned directory copy
  (default — submodule only if the standalone repo ships on an
  independent release cadence), update doc links, write `RELEASING.md`.

**Phase 7 prerequisite:** Phase 6 acceptance test passes and the skill
has been used on at least one real circuit addition in this project.
Extraction before real use risks shipping rough edges discovered only
in practice.

Companion design doc:
`docs/developers/ideas/archived/idea-001.skill-packaging.md`.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
