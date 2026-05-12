---
id: TASK-072
title: Author docs/developers/BRANCH_PROTECTION_CONCEPT.md documenting the protection ruleset
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: developer-docs-governance
order: 11
---

## Description

CircuitSmith does not currently enforce branch protection on `main`
via GitHub's mechanism — the project's branch policy (no direct
commits to main, squash-merge feature branches) is enforced
client-side via `/check-branch` and `/commit`. Adding GitHub's
server-side enforcement is the next layer: even a deliberately
malicious or careless push from a contributor without local tooling
cannot bypass the rules.

This task authors the **concept doc** that records the protection
ruleset and its rationale. The follow-on task (TASK-073) applies the
config to the GitHub repo.

Ruleset (decided in conversation with the project owner — solo +
autonomous-loop posture, contributor #2 not yet on the horizon):

| Rule | Setting | Rationale |
|---|---|---|
| Require status checks | Yes — `Test (ubuntu-latest)`, `Test (windows-latest)` | CI must be green before merge |
| Require branches up to date | Yes (strict) | No merge of stale branches |
| Require PR review | **No** | Solo project — admin-self-approval deadlock would block every solo merge. Trigger to flip on: contributor #2 lands. |
| Enforce for administrators | **No** | Owner needs to land hot-fixes without bypass |
| Allow force pushes | No | Reflog-recovery property per CLAUDE.md `## Branch merges — squash, not fast-forward` and AUTONOMY.md |
| Allow deletions | No | `main` is permanent |
| Require linear history | Yes | Matches the squash-merge-only policy already in CLAUDE.md |

Model: AwesomeStudioPedal's
[`BRANCH_PROTECTION_CONCEPT.md`](../../../../../AwesomeStudioPedal/docs/developers/BRANCH_PROTECTION_CONCEPT.md)
(79 lines). Adapted for the solo posture as described above.

## Acceptance Criteria

- [ ] `docs/developers/BRANCH_PROTECTION_CONCEPT.md` exists and is linked from CONTRIBUTING.md and COMMIT_POLICY.md (TASK-071).
- [ ] The ruleset table is reproduced with the rationale per row as above.
- [ ] The "trigger to revisit" condition is documented explicitly: when contributor #2 joins the repo, flip the PR-review-required rule on (with admin-enforcement still off).
- [ ] The doc names the implementation path: `gh api -X PUT /repos/{owner}/{repo}/branches/main/protection` with the JSON body the rules translate to. Exact command lands in TASK-073's body.
- [ ] Branch-naming conventions are recorded with examples (per CLAUDE.md `## Branch merges — squash, not fast-forward`): `release/epic-NNN-<slug>`, `chore/<scope>`, `fix/<scope>`.
- [ ] The doc states explicitly that client-side enforcement (`/check-branch`, `/commit`) and server-side enforcement (GitHub branch protection) are **complementary**, not redundant — different threat models.

## Test Plan

No automated tests. Verify by spot-check: the ruleset matches what
TASK-073 will actually apply; the trigger condition is unambiguous.

## Prerequisites

None — the ruleset is decided.

## Notes

This task and TASK-073 are deliberately split. The doc lands first
and is immutable history of the *intent*; the config-apply
(TASK-073, HIL: Main) is the *action* that publishes that intent to
the remote. A contributor reading the doc one year from now sees the
original rationale even if the config has drifted; a maintainer
auditing the config has the doc as the source of truth.

The "require PR review: No" choice is the load-bearing solo-mode
concession. Document the alternative ("require 1 approving review +
enforce-admins off") and why it was rejected — it is workable but
adds a per-commit click-through that the project owner did not
prefer at this stage. Keeping the alternative recorded means the
flip is a one-line edit when contributor #2 joins.
