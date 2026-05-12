---
id: ADR-0008
title: Phase 2b opens on evidence (escalation count), not calendar
status: Accepted
date: 2026-05-12
dossier-section: idea-001-circuit-skill.md §Phase 2b trigger gate
---

## Context

Phase 2 ships v0.1 of the layout engine — a structural rubric plus a
slot kernel that gets most schematics right. Phase 2b is the
follow-up: an AI-driven placer that handles the cases the rubric
mis-handles. Two ways to schedule Phase 2b:

- **Calendar** — pick a release date, ship Phase 2b on it. Risks
  shipping AI when the rubric was good enough, or *not* shipping it
  when the rubric is failing. Either way the decision is divorced
  from how the v0.1 placer is actually performing.
- **Evidence** — every v0.1 layout records its escalations
  (`meta.yml` — "rubric said B+, here's why") in a corpus. Phase 2b
  opens automatically when the corpus crosses a defined threshold of
  escalation count or escalation severity. The release script reads
  the corpus and refuses to ship a Phase 2 release once the gate has
  tripped.

Evidence-driven scheduling is the dossier's pattern for all "ship the
next phase when the current one's limits are documented" decisions.

## Decision

Phase 2b opens **on evidence**, not on calendar. The mechanism:

1. Every v0.1 layout writes a `meta.yml` recording rubric verdict,
   escalation count, and escalation reasons (TASK-057).
2. `scripts/check_phase2b_trigger.py` (TASK-058) walks the corpus,
   compares against the threshold defined in the dossier, and exits
   non-zero when the threshold is crossed.
3. The release script (TASK-059) invokes the check and refuses to
   tag a Phase 2 release if the gate has tripped — the maintainer
   has to either suppress with an explicit reason or open Phase 2b
   work.

The threshold is documented in the dossier and the script; the
release script does not invent it.

## Consequences

**Easier:**

- The Phase 2 → Phase 2b transition is a falsifiable signal, not a
  judgement call at every release-prep meeting. The maintainer
  reviews the gate output, not the question of whether to open
  Phase 2b at all.
- The escalation corpus becomes a useful artefact in its own right —
  it tells the maintainer *which* placement patterns the rubric
  misses, which informs the Phase 2b design.
- Phase 2b can open *late* if the rubric is unexpectedly good — the
  release script is happy to ship Phase 2 indefinitely as long as
  the gate is green.

**Harder:**

- A bad threshold (too lax) lets Phase 2 ship while the rubric
  silently fails. A bad threshold (too strict) blocks releases on
  routine escalations. Tuning is on the maintainer.
- The pattern only works if v0.1 layouts honestly emit their
  escalations. The `co-erc-engine` and renderer code-owner skills
  (TASK-056) surface this invariant at edit time.

## See also

[`idea-001-circuit-skill.md §Phase 2b trigger gate`](../ideas/archived/idea-001-circuit-skill.md)
for the threshold values and the escalation taxonomy. EPIC-002
TASK-057..059 implement the mechanism.
