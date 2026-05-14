---
id: TASK-133
title: Component-skill docs final pass
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Small (<2h)
complexity: Junior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 24
prerequisites: [TASK-132, TASK-119]
---

## Description

Closes EPIC-014 with a docs-only final pass. Most of the
component-skill docs were updated incrementally as the upstream
tasks landed (TASK-120/121/122 each added a row;
TASK-119 added the sub-block grammar; TASK-126 added the
cross-page label glyph description). This task is the proofreading
and cross-reference audit pass.

Specifically:

- Confirm
  [`.claude/skills/circuit/docs/components.md`](../../../.claude/skills/circuit/docs/components.md)
  has an *Active devices* table (rows for `bjt_npn`, `bjt_pnp`)
  and an *ICs* table (rows for `ic/555`, `ic/opamp_dual_supply`)
  with consistent column conventions matching the existing
  `passives.py` / `mcus.py` tables.
- Confirm
  [`.claude/skills/circuit/docs/layout.md`](../../../.claude/skills/circuit/docs/layout.md)
  covers the four new kernel rules (R+C low-pass, R+C high-pass,
  C+C decoupling pair, R+R divider) and the `pages:` partition.
- Confirm
  [`.claude/skills/circuit/docs/index.md`](../../../.claude/skills/circuit/docs/index.md)
  cross-references the new capabilities in the "what this skill
  can do" overview.
- Confirm
  [`.claude/skills/circuit/docs/erc-checks.md`](../../../.claude/skills/circuit/docs/erc-checks.md)
  has rows for every ERC rule landed in TASK-117 / TASK-123 /
  TASK-127 (11 new rules total).
- Confirm the *Cross-references* sections of the (already
  archived) IDEA-008 and IDEA-009 still resolve from their
  `archived/` location; the ideas were archived at epic open per
  the `/ts-epic-new` convention.

## Acceptance Criteria

- [ ] All four skill-docs files (components.md, layout.md, index.md, erc-checks.md) reflect the EPIC-014 capabilities consistently.
- [ ] IDEA-008 and IDEA-009 (archived at epic open) carry an Archive Reason naming EPIC-014.
- [ ] `markdownlint-cli2` passes on every edited file.
- [ ] The gallery README index page references EPIC-014, not IDEA-008/009.

## Test Plan

No automated tests required — change is documentation. Final-pass
audit is a manual walk through the four skill-docs files and the
two archived idea files.

Manual verification:

1. Read each skill-docs file end-to-end as a new contributor; no
   reference to IDEA-008 / IDEA-009 should remain as
   "future work" — every such reference must now point at
   EPIC-014 (closed) or at the actual implementing module.
2. The 11 new ERC rules are catalogued in `erc-checks.md` with
   their final assigned codes.
3. `markdownlint-cli2` passes.

## Documentation

This task **is** the documentation pass. The files touched are
listed in the description.

## Prerequisites

- **TASK-132** — last gallery re-attempt; all artefacts must
  exist before the cross-reference audit is meaningful.
- **TASK-119** — sub-block docs landed; the audit verifies that
  pass and the active-device pass cohere with each other.

## Notes

- This task is intentionally narrow — proofreading only. If the
  audit surfaces a genuine documentation gap (not a typo, but a
  missing chapter), file a follow-up task rather than expanding
  this one.
