---
id: TASK-103
title: Drift sweep — identify stale claims, retired scripts, and broken refs
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: post-epic-006-doc-audit
order: 2
prerequisites: [TASK-102]
---

## Description

The inventory from TASK-102 lists what exists. This task identifies
what is *wrong* — claims the docs make that no longer match the
code. Output is `docs/developers/_doc-audit-drift.md` (another
underscore-prefixed working doc) listing every drift item with:

- File and line reference.
- Drift class:
  - **Retired script** — prose mentions a script that no longer
    exists (`generate-schematic.py`, ad-hoc helpers from the
    pre-EPIC-001 era).
  - **Stale CLI flag** — flag named in docs no longer exists or has
    been renamed.
  - **Moved filepath** — `.claude/skills/circuit/` references that
    should be `src/circuitsmith/` post-relocation, etc.
  - **Shipped "planned" feature** — prose says "we plan to X" and
    X has shipped.
  - **Stale example** — code block that no longer parses or runs
    against the current schema / API.
  - **Broken internal link** — relative link target does not exist.
  - **Phantom TASK/EPIC/IDEA ref** — references a TASK/EPIC/IDEA
    ID that no longer exists (e.g. retired tasks).
- One-line note on the proposed fix.

Sweep technique: walk the inventory in freshness order
(pre-EPIC-001 first, working forward) and for each file:

1. Grep for the known retired scripts and renamed paths.
2. Open the file and read it against the current state of the
   code at the referenced locations.
3. Run any embedded examples (YAML, shell commands) that can be
   run cheaply.

This task does **not** fix the drift — it only catalogues it.
Fixes happen in TASK-104 (voice + structural rewrite, which
naturally subsumes drift fixes in rewritten files) and TASK-109
(final entry-point pass).

## Acceptance Criteria

- [ ] `docs/developers/_doc-audit-drift.md` exists with every drift
      item from a complete walk of the inventory.
- [ ] Each item has file/line, drift class, and proposed fix.
- [ ] No silent omissions — every file from the inventory must be
      either visited (drift items logged) or marked
      "scanned, no drift" in the drift doc.

## Test Plan

No automated tests required — change is working document.

Manual verification:

1. Cross-check the drift doc against the inventory: every file
   visited.
2. Spot-check 5 random drift items by reading the source and
   confirming the drift is real.

## Prerequisites

- **TASK-102** — the inventory tells this task which files to walk.

## Notes

- Drift catalogue, not fix list. Resist the urge to fix drift
  inline during this task — it doubles the review burden and
  blurs the audit/rewrite split.
- The "phantom TASK ID" check has a known false-positive pattern:
  retired tasks (TASK-043, -044, -045) are referenced legitimately
  from EPIC-006's body. Don't flag those; only flag references that
  expect the task to *still exist* as open / in-progress.
- The grep step should include `CHANGELOG.md` — released-CHANGELOG
  bullets are frozen and should not be drift-fixed, but Unreleased
  bullets are fair game.
