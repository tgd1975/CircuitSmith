---
id: TASK-138
title: Walk the IDEA-001 ERC dossier check-by-check against the shipped erc_engine
status: open
opened: 2026-05-15
effort: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: dossier-gap-analysis
order: 5
prerequisites: [TASK-134]
---

## Description

Walk
[`idea-001.erc-engine.md`](../../ideas/archived/idea-001.erc-engine.md)
against the shipped
[`src/circuitsmith/erc_engine.py`](../../../../src/circuitsmith/erc_engine.py).
The dossier defines schema checks **S1–S5** and electrical checks
**E1–E10** — 15 codes total. EPIC-014 extended the catalog to
S1–S7 plus E1–E22 (27 codes). The dossier scope is the original
15; the new codes are noted for context but **not** bucket-assigned
here (they are EPIC-014 deliverables, not dossier gaps).

Heed the `/co-erc-engine` invariants if editing `erc_engine.py` —
but this task is **read-only** with respect to the engine.

For each of S1–S5 and E1–E10, write one row into the **ERC engine**
sub-table of `docs/developers/_dossier-gap-analysis.md` with these
columns:

| Check | Shipped? | Severity matches dossier? | Bucket | Notes |

- **Shipped?** — Yes / No / Reduced-scope.
- **Severity matches dossier?** — compare the dossier's
  ERROR/WARN/INFO classification against the catalog in
  `src/circuitsmith/schema/rules.json` (the canonical severity
  table). Severity mismatches are bucket-2 (reduced scope) unless
  there's a clear gate (e.g. E9 + diode category from TASK-135 →
  bucket 3).
- **Bucket** — per the four-bucket scheme.
- **Notes** — for E9 specifically, cite the TASK-135 diode-row
  verdict explicitly. For any check where the shipped
  implementation diverges from the dossier's pseudo-code, name the
  divergence in one line.

Special attention:

- **E9 (reverse-polarity protection)** — the dossier gates ERROR
  promotion on the `diode` category landing. Coordinate with
  TASK-135's diode row: same evidence, same bucket. Don't
  double-spawn the IDEA.
- **S1–S5 (schema checks)** — these are validator-level, not
  engine-level. Confirm whether each shipped in
  `circuitsmith/schema/validator.py` (or wherever schema-validation
  lives) and not the engine itself.

## Acceptance Criteria

- [ ] 15-row sub-table: one row per S1–S5 / E1–E10 check.
- [ ] Severity-match column populated for every row.
- [ ] E9 row aligns with TASK-135's diode-category verdict (same
      bucket, cross-linked).
- [ ] Severity-mismatch rows are either bucket 2 (fine as-is) or
      bucket 4 (spawn) — never left ambiguous.
- [ ] Any bucket-4 row has a spawned IDEA-NNN file linked from the
      verdict.

## Test Plan

No automated tests required — change is documentation / analysis.

Manual verification:

1. Count rows: 5 (S1–S5) + 10 (E1–E10) = 15. No more, no fewer.
2. Open `src/circuitsmith/schema/rules.json` and confirm the
   severity for each S/E code matches what the row says.

## Notes

- The walk is **dossier-scope only**: the 12 new codes EPIC-014
  added (S6, S7, E11–E22) belong to EPIC-014's implementation log,
  not IDEA-012's gap analysis. Cite them in the notes column when
  relevant for context (e.g. "E11–E14 — sub-block ERC, shipped by
  EPIC-014, out of dossier scope").
- TASK-141 (skill packaging) depends on this task's verdicts via
  the dossier's "ERC clean on the five acceptance circuits" promise
  in the skill-packaging file. Make sure severity verdicts are
  defensible — they feed forward.
