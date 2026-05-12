---
id: TASK-048
title: Add minimal GitHub Actions CI workflow
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Medium
human-in-loop: Clarification
epic: project-bootstrap
order: 3
prerequisites: [TASK-046, TASK-047]
---

## Description

Add `.github/workflows/ci.yml` running on every push and PR. The
workflow does the same checks the local pre-commit hook does, plus the
test suite — so a contributor who bypasses the hook with
`CS_COMMIT_BYPASS` still cannot land broken code.

Steps in the workflow:

1. Checkout
2. Set up Python (version from `pyproject.toml` `requires-python`)
3. Install: `pip install -e . -r requirements-dev.txt`
4. Install `markdownlint-cli2` via `npm install -g`
5. Run `markdownlint-cli2 "**/*.md" "#node_modules"` — matches the pre-commit invocation
6. Run `pytest` — exit code is the gate

ERC/SVG-staleness gates are deliberately **not** in scope here — they
land in EPIC-002 (TASK-015 cutover) and EPIC-003 (TASK-029) alongside
the renderer and ERC engine that produce the artifacts.

## Acceptance Criteria

- [ ] `.github/workflows/ci.yml` exists and is triggered by `push` and `pull_request`.
- [ ] Workflow runs markdown lint with the same glob as the pre-commit hook (single source of truth for the invocation can live in a shared shell snippet or be duplicated explicitly with a comment pointing at the other).
- [ ] Workflow runs `pytest` and fails the build on test failures.
- [ ] CI runs on `ubuntu-latest` and `windows-latest` (per CLAUDE.md OS-context — the project is developed on both).

## Test Plan

Open a draft PR and verify both checks fail when something is wrong (introduce a markdown lint error or a failing test on a throwaway branch) and pass when the tree is clean.

## Prerequisites

- **TASK-046** — `pyproject.toml` + `requirements-dev.txt` are the install target.
- **TASK-047** — pytest needs configured discovery to run from CI's CWD.

## Notes

Branch-protection rules referencing this workflow as a required check are out of scope for this task — that's a repo-admin step the maintainer takes once the workflow is green on `main`.
