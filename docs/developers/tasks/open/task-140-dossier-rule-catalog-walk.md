---
id: TASK-140
title: Walk the IDEA-001 rule-catalog dossier against the shipped catalog size and shape
status: open
opened: 2026-05-15
effort: Small (<2h)
complexity: Medium
human-in-loop: No
epic: dossier-gap-analysis
order: 7
prerequisites: [TASK-134]
---

## Description

Walk
[`idea-001.rule-catalog.md`](../../ideas/archived/idea-001.rule-catalog.md)
against the in-repo catalog (path located in TASK-134's
orientation — most likely
`src/circuitsmith/schema/rules.json` or a sibling).

The dossier targets a **30–50-entry rule catalog**. EPIC-014's
TASK-133 final pass reported the catalog at 27 codes
(S1–S7 + E1–E22) plus 19 kernel rules. Decide which counts
matter for the dossier's ceiling:

- If the ceiling refers to **ERC checks only** (S/E codes): 27
  codes vs the 30–50 target — under-ceiling, bucket 1.
- If the ceiling refers to **all classification rules** (ERC +
  kernel canonical-slot rules): 27 + 19 = 46 — within the 30–50
  band, bucket 1.
- If the ceiling refers to **the JSON catalog file specifically**
  (only ERC codes, in
  `src/circuitsmith/schema/rules.json`): 27 — bucket 1.

For each interpretation, write one row into the **Rule catalog**
sub-table of `docs/developers/_dossier-gap-analysis.md` with the
count, the ceiling, and a verdict. The "Aspect" column
distinguishes the three interpretations so the walk doesn't
conflate them.

The load-bearing question is whether the **ceiling is still
load-bearing**:

- **Bucket 1** — count is within range, ceiling hasn't changed
  ERC behaviour, fine as-is.
- **Bucket 2** — count exceeds 50 (it does not, but verify); the
  ceiling was aspirational, no follow-up.
- **Bucket 3** — ceiling is a gate (ERC behaviour changes at the
  boundary). This is unlikely — the ceiling was never enforced —
  but verify by grepping `src/circuitsmith/` for any reference to
  the 30 / 50 constants.

## Acceptance Criteria

- [ ] 3 rows in the Rule-catalog sub-table (one per interpretation
      of the 30–50 ceiling).
- [ ] Each row carries the current count from the actual catalog
      file (verified via Read, not memory).
- [ ] Verdict on whether the ceiling is load-bearing or
      aspirational, with `grep` evidence for the latter.

## Test Plan

No automated tests required — change is documentation / analysis.

Manual verification:

1. Open the rule catalog file (path from TASK-134's orientation
   notes) and count the codes manually — matches the sub-table.
2. `grep -rn '30.*50\|catalog.*size' src/circuitsmith/` should
   return zero hits referencing the ceiling as an enforced
   threshold.

## Notes

- The 30–50-entry target was a sizing aspiration, not a hard
  ceiling — confirmed by EPIC-014 shipping 27 codes without
  triggering any "catalog too small" path. This walk just records
  the verdict so future contributors don't re-litigate.
- If the count somehow exceeds 50, that's a real signal — the
  catalog should be sliced into category-specific files. Unlikely
  given current counts, but the walk should be prepared to spawn
  a bucket-4 IDEA if it does.
