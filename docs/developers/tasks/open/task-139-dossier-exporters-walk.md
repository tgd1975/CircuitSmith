---
id: TASK-139
title: Walk the IDEA-001 exporters dossier against shipped BOM + netlist exporters
status: open
opened: 2026-05-15
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: dossier-gap-analysis
order: 6
prerequisites: [TASK-134]
---

## Description

Walk
[`idea-001.exporters.md`](../../ideas/archived/idea-001.exporters.md)
against the shipped BOM and netlist exporters (EPIC-004 + EPIC-006
closeout). Both shipped per the EPIC-004 closeout, so most rows
here will be bucket 1.

For each named exporter feature in the dossier, write one row into
the **Exporters** sub-table of
`docs/developers/_dossier-gap-analysis.md`:

- **BOM column set** — `ref`, `value`, `package`, `qty`, etc. Match
  against the shipped BOM emit.
- **BOM format** — Markdown table per the dossier, CSV per any
  later extension. Confirm shipped format.
- **Netlist format** — KiCad-compatible netlist per EPIC-004.
  Bucket 1 expected.
- **Cross-page netlist handling** — EPIC-014 TASK-125 / TASK-127
  emit per-page artefacts but the netlist remains a single
  whole-circuit file. Confirm and bucket.
- **Three-column PartsLedger-aware BOM** — the dossier sketches
  this. Open [IDEA-011](../../ideas/open/idea-011-prefer-on-hand-parts-from-partsledger.md)
  owns it end-to-end. **Cross-link, do not duplicate.** Bucket 3
  with the gate "IDEA-011 lands" and a link to the open idea.

Drop any rows whose only content is "see ASP IDEA-018/019" —
those references are stale per IDEA-012's "Open questions"
cross-repo bullet. **Don't write a row just to record a
reference**; record the cross-repo verdict in TASK-142's cleanup
table.

## Acceptance Criteria

- [ ] One analysis row per dossier-named exporter feature; bucket
      assigned.
- [ ] Three-column PartsLedger BOM row is bucket 3, gated on
      IDEA-011, with explicit cross-link.
- [ ] No row consists solely of "see ASP IDEA-018/019" — those go
      to TASK-142.
- [ ] Any bucket-4 row has a spawned IDEA-NNN file linked from the
      verdict.

## Test Plan

No automated tests required — change is documentation / analysis.

Manual verification:

1. Open `src/circuitsmith/exporters/` (or wherever the BOM / netlist
   emit lives) and confirm every dossier feature has a row.
2. Confirm the IDEA-011 cross-link in the three-column-BOM row
   resolves to the open idea file.

## Notes

- This task should be the shortest of the file walks — BOM +
  netlist scope is small (typically 5–8 rows total) and EPIC-004
  / EPIC-006 closure took care of most rows.
- The PartsLedger row is the place where the walk can confirm that
  IDEA-011's deferred status remains correct — bucket 3 with the
  gate clearly stated.
