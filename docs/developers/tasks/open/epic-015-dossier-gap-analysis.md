---
id: EPIC-015
name: dossier-gap-analysis
title: Walk the IDEA-001 dossier vs shipped 0.1.0 — gap analysis and follow-up spawns
status: open
opened: 2026-05-15
closed:
assigned:
branch: release/epic-015-dossier-gap-analysis
---

Seeded by IDEA-012 (Revisit the original IDEA-001 dossier — gap
analysis against shipped 0.1.0).

CircuitSmith 0.1.0 shipped to PyPI on the back of EPIC-001..006 plus
the packaging wave (TASK-080) and the renderer-v2 epic (EPIC-014).
That is the v0.1 slice of the inherited IDEA-001 dossier — by design.
The dossier itself stages further work behind explicit gates (Phase
2b AI placer, Phase 7 standalone-repo extraction) and lists a
Deliberately Excluded section that doubles as a "not yet, but maybe
later" wishlist. After eight months of real implementation the shape
of what is missing is no longer the same as what the dossier said
was deferred — some "excluded" items have become plausible, some
gate prerequisites have or have not been hit, and some Phase 1–6
work shipped with reduced scope.

This epic executes the dossier walk that IDEA-012 bookmarks. Each
task walks one of the nine dossier files (or one of the cross-cutting
close-out steps), bucket-assigns every named deliverable into the
four-bucket scheme below, and writes the verdict into the working
doc's matching sub-table. Bucket-4 rows spawn follow-up IDEAs
immediately, not in batch.

## The four-bucket classification scheme

Each named deliverable in the dossier gets exactly one bucket:

1. **Shipped in 0.1.0 as specified** — close the loop, no follow-up.
2. **Shipped in 0.1.0 with reduced scope** — note the delta; decide
   whether the gap is worth a follow-up idea or is fine as-is.
3. **Deferred by design, gate not yet tripped** — confirm the gate
   condition is still the right one (e.g. Phase 2b's "kernel-failure
   modes on real use" trigger) and capture the evidence (e.g.
   `provenance.escalations` corpus count).
4. **Deferred by design, gate now tripped or trip-able** — spawn a
   follow-up IDEA-NNN (or epic, if scope is clear) and link from the
   analysis row.

## Deliverable location

The analysis table lives in a working doc at
[`docs/developers/_dossier-gap-analysis.md`](../../_dossier-gap-analysis.md)
— underscore-prefixed so the indexes skip it, mirroring TASK-102's
`_doc-audit-inventory.md`. TASK-134 scaffolds the eight sub-tables
there; TASK-135..141 each extend their respective sub-table; TASK-142
runs the coverage check against the working doc.

IDEA-012 was archived at the moment this epic was elevated (the
project convention: an idea archives on elevation, not on epic
closure). Its body now holds an `## Archive Reason` pointer to this
epic and to the working doc — the analysis no longer grows inside
the idea, even though the idea's original deliverable spec proposed
that.

## Task ordering and dependencies

The phase-plan walk (TASK-134) goes first because it produces the
analysis-table scaffold every other task writes into and because
Phase 7's verdict feeds the skill-packaging row (TASK-141). All
file-walk tasks (TASK-135..141) depend on the scaffold. TASK-142
(cross-repo cleanup + close-out) gates on everything else being
done.

```
TASK-134 (phase plan + orient)
  ├─ TASK-135 (components)
  ├─ TASK-136 (yaml format)
  ├─ TASK-137 (layout engine)
  ├─ TASK-138 (ERC engine)
  ├─ TASK-139 (exporters)
  ├─ TASK-140 (rule catalog)
  └─ TASK-141 (skill packaging)  [also depends on TASK-138]
                ↓
        TASK-142 (cross-repo cleanup + close-out)
```

## Expected scale

The idea forecasts roughly 60–90 analysis-table rows across the nine
dossier files (5–15 per file). Most are bucket-1 one-liners; the
long tail is bucket-3 gate notes. **Bucket-4 spawns are expected to
be few** — the dossier was pruned hard at idea→epic conversion and
0.1.0 shipped most of what survived. If the epic produces more than
~5 new IDEAs, that's a signal something was missed in the original
conversion and warrants a discussion before mass-spawning.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
