---
id: TASK-137
title: Walk the IDEA-001 layout-engine concept against the shipped kernel + router
status: open
opened: 2026-05-15
effort: Small (<2h)
complexity: Medium
human-in-loop: No
epic: dossier-gap-analysis
order: 4
prerequisites: [TASK-134]
---

## Description

Walk
[`idea-001.layout-engine-concept.md`](../../ideas/archived/idea-001.layout-engine-concept.md)
against the shipped layout engine. The companion
[`idea-001.layout-engine-discussion.md`](../../ideas/archived/idea-001.layout-engine-discussion.md)
is rationale-only — skim for context, **do not** generate rows from
it.

For each named subsystem in the concept document, write one row
into the **Layout engine** sub-table of
`docs/developers/_dossier-gap-analysis.md`:

- **Kernel dispatch** — `src/circuitsmith/layout/kernel.py`. The
  rule-based dispatch shipped per EPIC-002 plus EPIC-014's nine new
  rules (IDs 11–19). Bucket 1 expected.
- **Router** — `src/circuitsmith/layout/router.py`. The L-shaped /
  Manhattan router shipped per EPIC-002. Cross-check against the
  dossier's "wire jog" and "via insertion" requirements — bucket 1
  or 2 depending on coverage.
- **Rubric scorer** — the dossier sketches a confidence-score
  rubric that gates kernel escalations. Locate the implementation
  (likely
  `src/circuitsmith/layout/kernel.py:_score_placement` or similar)
  and bucket-assign.
- **Page-break logic** — multi-page rendering shipped per EPIC-014
  TASK-124..127 (`pages:` partition, cross-page labels, cross-page
  ERC). Bucket 1 with the EPIC-014 verdict.
- **Canonical-slot table** — the dossier's per-rule canonical-slot
  promise. EPIC-014 TASK-133 extended this from 8 rows to 19. Check
  `docs/developers/layout.md` and confirm coverage matches the rule
  catalog count from TASK-140.

Cross-reference EPIC-014's closing tasks (TASK-110..133) before
spawning anything — most of the layout-engine concept is now
shipped.

## Acceptance Criteria

- [ ] One analysis row per named subsystem in the concept document;
      bucket assigned.
- [ ] Page-break row links to EPIC-014 TASK-124..127.
- [ ] Canonical-slot row cites the current count (post-EPIC-014: 19
      rules) and confirms coverage matches the rule catalog.
- [ ] Rubric scorer row identifies the in-repo implementation file
      and confirms whether escalation reasons land in
      `meta.yml.provenance.escalations` (cross-check with Phase 2b's
      evidence base from TASK-134).
- [ ] Any bucket-4 row has a spawned IDEA-NNN file linked from the
      verdict.

## Test Plan

No automated tests required — change is documentation / analysis.

Manual verification:

1. Open `src/circuitsmith/layout/` and confirm every subsystem
   named in the concept doc has a corresponding row.
2. Confirm the canonical-slot row's count matches
   `docs/developers/layout.md` (or wherever the table now lives).

## Notes

- The rubric scorer is the most likely place to surface a
  bucket-3-or-4 ambiguity: the dossier sketches it in detail but
  the shipped implementation may be coarser. Bucket 3 if "ships
  later when v0.1 produces real failure modes" is still the right
  framing (this dovetails with TASK-134's Phase 2b verdict);
  bucket 4 if escalations have actually appeared in the wild.
- The discussion file is intentionally excluded from row
  generation. Walking it would double-count rationale and produce
  spurious bucket-3 entries that the concept doc already covers.
