---
id: TASK-074
title: Extend security-review hook to detect personal-contact-info leaks
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: Clarification
epic: architecture-fitness-functions
order: 8
---

## Description

CircuitSmith's policy is that no committed file should contain the
maintainer's personal contact details (email address, phone number,
real name beyond the GitHub handle `tgd1975`). The
[`feedback-no-personal-contact-in-docs.md`](https://example.invalid)
memory rule captures this on the agent side, but a memory rule alone
does not protect against:

- A future contributor who has not read the memory.
- The agent forgetting and re-introducing the pattern.
- An incoming pull/merge/rebase that adds the leak from elsewhere.

The security-review hooks already installed by
[`scripts/install_git_hooks.sh`](../../../../scripts/install_git_hooks.sh)
(`pre-merge-commit`, `post-merge`, `pre-rebase`) are the right
extension point: they already scan incoming diffs and write reports
to `.claude/security-review-latest.md`. Add personal-data patterns
to the detection set.

Surfaced from the user override at
[TASK-067](../closed/task-067-author-code-of-conduct.md): "maybe add
a skill or something — I don't want my contact details anywhere in
the documents."

## Acceptance Criteria

- [ ] The security-review hook detects email-address-shaped strings
      matching the maintainer's known address (initially
      `t.deutsch.75@gmail.com`; the pattern list lives in a config
      file, not hard-coded in the hook).
- [ ] Phone-number-shaped strings are also detected (E.164 form, plus
      common local-format variants).
- [ ] Detection is scoped to text-bearing files (`.md`, `.toml`,
      `.yml`, `.json`, `.py`, `.sh`); binaries are skipped.
- [ ] An allowlist mechanism exists so that legitimate mentions
      (e.g. CHANGELOG entries quoting a removal commit, or a
      `.envrc.example` placeholder) can be exempted by exact match.
- [ ] A match emits a hook-blocking error (not just a warning) with
      the offending file:line and a one-liner explaining the policy.
- [ ] `scripts/tests/test_security_review_personal_data.py` covers:
      a clean diff passes, a diff adding the email fails, an
      allowlisted file with the email passes.

## Test Plan

1. Add `tests/test_security_review_personal_data.py` per the AC.
2. Run the hook against a synthetic diff that contains the email →
   expect failure.
3. Run against a diff that contains an allowlisted mention → expect
   pass.
4. Run against the current `main` HEAD → expect pass (no leaks).

## Prerequisites

None — the security-review hook already exists.

## Notes

- **Pattern source.** Keep the pattern list in
  `scripts/git-hooks/personal_data_patterns.yml` so a future
  contributor can extend it without editing the hook script. The
  initial entry is the maintainer's email; later entries may include
  phone numbers, the real name if/when committed by mistake, etc.
- **Allowlist mechanism.** Match by `file:line-prefix` so trivial
  edits don't unlist. Allowlist entries live alongside the patterns
  file. Document the format in the hook docstring; reference it from
  [`SECURITY_REVIEW.md`](../../SECURITY_REVIEW.md) (when
  [TASK-070](../open/task-070-author-security-review-doc.md) lands).
- **HIL `Clarification`.** The maintainer should confirm the initial
  pattern list before this lands — adding the wrong pattern blocks
  legitimate commits.

## Sizing rationale

Small because the existing security-review hook already has the
infrastructure for file-scoped scans; this task adds one pattern
matcher and a config file, plus tests.
