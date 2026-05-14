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

- The walk should look at the whole picture (shipped + deferred +
  excluded) rather than slicing by release line — patch-vs-minor
  routing falls out naturally once each row's bucket is assigned.
- Focus the cross-reference effort on **what 0.1.0 actually
  implemented**, not on the (sparse) open-idea backlog. Open ideas at
  time of writing: only IDEA-011 (PartsLedger inventory) and
  IDEA-013 (senior review). Archived siblings worth checking on the
  walk because they may already have closed loops the dossier flags as
  open: IDEA-008 (sub-blocks + non-LED kernel rules) and IDEA-009
  (active-device profiles + multi-page renderer) — read the archived
  file before re-spawning anything in that space.
- The dossier's relationship table references **AwesomeStudioPedal's**
  IDEA-011, IDEA-018, IDEA-019, IDEA-022 (not this repo's IDEA-011,
  which is unrelated). For each: open the referenced file in the ASP
  repo during the walk and decide row-by-row whether the content is
  still relevant — if yes, restate the relationship in CircuitSmith
  terms; if no (already archived there, superseded, or out of scope
  post-split), drop the reference.

## Implementation plan

The walk is one long sitting, not a multi-session epic. The plan
below is a checklist for that sitting; each step produces a concrete
edit to *this* file (the analysis table grows in-place) or spawns a
named child IDEA. No external task files, no separate ADRs — the
output is this idea, expanded.

### Step 0 — orient (≈15 min, no edits)

- Re-read [idea-001-circuit-skill.md](../archived/idea-001-circuit-skill.md)
  end-to-end to refresh the phase plan and exclusion list.
- Locate the in-repo rule catalog. Candidates: `src/circuitsmith/`
  schema files, `docs/developers/rules/`, or a string-grep for
  `rule-catalog` / `RULE-CATALOG`. Record its path in scratch space —
  the catalog-scope row in step 7 needs it.
- Run `grep -rl 'provenance.escalations' .` plus a sample read of two
  or three `meta.yml` files in any rendered output dir to confirm the
  escalations corpus shape. This is the evidence base for the Phase
  2b row in step 1.
- Open the analysis-table scaffold below in the editor.

### Step 1 — phase-plan walk (idea-001-circuit-skill.md)

Walk every numbered phase (1 through 7) in the dossier's phase plan.
For each:

1. Assign a bucket (1 / 2 / 3 / 4 per the four-bucket scheme above).
2. Write one row into the analysis table (`Phase N — short name —
   bucket — verdict / link`).
3. Bucket-3 rows must cite the evidence that keeps the gate closed.
   Specifically for **Phase 2b**: state the escalations-corpus count
   (`grep -c …` across all rendered `meta.yml` files) and whether any
   entries flag the kernel-failure modes the dossier names.
4. Bucket-4 rows spawn a child IDEA *immediately* — don't batch.

Phase 7 (standalone-repo extraction) gets explicit treatment per the
"Known starting points" hypothesis: the PyPI ship packaged the Python
module; the `.claude/skills/circuit/` skill directory is still
in-repo and consumed by-copy elsewhere — so the phase is deferred-
by-default, not redundant. Record that verdict in the row.

### Step 2 — components walk (idea-001.components.md)

- Open [idea-001.components.md](../archived/idea-001.components.md).
- Inventory the **shipped** library: `src/circuitsmith/components/`
  currently exposes `actives.py`, `connectors.py`, `ics.py`,
  `mcus.py`, `passives.py`, `sensors.py`. The dossier's "diode
  category" backlog item is the load-bearing one — check whether
  diodes/transistors in `actives.py` close that loop or only partially
  cover it (ERC §E9 promotion to ERROR is the proxy: is the rule
  active or still gated?).
- Cross-reference the archived [IDEA-009](../archived/idea-009-active-device-profiles-and-multi-page-renderer.md)
  before re-spawning anything in the actives space — its closure
  probably resolves several dossier rows.
- One table row per dossier §5.3 backlog entry, bucket-assigned.

### Step 3 — YAML format walk (idea-001.yaml-format.md)

- Read [idea-001.yaml-format.md](../archived/idea-001.yaml-format.md)
  alongside the shipped schema at
  [src/circuitsmith/schema/circuit.schema.json](../../../src/circuitsmith/schema/circuit.schema.json).
- For each schema construct the dossier names, mark *shipped /
  reduced / deferred*. Flag any field that shipped under a different
  name — the dossier's vocabulary is the ancestor, not the source of
  truth.
- Cross-reference archived [IDEA-008](../archived/idea-008-first-class-sub-blocks-and-non-led-kernel-rules.md)
  for the sub-block syntax row before spawning anything new.

### Step 4 — layout engine walk (concept + discussion)

