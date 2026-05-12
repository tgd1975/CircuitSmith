---
id: EPIC-008
name: architecture-fitness-functions
title: Architecture Fitness Functions and Governance
status: open
opened: 2026-05-12
closed:
assigned:
branch: release/epic-008-governance-slice
---

Promote the architecture's load-bearing invariants from prose into
machine-checked tests, edit-time guardrails, and process artefacts.

The [IDEA-001 dossier](../../ideas/archived/idea-001-circuit-skill.md)
and its seven companion files specify the design — `NetGraph` as the
shared contract, exporter decoupling, the skill-directory portability
contract, the hallucination-free rule-catalog policy. This epic
supplies the mechanisms that *prevent drift* from that design during
implementation, before code volume ramps. Documents describe; tests,
hooks, and gates enforce.

Six mechanisms, seven tasks:

- **Boundary-import contract test** (TASK-050) — `bom_exporter`,
  `netlist_exporter`, and `renderer` cannot reach across the decoupling
  lines named in the dossier. Machine-checked, not review-checked.
- **Portability lint** (TASK-051) — `.claude/skills/circuit/` carries
  no project-specific paths or imports. Phase 7 (EPIC-006 / TASK-043–045)
  extraction stays mechanical because every Phase 1–6 commit was
  vetted against this lint.
- **Schema-validation pre-commit** (TASK-052) — malformed `.circuit.yml`
  cannot be committed in the first place. Catches drift before the
  renderer is even invoked.
- **`NetGraph` golden-hash CI contract** (TASK-053) — schema or
  serialiser changes that inadvertently break determinism fail loudly,
  not silently. Beyond TASK-008's one-shot check.
- **ADR seed** (TASK-054) — the load-bearing decisions extracted from
  the dossier into a decision-log format newcomers can read in one
  sitting. The dossier remains authoritative; ADRs are the index.
- **Code-owner skills + `PreToolUse` hook** (TASK-055, TASK-056) —
  high-blast-radius files surface their invariants at edit time, before
  the change lands. Local analogue of GitHub CODEOWNERS, fitted to the
  current solo, Claude-driven workflow.

The Phase 2b trigger gate (three additional tasks: TASK-057, TASK-058,
TASK-059) lives in EPIC-002 because it is tightly coupled to the
layout-engine `meta.yml` deliverables, but it shares this epic's intent:
turn a policy ("the maintainer evaluates at every release-prep review")
into a mechanism (the release script reads the corpus and refuses to
ship).

This epic is independent of EPIC-001..007 in the sense that each task
gates only on its specific subject modules, and several tasks (ADRs,
portability lint, code-owner registry) have no prerequisites at all —
they can land before any Phase 1 code exists, and start enforcing as
soon as code arrives.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
