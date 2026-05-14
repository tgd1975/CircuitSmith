---
id: TASK-141
title: Walk the IDEA-001 skill-packaging dossier against the shipped skill and acceptance tests
status: open
opened: 2026-05-15
effort: Small (<2h)
complexity: Medium
human-in-loop: No
epic: dossier-gap-analysis
order: 8
prerequisites: [TASK-134, TASK-138]
---

## Description

Walk
[`idea-001.skill-packaging.md`](../../ideas/archived/idea-001.skill-packaging.md)
against the shipped skill at
[`.claude/skills/circuit/`](../../../../.claude/skills/circuit/) and
the EPIC-006 acceptance harness.

The dossier's **acceptance-tests list** is the load-bearing part —
five canonical circuits the skill must render end-to-end with ERC
clean. For each acceptance test:

- **Shipped?** — Yes / Superseded / Pending.
- **Superseded** means the test was replaced by EPIC-006's test
  harness (e.g. `tests/skills/test_circuit_skill.py`) or by
  EPIC-012's gallery regression script
  (`scripts/check_gallery_regression.py`).
- **Pending** means the test hasn't shipped and the dossier's
  promise is unfulfilled — bucket 3 or 4 depending on whether the
  gap is intentional.

The five canonical circuits per the dossier (verify the list during
the walk; the dossier may name fewer or different ones than
remembered):

1. Power-LED indicator.
2. Pull-up button + MCU pin.
3. Decoupled MCU power island.
4. I²C sensor + MCU.
5. (The fifth — check the dossier; might be voltage divider, USB-C
   passthrough, or an RC filter.)

Cross-reference TASK-128..132 from EPIC-014 — those re-attempted
five gallery entries through the renderer-v2 pipeline. Most rows
will be bucket 1 with both an EPIC-006 acceptance link and an
EPIC-014 gallery link.

**Phase 7 dovetail.** This task depends on TASK-134's Phase 7
verdict (skill-directory-still-by-copy, not extracted). Confirm
the skill-packaging row's verdict aligns with that Phase 7 verdict —
they tell the same story: skill packaging shipped, skill
extraction did not.

**ERC-clean check.** The dossier's acceptance criterion includes
"ERC clean" on every canonical circuit. Coordinate with TASK-138's
severity verdicts — any check whose severity diverged from the
dossier may cause an acceptance circuit to throw a warning the
dossier didn't anticipate. Note such cases in the row.

## Acceptance Criteria

- [ ] One analysis row per dossier-named acceptance test (likely
      5).
- [ ] Each row carries Shipped / Superseded / Pending status with
      a link to the EPIC-006 or EPIC-014 task that owns the
      coverage.
- [ ] Skill-packaging row aligns with TASK-134's Phase 7 verdict
      (same direction, no contradictions).
- [ ] Any row whose ERC-clean criterion now produces a warning
      it didn't originally cites the relevant E-code and TASK-138
      row.
- [ ] Any bucket-4 row has a spawned IDEA-NNN file linked from the
      verdict.

## Test Plan

No automated tests required — change is documentation / analysis.

Manual verification:

1. Run the gallery regression script
   (`python scripts/check_gallery_regression.py`) — confirms the
   five (or however many) shipped circuits render identically.
   Note in the analysis that the regression script supersedes the
   dossier's manual-render acceptance check.
2. Open `.claude/skills/circuit/SKILL.md` and confirm it still
   matches the dossier's "skill consumed by-copy" intent.

## Notes

- The skill-packaging row depends on TASK-134 (Phase 7 verdict)
  and TASK-138 (severity verdicts) — that's why prerequisites lists
  both. Activating this task before the prereqs are closed will
  leave verdicts unresolved.
- The dossier may sketch an "auto-publish skill to PyPI" path; the
  shipped reality is that the Python module is on PyPI but the
  skill directory is by-copy. Bucket 2 with the explicit verdict
  "skill remains by-copy by design; PyPI ships the module only".
