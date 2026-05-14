---
id: IDEA-012
title: Revisit the original IDEA-001 dossier — gap analysis against shipped 0.1.0
description: Walk the archived IDEA-001 dossier section-by-section against shipped 0.1.0 and spawn follow-up ideas for the deliberately-deferred, contingent, and excluded surface area.
category: tooling
---

<!-- Bookmark idea — opened on the squash-merge into main without
     review. The body below is a sketch of what the analysis should
     cover; the real work is the thorough walk-through and the
     follow-up ideas it spawns. -->

## Motivation

CircuitSmith 0.1.0 shipped to PyPI on the back of EPIC-001..006 plus a
follow-on packaging/release wave (TASK-080). That is — by design — only
the v0.1 slice of the inherited [IDEA-001 dossier](../archived/idea-001-circuit-skill.md).
The dossier itself stages further work behind explicit gates (Phase 2b
AI placer, Phase 7 standalone-repo extraction) and lists a Deliberately
Excluded section that doubles as a "not yet, but maybe later" wishlist.

We have not done a structured walk of the dossier since the
idea→epic conversion on 2026-05-12. After eight months of real
implementation, the shape of what is missing is no longer the same as
what the dossier said was deferred. Some "excluded" items have become
plausible; some Phase 2b/7 prerequisites have or have not been hit;
some Phase 1–6 work shipped with reduced scope and left a tail.

This idea is the bookmark to do that walk-through and spawn the
follow-up ideas it produces.

## Scope of the analysis

Walk every section of the inherited dossier and classify each named
deliverable into one of four buckets:

1. **Shipped in 0.1.0 as specified** — close the loop, no follow-up.
2. **Shipped in 0.1.0 with reduced scope** — note the delta; decide
   whether the gap is worth a follow-up idea or is fine as-is.
3. **Deferred by design, gate not yet tripped** — confirm the gate
   condition is still the right one (e.g. Phase 2b's "kernel-failure
   modes on real use" trigger), and whether 0.1.0 evidence moves the
   needle.
4. **Deferred by design, gate now tripped or trip-able** — spawn a
   follow-up idea (or epic, if scope is clear) and link from here.

The dossier files to walk, in their authoring order (see the dossier's
own "Deep-dive authoring order" section):

- [`idea-001-circuit-skill.md`](../archived/idea-001-circuit-skill.md) — overview, phase plan, exclusions
- [`idea-001.components.md`](../archived/idea-001.components.md) — component library, backlog rows
- [`idea-001.yaml-format.md`](../archived/idea-001.yaml-format.md) — `.circuit.yml` schema
- [`idea-001.layout-engine-concept.md`](../archived/idea-001.layout-engine-concept.md) — kernel + router + rubric
- [`idea-001.layout-engine-discussion.md`](../archived/idea-001.layout-engine-discussion.md) — rationale (for context only)
- [`idea-001.erc-engine.md`](../archived/idea-001.erc-engine.md) — checks S1–S5 + E1–E10
- [`idea-001.rule-catalog.md`](../archived/idea-001.rule-catalog.md) — 30–50-rule catalog scope
- [`idea-001.exporters.md`](../archived/idea-001.exporters.md) — BOM + netlist
- [`idea-001.skill-packaging.md`](../archived/idea-001.skill-packaging.md) — skill packaging, acceptance tests

For each file, the deliverable is: a short table in this idea (one row
per dossier section walked) with the bucket assignment and — for
bucket 4 — the spawned IDEA-NNN link.

## Known starting points for the walk

These are the surfaces I already suspect the walk will touch — not a
substitute for the walk itself, just so future me doesn't start cold.
Each is a hypothesis to confirm or kill during the analysis.

- **Phase 2b — AI placer.** Dossier says "ships when v0.1 has
  accumulated concrete kernel-failure modes on real circuits". After
  0.1.0, has the kernel actually escalated on anything in
  `meta.yml.provenance.escalations`? If yes, Phase 2b becomes a real
  follow-up; if no, the trigger gate remains correct and we just
  record the cycle's outcome.
- **Phase 7 — Standalone repo extraction.** Dossier says the
  prerequisite is "Phase 6 acceptance test passes and the skill has
  been used on at least one real circuit addition in this project."
  The PyPI ship in TASK-080 is a *different* extraction path — it
  packaged the `circuitsmith` Python module, not the skill directory
  proper. Decide whether Phase 7 is now redundant, transformed, or
  still pending.
- **Deliberately-excluded items.** Several have softened or hardened:
  audio signal conditioning, the `diode` category (which gates E9
  promotion to ERROR per ERC §E9), general-purpose auto-layout, the
  rule catalog's 30–50-entry ceiling.
- **Rule catalog scope.** Dossier seeds the catalog with one entry
  per shipped ERC check (15 rows) and backlogs the rest. Where is the
  catalog actually at after 0.1.0, and what is the next batch?
- **Component library backlog.** [components.md](../archived/idea-001.components.md)
  has a "requires a new §5.3 row first" backlog (diodes, transistors,
  ICs beyond MCU). [IDEA-009](../archived/idea-009-active-device-profiles-and-multi-page-renderer.md)
  already addresses active devices; check what overlap exists and
  whether the backlog row format is still the right entry shape.
- **Pipeline contracts that drifted.** Phase 5 (Markdown integration)
  named two implementation paths gated on IDEA-022 (MkDocs) ordering.
  IDEA-022 lived in AwesomeStudioPedal, not here — so this contract
  needs reframing or dropping.

## Open questions for the walk

- Does any of bucket 2's "reduced scope" surface area belong on the
  0.1.x patch line, or only on 0.2.0+?
- Several already-open follow-up ideas (IDEA-008, IDEA-009, IDEA-011)
  already cover slices of the dossier's exclusions. The walk should
  cross-reference and avoid duplicating them rather than spawning
  parallel ideas.
- The dossier's relationship table references IDEA-011, IDEA-018,
  IDEA-019, IDEA-022 — all of which live in AwesomeStudioPedal. After
  the cross-repo split, what is the right framing for these
  relationships? (PartsLedger-style "two repos, one contract" or
  "ASP's IDEA-011 is now CircuitSmith's PCB story TBD"?)

## Deliverable shape

The walk produces *this idea, expanded* — the body above grows a real
analysis table plus the spawned follow-up ideas. When that table is
done and every bucket-4 row has a child IDEA, this idea archives.

## Why this is a bookmark, not a task

The walk-through is a long-form analysis that needs a calm sitting
with all nine dossier files open. Filing it as an open IDEA keeps it
visible without committing the next agent session to it.
