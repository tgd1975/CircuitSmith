---
id: ADR-0009
title: Autonomous-implementation mode — protocol + driver skill
status: Accepted
date: 2026-05-12
dossier-section: docs/developers/AUTONOMY.md
---

## Context

The user wants epic implementation to run with minimal involvement —
brief at the start, review at the end, intervene only on rare
occasions. The task system already supplies the mechanical pieces
(`/ts-task-active`, `/ts-task-done`, `/housekeep`, `/commit`,
`/check-branch`, `human-in-loop` labels), but the operational
protocol that sequences them into an autonomous loop has been
implicit, decided per-session.

A read of the open task set surfaced concrete drift hazards: HIL
labels with no defined semantics, no driver skill that sequences
an epic, EPIC-007 sitting on `branch: main` (which `/check-branch`
blocks), no ADR folder for the "decide + ADR + continue" rule, no
permissions allowlist for the routine commands the loop runs, no
definition-of-done gate before `/ts-task-done`.

The four-option HIL space, the ADR-on-ambiguity rule, and the
no-push-without-approval rule were the user's stated preferences;
they need to be written down before the next autonomous epic run
relies on them.

## Decision

Adopt the protocol described in
[`docs/developers/AUTONOMY.md`](../AUTONOMY.md):

- Four HIL values (`No`, `Clarification`, `Support`, `Main`) with
  defined agent behaviour for each.
- An ADR-on-ambiguity rule: mid-task decisions without a defensible
  default land as a new ADR and the work continues; ADRs are
  reviewed in batch at the next stop-line.
- An epic-driver `/epic-run` skill that composes over the existing
  task-system skills — it does not re-implement state transitions.
- A definition-of-done checklist that gates `/ts-task-done`.
- A no-push-without-approval rule, backed by `.claude/settings.json`
  `permissions.deny` entries (the harness blocks; the protocol
  matches the mechanism).
- A `## Implementation log` convention on every epic file —
  one append-only line per closed task.
- A per-epic `branch:` convention (`release/epic-NNN-<slug>`) with
  `/ts-task-active` nagging on mismatch and offering the
  `[c]ontinue` path to rewrite the field.

The protocol's scope is **operational, not enforced by CI**. A
GitHub Actions check that fails on missing ADRs or missing
implementation-log entries would be a tightening move; deliberately
deferred until the protocol shows it holds in practice.

## Consequences

**Easier:**

- The next autonomous epic run has a single document the user and
  agent agree on. Disagreements about "should the agent ask?" map
  to specific clauses in AUTONOMY.md.
- New tasks fall into one of four HIL buckets — labelling is
  reproducible, not a session-by-session judgement.
- ADRs become the standard channel for mid-run decisions, instead
  of either freezing on each one or making them silently.
- The end-of-epic review packet is a structured format the user
  can scan in a minute, instead of a conversation log.

**Harder:**

- Protocol drift is now a real failure mode — if the agent's
  behaviour diverges from AUTONOMY.md, the user can no longer rely
  on the contract. Periodic re-audits (perhaps a `/audit-autonomy`
  skill) become a possible follow-up.
- The HIL sweep across existing tasks is a one-time-with-recurrence
  cost: every new task is labelled and the labels must remain
  operationally meaningful.
- The `/epic-run` skill has to be kept in sync with the underlying
  task-system skills it composes — a skill API change ripples
  here.

## See also

- [`docs/developers/AUTONOMY.md`](../AUTONOMY.md) — the protocol
  itself, source of truth for the operational details.
- [`CLAUDE.md`](../../../CLAUDE.md) `## Autonomy` — one-paragraph
  pointer at AUTONOMY.md.
- TASK-060 — the seed task; body carries the audit findings that
  motivated each piece of this decision.
- [`ADR-0007`](0007-skill-directory-is-the-library.md) — adjacent
  decision about the skill directory; the autonomous loop respects
  the portability contract that ADR codifies.
