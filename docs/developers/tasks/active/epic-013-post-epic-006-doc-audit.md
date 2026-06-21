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

## Implementation log

- 2026-06-21 — TASK-102 closed (effort actual Small) and TASK-103 closed
  (effort actual Medium). Inventory (`_doc-audit-inventory.md`) buckets all
  292 tracked `.md` files: 241 are records / ADRs / generated indexes /
  sidecars / skill-defs (out of voice scope), leaving ~51 prose docs
  enumerated by audience + freshness. Drift catalogue
  (`_doc-audit-drift.md`) logs 25 grep/Glob-verified items across 11 files —
  dominated by a "concept stage / nothing exists yet" cluster (README,
  ARCHITECTURE, CONTRIBUTING, CLAUDE, TESTING, users/*) and the
  `src/circuitsmith/` relocation aftermath (stale `from circuit.*` imports +
  `.claude/skills/circuit/` paths in TESTING.md and circuit-yaml.md).
- 2026-06-21 — **HIL boundary.** TASK-104 (voice unification) is Main-HIL
  and every later task (105–109) is gated on it; 108 and 109 are also
  Main-HIL. Autonomous progress ends here. `_doc-audit-hil-plan.md` lays out
  the canonical-voice decision, the README-scope decision, the per-task
  plan, and the batched review tempo for the maintainer to drive 104–109.
- 2026-06-21 — Maintainer gave the three gating decisions (voice **accepted**;
  README **full rewrite** at TASK-109; `TESTING.md` **stub-and-point** at
  TASK-107). TASK-104 closed (effort actual Small — the inventory showed most
  docs already canonical, so the voice pass touched only `ARCHITECTURE.md`
  plus a handful of concept-stage drift fixes, far under the Large estimate).
  Added the canonical-voice note to `CODING_STANDARDS.md`; removed the
  ARCHITECTURE status block and corrected its ERC ranges; fixed the
  concept-stage openers in `CONTRIBUTING.md`, `CLAUDE.md`, and `README.md`
  (README interim — full rewrite deferred to TASK-109). Drafts are on-branch
  for the maintainer's cold-read at review/merge. Proceeding to TASK-105.
- 2026-06-21 — TASK-105 closed (effort actual Medium — building the checker
  and tuning out false positives across 292 files took longer than the Small
  estimate). Shipped `scripts/check_doc_references.py`: a class-1 relative-link
  gate (frozen records, vendored skills, code fences, and lifecycle-folder
  drift excluded; ID / code-path / external-URL classes behind flags) with an
  11-case `tests/` suite, wired into CI, allow-listed, and documented
  (scripts/README, CI_PIPELINE). Fixed the ~17 broken links it surfaced —
  chiefly the `src/circuitsmith/` relocation aftermath in the circuit skill
  docs (`circuit-yaml.md`, `layout.md`) plus the user-doc links. Proceeding
  to TASK-106 / TASK-107.
- 2026-06-21 — TASK-106 closed (effort actual Small). Removed the stale
  EPIC-012 status notes in `users/README.md` and `tutorial/README.md`; added
  tutorial/gallery "See also" pointers to the three skill reference docs and
  a canonical-term glossary to `ARCHITECTURE.md`. Tutorial terminology
  scanned consistent with the reference docs — no disagreements to reconcile.
