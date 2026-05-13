---
id: EPIC-006
name: circuit-skill-packaging
title: Circuit Skill — Skill Packaging and PyPI Publication
status: open
opened: 2026-05-12
closed:
assigned:
branch: release/epic-006-circuit-skill-packaging
---

Seeded by IDEA-001 (Circuit-Skill — AI-Assisted Schematic Generation with ERC, BOM, and Netlist Export).

**Rewritten 2026-05-13** under
[ADR-0012](../../adr/0012-library-as-installable-package.md) — the
delivery model changed from standalone-folder extraction to
installable Python package. The epic's intent ("ship the library so
other projects can use it without depending on CircuitSmith") is
unchanged; only the *mechanism* moved from folder-copy to
package-publish.

Two phases, paired because the second consumes the first:

- **Phase 6** — write `.claude/skills/circuit/SKILL.md` with the full
  system prompt and `allowed-tools` frontmatter, register in
  `.vibe/config.toml`, run the five acceptance tests (happy path, ERC
  error, BME280 over I2C, controller-swap to Raspberry Pi, incremental
  layout stability), finalise the skill `docs/`.
- **Phase 7** — publish the `circuitsmith` package to PyPI. Configure
  `python -m build` to produce a wheel + sdist; set up trusted
  publishing on PyPI (token-based fallback); write `RELEASING.md`
  documenting the tag-and-release flow; cut the first real `0.1.0`
  release. Consumers get the package via `pip install circuitsmith`;
  the skill folder stays in this repo as the agent-facing surface.

**Phase 7 prerequisite (soft).** Phase 6 acceptance passes and the
skill has been used on at least one real circuit addition in this
project. ADR-0012 decouples publication from real-circuit usage at
the *mechanism* level, but the version-bump from `0.1.0.dev0` to
`0.1.0` is still gated on real use — first-publication rough edges
should be discovered before a tagged release advertises stability.

Companion design doc:
[`idea-001.skill-packaging.md`](../../ideas/archived/idea-001.skill-packaging.md)
(original Phase 7 plan, now superseded for the extraction half) and
[`idea-002-consolidate-skill-python-into-central-module.md`](../../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md)
(the rewrite rationale and ADR-0012 reckoning).

## Retired tasks

The following tasks retire under ADR-0012 — the standalone-skill-repo
extraction path they implemented is obsolete:

- **TASK-043** (Create circuit-skill standalone GitHub repository) —
  no separate skill repo; the skill folder stays in this project.
- **TASK-044** (Extract skill commit history via `git subtree split`) —
  no extraction; nothing to subtree-split.
- **TASK-045** (Replace skill dir with pinned copy) — pinned folder
  copies are obsolete; the skill folder lives here.

All three are closed with status `closed` and a closure note pointing
at ADR-0012. The replacement is **TASK-080** below.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
