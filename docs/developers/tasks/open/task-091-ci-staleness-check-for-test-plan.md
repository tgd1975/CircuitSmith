---
id: TASK-091
title: Add a CI staleness check that flags tests not referenced in the plan
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: test-plan-and-coverage
order: 9
prerequisites: [TASK-089, TASK-090]
---

## Description

The risk this whole epic exists to prevent is drift: a new test file
lands without a corresponding plan entry, or a plan entry references
a test that has been deleted. The matrix (TASK-089) makes drift
visible; this task makes it *unmissable* by failing CI when it
happens.

Implementation shape (mirrors TASK-029 — the existing erc-report
staleness check):

- New script `scripts/check_test_plan_staleness.py`.
- Walks `tests/` (and any on-device test directories) to enumerate
  test files.
- Walks `docs/developers/testing/*.md` to enumerate referenced test
  files (parse the matrix and the per-subsystem chapter bodies).
- Failure modes:
  - **Test file with no plan reference** → exit non-zero with the
    file path and a one-line "add an entry to the matrix and the
    relevant chapter" hint.
  - **Plan reference to a non-existent test file** → exit non-zero
    with the broken reference and the chapter/line it appears on.
- Wired into the same CI job that runs the erc-report staleness
  check (likely `.github/workflows/ci.yml` — check existing layout).

Local-dev integration:

- Add `Bash(python scripts/check_test_plan_staleness.py:*)` to
  `.claude/settings.json` allow list (per the "Allow new scripts
  proactively" memory).
- The script must run cleanly from the project root and produce
  exit 0 on the current state of the repo when the plan is complete.

The script is **not** wired into the pre-commit hook — the budget
there is "well under a second per file" (per
`docs/developers/COMMIT_POLICY.md`), and walking every test file is
too slow. CI-only is correct.

## Acceptance Criteria

- [ ] `scripts/check_test_plan_staleness.py` exists, is executable,
      and exits 0 on the current repo state.
- [ ] The script flags both missing-from-plan and dangling-reference
      failures with actionable error messages.
- [ ] CI runs the check on every PR (same job or sibling of the
      erc-report staleness check).
- [ ] `.claude/settings.json` includes the new `Bash(python ...)`
      allow rule.
- [ ] `scripts/README.md` updated to list the new script and what it
      does.

## Test Plan

**Host tests** — script is a small CLI, should have a tests/ entry:

- `tests/test_check_test_plan_staleness.py`:
  - Construct a temp tree with three test files and a plan that
    references two of them. Confirm the script exits non-zero with
    the missing file's name in stderr.
  - Construct a temp tree with two test files and a plan that
    references three (one phantom). Confirm the script exits
    non-zero with the phantom reference in stderr.
  - Construct a temp tree where plan and tests match exactly.
    Confirm exit 0.

Manual verification:

1. Run the script against the current repo state: `exit 0` expected
   (after TASK-089 / TASK-090 closes).
2. Introduce a throwaway `tests/test_drift_probe.py` without
   updating the plan; confirm the script and CI flag it.
3. Remove the probe.

## Prerequisites

- **TASK-089** — the matrix must exist for the script to parse.
- **TASK-090** — outstanding gaps must be resolved (filed or
  annotated) before the check runs clean.

## Documentation

- `scripts/README.md` — add the new script row.
- `docs/developers/testing/README.md` — add a short "CI guard"
  paragraph at the bottom of the matrix pointing at the staleness
  check.
- `docs/developers/CI_PIPELINE.md` — add the new gate to the
  required-checks inventory.

## Notes

- Parsing the matrix is the fragile bit. Two options: regex-extract
  the test-file paths from the markdown table, or require every test
  file reference to be inside a fenced ` ```pytest ` block (so a
  proper parser can pick them out unambiguously). Pick fenced blocks
  — regex over markdown tables is a maintenance burden.
- Coordinate with EPIC-012's CI regression diff (TASK-101) — both
  land new CI gates; make sure they share the same job-naming
  convention so the contributor-facing CI dashboard stays tidy.
