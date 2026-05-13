---
id: TASK-030
title: Write docs/erc-checks.md
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: circuit-erc
order: 9
prerequisites: [TASK-022, TASK-027]
---

## Description

Author `.claude/skills/circuit/docs/erc-checks.md` — the per-check
reference. One section per check (S1–S5, E1–E10) covering:

- **Trigger** — what topological condition fires it.
- **Meaning** — what real-world hardware failure mode it prevents.
- **Severity** — WARNING vs ERROR, plus v0.1 defaults.
- **Suppression** — how to suppress per-component or per-circuit with
  a worked YAML example.
- **Cross-reference** — link to the catalog entry (`rules.json`)
  for the Why/Senior's tip/Source content.

This is the document a contributor reads when an ERC finding surfaces
on their PR.

## Acceptance Criteria

- [x] All 15 check codes have their own section in `erc-checks.md`.
- [x] Each section has all five subsections populated.
- [x] Each suppression example is a valid `.circuit.yml` snippet that the schema accepts.
- [x] Cross-references to `rules.json` entries are valid (every `enforced_by` resolves).

## Test Plan

No automated tests required — documentation deliverable. Spot-verify cross-references resolve and suppression examples parse against the schema.

## Prerequisites

- **TASK-022** — the 15 check codes to document.
- **TASK-027** — the report enrichment to cross-reference.

## Notes

This closes out EPIC-003.
