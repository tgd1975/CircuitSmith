---
id: TASK-134
title: Walk the IDEA-001 phase plan against shipped 0.1.0 + scaffold the analysis table
status: closed
closed: 2026-05-15
opened: 2026-05-15
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: Clarification
epic: dossier-gap-analysis
order: 1
---

## Description

First task of the dossier walk. Two responsibilities:

1. **Orient and scaffold.** Re-read
   [`idea-001-circuit-skill.md`](../../ideas/archived/idea-001-circuit-skill.md)
   end-to-end. Locate the in-repo rule catalog (candidates:
   `src/circuitsmith/schema/rules.json` or any
   `docs/developers/rules/*` doc — record the path in TASK-140's
   notes when found). Create the working doc at
   `docs/developers/_dossier-gap-analysis.md` (underscore-prefixed
   so the indexes skip it, mirroring TASK-102's
   `_doc-audit-inventory.md`) and seed it with this scaffold:

   ```markdown
   ## Analysis table

   ### Phase plan (idea-001-circuit-skill.md)
   | Phase | Bucket | Verdict / evidence / spawned IDEA |
   |---|---|---|

   ### Components (idea-001.components.md)
   | Dossier §5.3 row | Bucket | Verdict / evidence / spawned IDEA |
   |---|---|---|

   ### YAML format (idea-001.yaml-format.md)
   | Schema construct | Bucket | Verdict / evidence / spawned IDEA |
   |---|---|---|

   ### Layout engine (idea-001.layout-engine-concept.md)
   | Subsystem | Bucket | Verdict / evidence / spawned IDEA |
   |---|---|---|

   ### ERC engine (idea-001.erc-engine.md)
   | Check | Shipped? | Severity matches? | Bucket | Notes |
   |---|---|---|---|---|

   ### Exporters (idea-001.exporters.md)
   | Exporter row | Bucket | Verdict / evidence / spawned IDEA |
   |---|---|---|

   ### Rule catalog (idea-001.rule-catalog.md)
   | Aspect | Bucket | Verdict |
   |---|---|---|

   ### Skill packaging (idea-001.skill-packaging.md)
   | Acceptance test / row | Bucket | Verdict / evidence / spawned IDEA |
   |---|---|---|
   ```

2. **Walk the phase plan.** For each of Phases 1 through 7 in the
   dossier's phase plan, write one row into the **Phase plan**
   sub-table:
   - Phase 1 — kernel-and-rule-bound layout — bucket assignment + verdict.
   - Phase 2 — schemdraw renderer — same.
   - Phase 2b — AI placer — bucket 3 if gate-evidence supports it.
     **Must** cite `grep -c 'provenance\.escalations' $(find . -name 'meta.yml')`
     across the rendered `docs/users/examples/` gallery and the
     tutorial output. Note whether any escalation flags the
     kernel-failure modes the dossier names (`no-canonical-rule`,
     `density-too-high`, etc.).
   - Phase 3 — ERC + BOM — same.
   - Phase 4 — netlist + KiCad export — same.
   - Phase 5 — Markdown integration — note that the IDEA-022
     ordering dependency lived in AwesomeStudioPedal, not here, so
     the contract needs reframing or dropping (per the idea's
     "Pipeline contracts that drifted" hypothesis).
   - Phase 6 — skill packaging + acceptance — same.
   - Phase 7 — standalone-repo extraction — per the idea's hypothesis:
     PyPI ship in TASK-080 packaged the `circuitsmith` Python module,
     not the `.claude/skills/circuit/` directory. The skill directory
     is still consumed by-copy elsewhere. Record verdict as
     "deferred-by-default, not redundant" (bucket 3) unless the walk
     surfaces evidence to the contrary.

3. **Spawn bucket-4 IDEAs immediately.** If any phase comes out
   bucket-4, scaffold the follow-up IDEA via `/ts-idea-new`
   *before* moving on. Don't batch the spawns to the end of the task.

## Acceptance Criteria

- [ ] `docs/developers/_dossier-gap-analysis.md` exists and carries
      the eight-sub-table scaffold listed above.
- [ ] Phase-plan sub-table has 7 rows (one per phase) plus an
      explicit row for Phase 2b's gate evidence.
- [ ] Phase 2b row cites the `provenance.escalations` corpus count
      (zero or non-zero, with file paths if non-zero).
- [ ] Phase 5 row notes the AwesomeStudioPedal IDEA-022 reframing.
- [ ] Phase 7 row records the PyPI-vs-skill-directory verdict.
- [ ] Any bucket-4 rows have spawned IDEA-NNN files in
      `docs/developers/ideas/open/` and linked from the analysis row.

## Test Plan

No automated tests required — change is documentation / analysis.

Manual verification:

1. Read the 7+ phase rows; every row has a bucket (1/2/3/4) and a
   one-line verdict.
2. Run `grep -rl 'provenance.escalations' docs/users/examples/`
   yourself; row count matches the evidence cited in the Phase 2b row.

## Notes

- This task is the **only** one in the epic that creates the
  working-doc scaffold. Subsequent tasks (135..141) extend the
  existing sub-tables in place inside
  `docs/developers/_dossier-gap-analysis.md`.
- Step 0 of IDEA-012's implementation plan (orientation, locate the
  rule catalog, sample `meta.yml` files) folds into this task as
  setup — there is no separate orientation task.
- The Phase 5 reframing is the most likely source of an
  ambiguity-resolution moment. If the IDEA-022 dependency is
  genuinely stale (the Markdown integration shipped via EPIC-005's
  skill output, not via the dossier's MkDocs path), the row simply
  documents that and ends. No new IDEA needed for that path.
- The Phase 2b verdict is the load-bearing one for the whole walk:
  if escalations actually exist, that's a bucket-4 spawn (new AI
  placer IDEA); if not, bucket-3 with a frozen gate condition.
