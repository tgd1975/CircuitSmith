---
id: TASK-135
title: Walk the IDEA-001 components dossier against shipped component library
status: closed
closed: 2026-05-15
opened: 2026-05-15
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: dossier-gap-analysis
order: 2
prerequisites: [TASK-134]
---

## Description

Walk
[`idea-001.components.md`](../../ideas/archived/idea-001.components.md)
against the shipped library in
[`src/circuitsmith/components/`](../../../../src/circuitsmith/components/).
The currently-shipped modules are `actives.py`, `connectors.py`,
`ics.py`, `mcus.py`, `passives.py`, `sensors.py`.

For each row in the dossier's §5.3 backlog table, write one row into
the **Components** sub-table of
`docs/developers/_dossier-gap-analysis.md` with bucket assignment
and verdict.

The load-bearing rows the walk must cover explicitly:

- **Diode category.** The dossier's §5.3 backlog gates ERC §E9
  (reverse-polarity protection) on a `diode` category landing.
  Cross-check whether `actives.py` ships a diode profile and whether
  the rule catalog has E9 active as ERROR or still as WARN. Bucket 1
  if shipped and E9 promoted; bucket 2 if shipped with E9 still gated;
  bucket 3 if not shipped and gate still tracking the absence.
- **Transistors.** TASK-120 / TASK-129 (EPIC-014) shipped
  `bjt_npn`/`bjt_pnp` and two CE-amplifier kernel rules. Bucket 1
  expected — confirm and link to EPIC-014 in the verdict.
- **ICs beyond MCU.** TASK-121 / TASK-122 shipped `ic/555` and
  `ic/opamp_dual_supply`. Bucket 1 expected.
- **Audio signal conditioning.** Dossier originally excluded this;
  hypothesis from IDEA-012 is that it has softened. Walk the
  archived [IDEA-009](../../ideas/archived/idea-009-active-device-profiles-and-multi-page-renderer.md)
  to see whether op-amp landing changes the bucket.

Cross-reference the archived
[IDEA-009](../../ideas/archived/idea-009-active-device-profiles-and-multi-page-renderer.md)
before spawning anything new in the actives space — its closure
probably resolves several dossier rows. **Don't spawn duplicates of
already-archived IDEAs.**

## Acceptance Criteria

- [ ] One analysis row per §5.3 dossier backlog entry; bucket
      assigned.
- [ ] Diode-category row carries explicit E9-severity verdict
      (ERROR vs WARN) sourced from the rule catalog.
- [ ] Transistor and IC rows link to the closing TASK-NNN from
      EPIC-014 in the verdict column.
- [ ] Any bucket-4 row has a spawned IDEA-NNN file linked from the
      verdict — and a one-line note confirming the spawn isn't
      duplicating IDEA-008 or IDEA-009 (already archived).

## Test Plan

No automated tests required — change is documentation / analysis.

Manual verification:

1. Open `src/circuitsmith/components/` and confirm every shipped
   component file is referenced in at least one row of the
   Components sub-table.
2. Confirm E9's catalog severity matches what the diode row says.

## Notes

- The hardest call here is the diode row's bucket. If diodes ship
  but E9 is still WARN, that's a real reduced-scope verdict
  (bucket 2) and a potential bucket-4 candidate ("promote E9 to
  ERROR now that the gate is unblocked"). Decide based on whether
  the dossier-stated promotion criterion ("diode category lands")
  was actually a sufficient condition or whether downstream tests
  also need to land.
- Skip the dossier's "components we don't ship by design" rows
  (e.g. relays, mechanical switches) — those are excluded-section
  items handled by Step 0 of IDEA-012 and don't need a row here
  unless the exclusion has softened.
