---
id: EPIC-013
name: post-epic-006-doc-audit
title: Post-EPIC-006 Documentation Audit and Rewrite
status: open
opened: 2026-05-13
closed:
assigned:
branch: release/epic-013-post-epic-006-doc-audit
---

Seeded by IDEA-007 (Intensive review and rework of the documentation after EPIC-006).

Once EPIC-006 lands, CircuitSmith has gone through the full arc from
concept-stage dossier to a working schematic-generation pipeline.
The documentation in `docs/` has accumulated in lockstep with that
work — meaning prose written for an earlier shape of the system is
still sitting next to prose written for the final shape. This epic
runs the end-to-end pass that brings everything into one voice, one
mental model, and one canonical structure.

**Strictly post-EPIC-006.** This epic is opened now to lock in the
scope, but its tasks should not start until EPIC-006 closes. Doing
the pass during EPIC-006 means chasing a moving target; doing it
well after means rediscovering all the small drifts a second time.

Deliverables:

- **Inventory** — a one-time catalog of every `.md` file in the
  repo, bucketed by audience (builder / developer / contributor /
  user) and by freshness (pre-EPIC-001, mid-epic, post-EPIC-006).
- **Drift sweep** — surfaces stale CLI flags, retired scripts,
  moved filepaths, "planned" features that shipped, and examples
  that no longer parse.
- **Voice unification** — picks a canonical voice (likely the one
  used in EPIC-005/006 docs, written with the full system in mind)
  and brings the earlier docs forward to match.
- **Cross-reference audit** — every internal link, every reference
  to `TASK-NNN` / `EPIC-NNN` / `IDEA-NNN`, every code-path mention.
- **Alignment passes** — coordinate with EPIC-011 (test plan) and
  EPIC-012 (tutorial / gallery) so the three layers tell the same
  story.
- **Dossier annotation** — the archived IDEA-001 dossier gets
  inline "what shipped" / "what didn't" annotations so it stays
  useful as historical context.
- **Final entry-point pass** — `README.md` and the top-level
  pointers reflect the post-EPIC-006 reality.

Cross-references:

- **EPIC-006 — circuit skill packaging**: closure of EPIC-006 is
  the operational trigger for this epic. The first task here
  (TASK-102, inventory) cannot start until EPIC-006's last task
  closes.
- **EPIC-011 — test plan**: TASK-107 audits the "how it's tested"
  sections in narrative docs against the test plan from EPIC-011.
- **EPIC-012 — tutorial and gallery**: TASK-106 audits the
  reference docs against the tutorial / gallery to make sure they
  tell consistent stories.

Sequencing inside the epic follows the natural review pass:
inventory → drift sweep → voice → cross-refs → tutorial alignment →
test-plan alignment → dossier annotation → entry-point pass. The
two alignment tasks (106, 107) sit in the middle of the order
because they cannot start until the dependencies in EPIC-011 /
EPIC-012 have *enough* shape to audit against — not full closure of
those epics, just enough that their canonical artefacts exist.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
