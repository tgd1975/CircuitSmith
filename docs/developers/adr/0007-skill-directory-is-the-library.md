---
id: ADR-0007
title: The skill directory is the library; portability contract holds
status: Accepted
date: 2026-05-12
dossier-section: idea-001.skill-packaging.md
---

## Context

Phase 7 of the roadmap (EPIC-006) extracts the renderer / ERC /
exporters into a standalone Claude Code skill repository so other
projects can use them without depending on CircuitSmith. Two
architectures could support that:

- **Library + skill wrapper** — the Python code lives as a normal
  package (`src/circuitsmith/...`), and the skill is a thin SKILL.md
  that imports from it. Phase 7 publishes the package to PyPI and
  the skill points at the published version.
- **Skill *is* the library** — the Python code lives inside
  `.claude/skills/circuit/` and is path-agnostic. Phase 7 is then a
  mechanical `cp -r .claude/skills/circuit /elsewhere/` — no port,
  no refactor, no decoupling pass.

The second option only works if every file inside
`.claude/skills/circuit/` is portable from day one: no hard-coded
project paths, no imports of modules outside the skill, no references
to sibling project names.

## Decision

The skill **is** the library. All renderer / ERC / exporter code
lives under `.claude/skills/circuit/` and obeys a **portability
contract**:

- Absolute paths matching the host project (`/home/`, `C:\`,
  `~/Dokumente`) are forbidden.
- Imports referencing top-level project modules (`from scripts.…`,
  `from data.…`) are forbidden.
- Hardcoded references to project-specific paths (`docs/builders/`,
  `data/`) or sibling project names (`AwesomeStudioPedal`,
  `PartsLedger`) outside `docs/` are forbidden.

Genuine exceptions go in `.portability-allow.txt` with a per-entry
reason. The contract is enforced mechanically by the portability
lint (TASK-051), not by code review.

Phase 7 (EPIC-006, TASK-043..045) is then mechanical: copy the
directory, add the standalone-repo's `pyproject.toml`, push.

## Consequences

**Easier:**

- The repository owns one Python tree; there is no
  library-vs-application boundary to maintain inside it.
- The portability lint is a single binary signal: if it stays green
  across Phases 1–6, extraction works. If it goes red, extraction
  breaks and we know why.
- Newcomers reading `.claude/skills/circuit/` see only what the
  standalone library would contain. The view is the deliverable.

**Harder:**

- Useful project-side utilities (the task-system scripts, the
  housekeep machinery) cannot be reached from inside the skill, even
  as a convenience. Anything genuinely shared has to be duplicated
  or vendored.
- The lint has to ship before the skill grows substantial code;
  that ordering is enforced by sequencing TASK-051 ahead of
  EPIC-001..006.

## See also

[`idea-001.skill-packaging.md`](../ideas/archived/idea-001.skill-packaging.md)
for the full portability contract and the Phase 7 extraction
procedure.