- The discussion file is rationale-only — skim it for context, do
  *not* generate rows from it.
- The concept file is the kernel + router + rubric spec. One row per
  named subsystem (kernel dispatch, router, rubric scorer, page-break
  logic). Page-break in particular: confirm whether the multi-page
  path from archived IDEA-009 shipped or is still partial.

### Step 5 — ERC engine walk (idea-001.erc-engine.md)

- The dossier defines checks S1–S5 and E1–E10. Open
  [src/circuitsmith/erc_engine.py](../../../src/circuitsmith/erc_engine.py)
  (heed the `/co-erc-engine` invariants if editing — but this step is
  read-only).
- Build a 15-row sub-table: one row per check, columns = *shipped?*,
  *severity matches dossier?*, *deferred-by-design (e.g. E9 on diode
  category)?*. Carry severity-mismatch rows into the bucket-4 spawn
  decision.

### Step 6 — exporters walk (idea-001.exporters.md)

- BOM + netlist. Both shipped per EPIC-006 closeout, so most rows
  here will be bucket-1. The interesting row is the
  **PartsLedger-aware three-column BOM** which the dossier sketches
  and which open [IDEA-011](idea-011-prefer-on-hand-parts-from-partsledger.md)
  owns end-to-end — cross-link, do not duplicate.
- Drop any rows whose only content is "see ASP IDEA-018/019" after
  confirming in the ASP repo that those references are stale or
  superseded (per the "Open questions" cross-repo bullet above).

### Step 7 — rule catalog walk (idea-001.rule-catalog.md)

- Compare the dossier's 30–50-entry target against the catalog
  located in step 0.
- One row: catalog *current size* vs *target ceiling*. If the
  ceiling is still load-bearing (i.e. ERC behaviour changes when
  hit), that's a bucket-3 with a real gate. If the ceiling was
  aspirational, that's bucket-2 with a "fine as-is" verdict.

### Step 8 — skill packaging walk (idea-001.skill-packaging.md)

- The dossier's acceptance-tests list is the load-bearing part. For
  each acceptance test: shipped? superseded by EPIC-006's test
  harness? still pending?
- The skill-packaging row dovetails with the Phase 7 verdict from
  step 1 — make sure they're consistent.

### Step 9 — cross-repo reference cleanup

- For each ASP-era reference the walk surfaced (the dossier's
  IDEA-011/018/019/022 in particular): open the file in the ASP repo,
  decide *relevant / superseded / out-of-scope*, and write that
  verdict into the corresponding analysis row. Do **not** spawn a
  CircuitSmith IDEA solely to mirror an ASP one — only spawn if
  CircuitSmith has work to do.

### Step 10 — close out

- Verify the analysis table covers every dossier section listed in
  "Scope of the analysis" — no missing rows.
- Verify every row meets its bucket's archival trigger (see
  "Deliverable shape" below).
- Run `/housekeep` so the ideas OVERVIEW reflects any new IDEA-NNN
  files spawned by bucket-4 rows.
- `/commit` this file + the spawned ideas + the regenerated OVERVIEW
  in one pathspec.
- Move this file to `archived/` and `/commit` the move as a
  follow-on. (`/ts-idea-archive` is the right driver if available.)

### Expected scale

Roughly 60–90 analysis-table rows across the nine dossier files (5–15
per file). Most are bucket-1 one-liners; the long tail is bucket-3
gate notes. Bucket-4 spawns are expected to be **few** — the dossier
was already pruned hard at idea→epic conversion, and 0.1.0 shipped
most of what survived. If the walk produces more than ~5 new IDEAs,
that's a signal something was missed in the original conversion and
warrants a discussion before mass-spawning.

## Deliverable shape

The walk produces *this idea, expanded* — the body above grows a real
analysis table plus the spawned follow-up ideas. Per-bucket archival
triggers:

- **Bucket 1 (shipped as specified):** one-line confirmation in the
  table; no follow-up.
- **Bucket 2 (shipped with reduced scope):** the row carries either
  an explicit "fine as-is, no follow-up" verdict or a spawned IDEA
  link — never left ambiguous.
- **Bucket 3 (deferred, gate not tripped):** one-line note that the
  gate condition still holds, plus the evidence that confirms it
  (e.g. zero `provenance.escalations` entries for Phase 2b).
- **Bucket 4 (deferred, gate tripped):** spawned IDEA-NNN link.

This idea archives when every dossier section listed above has a row
and every row meets its bucket's trigger — not when bucket 4 alone is
resolved.

## Why this is a bookmark, not a task

The walk-through is a long-form analysis that needs a calm sitting
with all nine dossier files open. Filing it as an open IDEA keeps it
visible without committing the next agent session to it.
