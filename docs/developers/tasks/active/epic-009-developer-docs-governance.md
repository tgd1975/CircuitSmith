---
id: EPIC-009
name: developer-docs-governance
title: Developer Documentation and Governance Scaffolding
status: open
opened: 2026-05-12
closed:
assigned:
branch: release/epic-009-developer-docs-governance
---

CircuitSmith ships unusually thorough *mechanical* guardrails for a
concept-stage project (code-owner skills, portability lint, ADR
discipline, the autonomous-implementation protocol in
[`docs/developers/AUTONOMY.md`](../../AUTONOMY.md)), but the *prose*
onboarding layer is thin: setup is split across [`README.md`](../../../../README.md),
[`CONTRIBUTING.md`](../../../../CONTRIBUTING.md), and [`.envrc.example`](../../../../.envrc.example);
test conventions are implicit; the architecture lives in the README
overview and the nine-file IDEA-001 dossier with no top-down
one-pager; the commit-policy rationale is a paragraph in CLAUDE.md
that a new contributor cannot find from a fresh clone; branch
protection on `main` is not enabled.

This epic closes that gap by mirroring the load-bearing subset of
AwesomeStudioPedal's developer-doc set —
[`docs/developers/`](../../../../../AwesomeStudioPedal/docs/developers/) —
into CircuitSmith, scoped to what a junior contributor needs to land
their first PR without coming back with five clarifying questions.
The selection was triaged against CircuitSmith's lifecycle stage:
load-bearing docs land now, release / known-issues docs land when
triggered, project-specific docs (BLE, Android) are skipped entirely.

The deliverables:

- **Onboarding set** — DEVELOPMENT_SETUP, TESTING, CODING_STANDARDS,
  CI_PIPELINE, TASK_SYSTEM, CODE_OF_CONDUCT. The "first-day junior"
  pack.
- **Architecture set** — ARCHITECTURE, MERMAID_STYLE_GUIDE. The
  top-down view; ADRs remain the decision-index, the dossier remains
  the depth, but ARCHITECTURE.md is the entry point.
- **Policy set** — SECURITY_REVIEW, COMMIT_POLICY,
  BRANCH_PROTECTION_CONCEPT. The "why we do it this way" pack;
  implicit knowledge becomes written knowledge.
- **Governance action** — apply GitHub branch protection on `main`
  per the documented config (TASK-073, HIL Main).

The protection ruleset is tuned for the current solo + autonomous-loop
posture: status checks required, linear history, no force-push, no
deletion, **PR review not required** (admin-self-approval deadlock
would otherwise block every solo merge), admin enforcement off. The
trigger to tighten the rules is contributor #2 landing — recorded in
the doc, not folklore.

This epic is independent of EPIC-001..006 (the implementation phases)
and lands **before** EPIC-001 work begins so the first wave of code
contributions has a documented home.

Cross-references:

- [`AUTONOMY.md`](../../AUTONOMY.md) — the operational protocol that
  governs how this epic's tasks are executed.
- [`adr/0009-autonomous-implementation-mode.md`](../../adr/0009-autonomous-implementation-mode.md) —
  the ADR that records the autonomous-loop decision; some of the
  rationale this epic surfaces in prose is also captured there.
- [`CLAUDE.md`](../../../../CLAUDE.md) — the implicit rules this
  epic transcribes into discoverable form.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.

## Implementation log
