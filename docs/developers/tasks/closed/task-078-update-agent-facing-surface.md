---
id: TASK-078
title: Update agent-facing surface for circuitsmith package rename
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Small (<2h)
effort_actual: XS (<30m)
complexity: Junior
human-in-loop: No
epic: circuitsmith-package
order: 3
prerequisites: [TASK-077]
---

## Description

Phase 3 of EPIC-010. Update the skill-resident surface so the
agent prompts and the code-owner reminders reflect the new
package layout. No library code changes — TASK-077 already
moved that.

- **Skill docstring updates.** Code samples in
  `.claude/skills/circuit/docs/index.md:77` and
  `.claude/skills/circuit/docs/components.md:135` switch from
  `from circuit.schema import …` to
  `from circuitsmith.schema import …`.
- **Code-owner reminder retarget.** The three `co-*`
  reminder skills point at file paths under the old skill
  folder; their `path:` (or equivalent trigger) targets need to
  shift to the new package location. Reminder content (the
  invariants surfaced) is unchanged:
  - `.claude/skills/co-netgraph/SKILL.md` → target
    `src/circuitsmith/netgraph.py`.
  - `.claude/skills/co-erc-engine/SKILL.md` → target
    `src/circuitsmith/erc_engine.py` (still a planned slot;
    reminder fires when the file appears).
  - `.claude/skills/co-schema/SKILL.md` → target
    `src/circuitsmith/schema/*.json`.
- **Skill shim files (deferred).** Phase 3.3 — optional thin
  `.py` shims next to `SKILL.md` for agent-callable surfaces —
  is explicitly out of scope here. Defer until a concrete
  agent-callable surface needs one.

## Acceptance Criteria

- [x] All `from circuit.*` references in
      `.claude/skills/circuit/docs/**/*.md` are rewritten to
      `from circuitsmith.*` (index.md:77, components.md:135).
- [x] The three `co-*` reminder skills load against the new
      paths — `.claude/codeowners.yaml` patterns shift from
      `.claude/skills/circuit/...` to `src/circuitsmith/...`
      (co-netgraph → `netgraph.py`, co-schema →
      `schema/*.json`, co-erc-engine → `erc_engine.py`).
      Skill registry confirms the new descriptions are loaded.
      Reminder bodies updated to reference ADR-0012 in place of
      ADR-0007 where the portability invariant is named.
- [x] No skill shim `.py` files added in this task (deferred
      per the idea's § "Phase 3.3").

## Test Plan

Manual verification: edit a guarded file under
`src/circuitsmith/` and confirm the `co-*` reminder surfaces.
`markdownlint-cli2 --fix` clean on the touched markdown files.

## Prerequisites

- **TASK-077** — the new package paths must exist before the
  agent-facing surface points at them.

## Notes

The full Phase 3 checklist lives in
[`docs/developers/ideas/archived/idea-002-consolidate-skill-python-into-central-module.md`](../../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md)
§ "Phase 3 — Agent-facing surface".
