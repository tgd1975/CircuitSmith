---
id: TASK-079
title: Repo docs sweep and CHANGELOG bullet for circuitsmith refactor
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuitsmith-package
order: 4
prerequisites: [TASK-077]
---

## Description

Phase 4 of EPIC-010. Sweep repo-internal docs for stale
references to the old library path and add the CHANGELOG bullet
that documents the rename.

- **Doc grep + targeted updates.** Search for
  `.claude/skills/circuit/` in: `CLAUDE.md`,
  `docs/developers/ARCHITECTURE.md`,
  `docs/developers/TESTING.md`,
  `docs/developers/CI_PIPELINE.md`,
  `docs/developers/CODE_OWNERS.md`,
  `docs/developers/AUTONOMY.md`. Update references that point
  at *library code* to `src/circuitsmith/`; leave references
  that point at the *agent-facing skill* (SKILL.md, docs/)
  alone — they still live under
  `.claude/skills/circuit/`.
- **scripts/README.md path descriptions** at lines 13 and 51 —
  same library-vs-skill distinction.
- **CHANGELOG bullet** under `[Unreleased] ### Changed`:
  *"Relocate library code from `.claude/skills/circuit/` to
  `src/circuitsmith/` and rename the importable package from
  `circuit` to `circuitsmith` (supersedes ADR-0007 via
  ADR-0012)."*
- **`.vibe/config.toml`** — no change. The `circuit` skill
  still exists at `.claude/skills/circuit/`, just with less
  code in it.

## Acceptance Criteria

- [x] `rg -n "\.claude/skills/circuit/" docs/ CLAUDE.md scripts/README.md`
      returns only matches that point at the agent-facing skill
      (SKILL.md, docs/). Library-code references are gone.
      ARCHITECTURE.md/TESTING.md/CI_PIPELINE.md/CODE_OWNERS.md/
      AUTONOMY.md/scripts/README.md updated; CLAUDE.md had no
      library-code references to start with.
- [x] `CHANGELOG.md` `[Unreleased] ### Changed` contains the
      bullet above. The edit lands in the dedicated
      CHANGELOG-delta commit at the end of the epic-run per the
      [`/epic-run`](../../../.claude/skills/epic-run/SKILL.md) §
      "CHANGELOG-delta phase" protocol; per-task commits never
      touch `CHANGELOG.md`.
- [x] `markdownlint-cli2 --fix` clean on all modified files.

## Test Plan

No automated tests required — change is documentation only.
Manual verification: grep returns are clean; CHANGELOG entry
present.

## Prerequisites

- **TASK-077** — the rename must already be in place before
  docs claim it happened.

## Notes

The full Phase 4 file list lives in
[`docs/developers/ideas/archived/idea-002-consolidate-skill-python-into-central-module.md`](../../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md)
§ "Phase 4 — Repo docs and CHANGELOG".
