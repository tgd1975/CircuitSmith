---
id: TASK-066
title: Author docs/developers/TASK_SYSTEM.md describing the IDEA/EPIC/TASK workflow and /ts-* skills
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: developer-docs-governance
order: 5
---

## Description

The task system is the spine of CircuitSmith's planning — every piece
of work flows through `IDEA → EPIC → TASK` with a defined lifecycle
(`open → active → closed`, plus `paused`). Today the workflow is
documented in pieces: HIL semantics live in
[`AUTONOMY.md`](../../AUTONOMY.md), commit/branch rules live in
[`CLAUDE.md`](../../../../CLAUDE.md), the `/ts-*` skills are
self-describing but not catalogued, and `/housekeep`'s behaviour is
named in CLAUDE.md but not explained. A new contributor has no single
page that explains "this is how we plan and track work."

Model: AwesomeStudioPedal's
[`TASK_SYSTEM.md`](../../../../../AwesomeStudioPedal/docs/developers/TASK_SYSTEM.md)
(202 lines). CircuitSmith's version describes the same package
(`awesome-task-system`, installed copy per CLAUDE.md `## Task-system
installation`) plus the project's local conventions.

## Acceptance Criteria

- [x] `docs/developers/TASK_SYSTEM.md` exists and is linked from CONTRIBUTING.md.
- [x] The three artefact types (IDEA, EPIC, TASK) are defined with one-paragraph descriptions and one example each.
- [x] The lifecycle states (`open`, `active`, `closed`, `paused`) are documented with transition triggers and the skill that effects each transition.
- [x] Every `/ts-*` skill is listed with a one-line description and a "use when" trigger.
- [x] `/housekeep`'s role is documented: the four index files (`OVERVIEW.md`, `EPICS.md`, `KANBAN.md`, `ideas/OVERVIEW.md`) are entirely generated; manual edits to them are lost.
- [x] The `human-in-loop` field's four values are explained at high level with a pointer at AUTONOMY.md for the agent-semantics depth.
- [x] Prerequisite semantics are explained: a task with unmet prerequisites cannot be activated.

## Test Plan

No automated tests. Verify by spot-check: every `/ts-*` skill listed
in the doc exists in `.claude/skills/`; the four index files named in
the doc exist and have the documented headers.

## Prerequisites

None — the task system already exists.

## Notes

This doc is the **human-facing** counterpart to AUTONOMY.md (which is
agent-facing). The same concepts (HIL, ADRs-on-ambiguity, the
work-phase / commit-phase split) get a paragraph each, with a link to
AUTONOMY.md for the operational details the agent needs.

The doc should explicitly **not** duplicate the dossier in
[`docs/developers/ideas/archived/`](../../ideas/archived/) — that's
the deep-design content, and the task system is plumbing.
