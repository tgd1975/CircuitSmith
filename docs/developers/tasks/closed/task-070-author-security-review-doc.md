---
id: TASK-070
title: Author docs/developers/SECURITY_REVIEW.md (script usage + reviewer checklist)
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: developer-docs-governance
order: 9
prerequisites: [TASK-055]
---

## Description

CircuitSmith already runs three security-review git hooks (post-merge,
pre-merge-commit, pre-rebase) via
[`scripts/security_review_changes.py`](../../../../scripts/security_review_changes.py) —
the mechanism exists, but there is no doc that explains (a) what the
script does, (b) how to read its output, (c) what a *human* reviewer
should look for when the script is silent, (d) how to bypass when
deliberate.

Two failure modes to address:

1. **The script runs, the contributor never looks at
   `.claude/security-review-latest.md`** because they do not know that
   file exists or what it contains. Silent reports are unread reports.
2. **The contributor relies on the script entirely and skips human
   review** of the diff. The script catches a pattern set; a
   reviewer's eyes catch the novel cases. Both layers are needed.

The doc fixes both: documents the script's surface, documents the
reviewer checklist for the human layer, documents the bypass policy
(`CS_SKIP_SECURITY_REVIEW=1` per CONTRIBUTING.md), and names the
escalation path when a real finding lands.

Model: AwesomeStudioPedal's
[`SECURITY_REVIEW.md`](../../../../../AwesomeStudioPedal/docs/developers/SECURITY_REVIEW.md)
(201 lines).

## Acceptance Criteria

- [x] `docs/developers/SECURITY_REVIEW.md` exists and is linked from CONTRIBUTING.md.
- [x] Script-usage section documents: what the three hooks check, when each fires, what `.claude/security-review-latest.md` contains, how to re-run on demand.
- [x] Reviewer-checklist section names at minimum: secrets in commits (.env, keys), `eval` / `exec` / `subprocess(shell=True)` patterns, path-traversal risks, dependency upgrades to unfamiliar packages, broad permissions in `.claude/settings.json`, new `Bash(...)` allowlist entries, gh-CLI calls with `--method PUT/DELETE`.
- [x] Bypass policy is recorded: `CS_SKIP_SECURITY_REVIEW=1` is logged; bypasses are reviewed in batch by the user, not normalised.
- [x] Escalation path: when the script or a reviewer finds something real, the doc names the action sequence (do not commit, file the finding as an open task tagged `security`, surface in the review packet).
- [x] The doc explicitly states it is **not** a substitute for OWASP / language-specific security training; it is the project-local convention layer above that.

## Test Plan

No automated tests. Manual: read each of the three hooks
(`scripts/git-hooks/`) and confirm the doc accurately describes each.
If the doc and the hook disagree, fix one or the other.

## Prerequisites

- **TASK-055** — the code-owner hook is the most analogous
  edit-time mechanism; the reviewer checklist explicitly states that
  code-owner reminders fire before edit time, security review fires
  after merge time, and the two layers are complementary.

## Notes

The "can't be too cautious" framing from the project owner is the
reason this doc lands now rather than at first-finding. A document
that exists before a finding lands gives the response a documented
shape; a document written *after* a finding tends to be a post-mortem,
not a guideline.

Keep the reviewer checklist short and **action-oriented** ("grep for
X, check for Y") rather than essay-style — checklists are for use
under time pressure.

## Sizing rationale

Medium because the reviewer checklist requires real thought (which
patterns to include, which to omit) rather than transcription. The
script-usage half is fast.
