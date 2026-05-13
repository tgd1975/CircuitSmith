---
id: TASK-102
title: Inventory all .md docs and bucket by audience and freshness
status: open
opened: 2026-05-13
effort: Small (<2h)
complexity: Medium
human-in-loop: Clarification
epic: post-epic-006-doc-audit
order: 1
---

## Description

Before any rewriting can happen, the audit needs to know what it's
working with. This task produces a single working artefact —
`docs/developers/_doc-audit-inventory.md` (underscore-prefixed, not
linked from indexes) — listing every `.md` file in the repo with
two classifications:

- **Audience**: `builder`, `developer`, `contributor`, `user`,
  `mixed`. Mixed is acceptable for files like `README.md` that
  genuinely serve multiple audiences.
- **Freshness**: `pre-epic-001` (written when the repo was
  concept-stage), `mid-epic` (written during EPIC-001 through
  EPIC-005), `epic-006` (current shape), `post-epic-006` (written
  by this audit or by EPIC-011 / EPIC-012). Use git blame on the
  *first* commit of the file as the freshness signal; if the file
  has been rewritten substantially since, override with judgment.

The inventory also flags two cross-cutting issues:

- **Orphans** — files that no other file links to. Often these are
  notes that should be deleted or merged.
- **Duplicate coverage** — pairs / triples of files that cover the
  same topic at different levels of fidelity. Common pattern:
  one paragraph in the README, a section in CONTRIBUTING, a full
  doc in `docs/developers/`. Mark them so TASK-104 (voice
  unification) can collapse them.

Output table columns:

| Path | Audience | Freshness | Lines | Last-substantive-edit | Orphan? | Duplicate-coverage-of |

The inventory is **input** to TASK-103 (drift sweep), TASK-104
(voice), and TASK-105 (cross-refs). Without it, those tasks
re-derive the same data three times.

## Acceptance Criteria

- [ ] `docs/developers/_doc-audit-inventory.md` exists and lists
      every `.md` file in the repo.
- [ ] Every entry has audience, freshness, line count, and
      last-substantive-edit-date.
- [ ] Orphans flagged; duplicate-coverage pairs cross-linked.

## Test Plan

No automated tests required — change is working document.

Manual verification:

1. `find . -name "*.md" -not -path "./node_modules/*"` row count
   matches the inventory's row count.
2. Spot-check 5 random entries: audience and freshness reasonable.

## Notes

- The freshness classification is the load-bearing one. The whole
  point of this epic is that the system *changed* under the docs;
  pre-EPIC-001 prose is the first thing to audit.
- The underscore-prefixed filename mirrors TASK-084's testing
  inventory. Same reason: keep working documents out of the
  audience-facing index.
- This task can start the moment EPIC-006 closes — it has no
  prerequisites within EPIC-013.
