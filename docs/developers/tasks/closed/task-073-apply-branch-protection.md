---
id: TASK-073
title: Apply GitHub branch protection on main per BRANCH_PROTECTION_CONCEPT.md
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: Main
epic: developer-docs-governance
order: 12
prerequisites: [TASK-072]
---

## Autonomy

`Main` — this task publishes state to the GitHub remote
(`gh api -X PUT /repos/.../branches/main/protection`). Per
[AUTONOMY.md § No-published-effect-without-approval](../../AUTONOMY.md#no-published-effect-without-approval),
the agent auto-prepares the command + payload but does not execute
without explicit per-invocation user approval.

## Description

Apply the branch-protection ruleset documented in TASK-072 to the
GitHub remote via the `gh api` CLI. This is the action half of the
TASK-072 / TASK-073 pair — TASK-072 records *what* and *why*; this
task does *the doing*.

Proposed command (subject to user-side approval at execution time):

```bash
gh api -X PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/tgd1975/CircuitSmith/branches/main/protection \
  -f required_status_checks.strict=true \
  -F 'required_status_checks.contexts[]=Test (ubuntu-latest)' \
  -F 'required_status_checks.contexts[]=Test (windows-latest)' \
  -F enforce_admins=false \
  -f required_pull_request_reviews= \
  -F restrictions= \
  -F allow_force_pushes=false \
  -F allow_deletions=false \
  -F required_linear_history=true
```

The exact JSON shape may need adjustment — `gh api` flag syntax for
nested null fields (`required_pull_request_reviews=null`) is finicky;
the doc lands the **intent**, the agent verifies the syntax against
the [GitHub REST API reference](https://docs.github.com/en/rest/branches/branch-protection)
at execution time.

## Acceptance Criteria

- [x] The `gh api` command is prepared in the task body with the exact JSON payload the ruleset translates to.
- [x] **User explicitly approves the command** at execution time — no `gh api -X PUT` runs without per-invocation approval.
- [x] After the command runs, `gh api /repos/tgd1975/CircuitSmith/branches/main/protection` returns the documented ruleset (verify by comparing the response to BRANCH_PROTECTION_CONCEPT.md's table).
- [x] CI context names match the actual job names from `.github/workflows/ci.yml` (`Test (ubuntu-latest)` / `Test (windows-latest)`). If the workflow's job names change later, the protection config must be updated in lockstep — recorded here as a tripwire for future ci.yml edits.
- [x] BRANCH_PROTECTION_CONCEPT.md is updated to reflect the as-applied configuration if it diverges from the documented intent. Verified no divergence; the doc as-written matches the API response 1:1.
- [ ] **Deferred to user** — A push attempt to `main` (deliberately, then immediately revert) confirms the rule fires from the server side. The agent cannot push to `main` (deny-listed in `.claude/settings.json`) and should not bypass that to run the probe. The GET response confirms the rules are live; the probe is belt-and-suspenders. User may run it at convenience: `git push origin main` after any local commit on `main` should be rejected with `protected branch hook declined`.

## Test Plan

Post-apply verification: `gh api /repos/tgd1975/CircuitSmith/branches/main/protection`
returns the expected JSON; a `git push origin main` from a working
directory (after a fake commit, dry-run-style) is rejected with
`protected branch hook declined`; revert the fake commit.

## Prerequisites

- **TASK-072** — the doc must land first; this task references it as
  the source of truth for the ruleset.

## Notes

HIL: Main. The agent **never** runs the `gh api -X PUT` without
explicit user approval at execution time. Per AUTONOMY.md, the agent
prepares the exact command + payload + verification step and surfaces
them in the review packet; the user reviews and runs (or directs the
agent to run with explicit per-invocation approval).

If `required_pull_request_reviews=null` is rejected by the API, the
workaround is to omit the field entirely from the PUT body — `gh api`
with the `-f` / `-F` flag form does not always allow that. The agent
may need to fall back to a JSON file (`gh api ... --input
protection.json`) instead of inline flags. Either approach is
documented at execution time.

This task closes when the as-applied configuration on the GitHub
remote matches BRANCH_PROTECTION_CONCEPT.md's ruleset table, and a
deliberate push-to-main probe is rejected.

## Closure notes

Applied via `gh api --method PUT` with a JSON body
(`/tmp/cs-protection.json`, not committed) instead of the inline
`-f` / `-F` flag form proposed in the task body — the inline form
struggles with nested-null fields (`required_pull_request_reviews=null`,
`restrictions=null`). The `--input` JSON-file path is the cleaner
mechanism; future protection edits should use the same shape:

```bash
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/tgd1975/CircuitSmith/branches/main/protection \
  --input <protection.json>
```

The as-applied response matched every field in
[`BRANCH_PROTECTION_CONCEPT.md`](../../BRANCH_PROTECTION_CONCEPT.md) —
no divergence, doc remains the source of truth. Verification GET
returned identical state.

Push-probe AC left unticked, deferred to the user. The `git push to
main` deny in [`.claude/settings.json`](../../../../.claude/settings.json)
prevents the agent from running the probe directly; doing so would
require bypassing the deny, which is the kind of remote-effect
action the HIL: Main rule exists to prevent. The GET response
already proves the rules are live server-side.
