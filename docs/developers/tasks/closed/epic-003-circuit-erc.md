---
id: EPIC-003
name: circuit-erc
title: Circuit Skill — ERC Engine and Rule Catalog
status: open
opened: 2026-05-12
closed:
assigned:
branch: release/epic-003-circuit-erc
---

Seeded by IDEA-001 (Circuit-Skill — AI-Assisted Schematic Generation with ERC, BOM, and Netlist Export).

Phase 3 of IDEA-001. Implements the topology-only Electrical Rule Check
engine with structural checks `S1–S3` and electrical checks `E1–E10`,
seeds the source-linked rule catalog (`knowledge/rules.json`) with one
entry per shipped check, and wires the catalog into the ERC report so
each non-OK finding carries a "Why / Senior's tip / Source" block.

ERC runs strictly pre-layout and consumes the shared `NetGraph` data
model owned by EPIC-002. The catalog is the knowledge layer that turns
the linter into a "senior designer" mentor — runtime LLM generation of
hardware rules is deliberately excluded.

Companion design docs:
`docs/developers/ideas/archived/idea-001.erc-engine.md`,
`docs/developers/ideas/archived/idea-001.rule-catalog.md`.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
