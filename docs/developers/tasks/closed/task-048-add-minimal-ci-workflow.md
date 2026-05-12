---
id: TASK-048
title: Add minimal GitHub Actions CI workflow
status: closed
closed: 2026-05-12
opened: 2026-05-12
effort: Small (<2h)
effort_actual: XS (<30m)
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

- [x] `.github/workflows/ci.yml` exists and is triggered by `push` and `pull_request`.
- [x] Workflow runs markdown lint with the same glob as the pre-commit hook (single source of truth for the invocation can live in a shared shell snippet or be duplicated explicitly with a comment pointing at the other).
- [x] Workflow runs `pytest` and fails the build on test failures.
- [x] CI runs on `ubuntu-latest` and `windows-latest` (per CLAUDE.md OS-context — the project is developed on both).

## Test Plan

Open a draft PR and verify both checks fail when something is wrong (introduce a markdown lint error or a failing test on a throwaway branch) and pass when the tree is clean.

## Prerequisites

- **TASK-046** — `pyproject.toml` + `requirements-dev.txt` are the install target.
- **TASK-047** — pytest needs configured discovery to run from CI's CWD.

## Notes

Branch-protection rules referencing this workflow as a required check are out of scope for this task — that's a repo-admin step the maintainer takes once the workflow is green on `main`.

### Implementation decisions (HIL: Clarification)

Three judgement calls landed without escalation, since each had a
clearly defensible default:

- **Python version**: pinned to `3.11`, the lower bound of
  `requires-python = ">=3.11"`. CI testing only the lowest supported
  version catches the most uses of newer-Python-only features; matrix
  over 3.11/3.12/3.13 was rejected for now because the project has
  no Python source yet beyond `scripts/`, so matrixing would burn
  runner time for no real coverage. Expand when a newer-Python-only
  feature lands.
- **Node version**: pinned to `20` (current LTS). The pre-commit hook
  does not pin a version, but it expects `markdownlint-cli2` on
  PATH; 20 is the lowest LTS that satisfies markdownlint-cli2's
  engines field, and the same channel the user runs locally via nvm.
- **Markdownlint single source of truth**: deliberately *duplicated*
  rather than factored into a shared shell snippet. The invocation
  is one line; introducing a shell snippet shared between
  `scripts/pre-commit` and `.github/workflows/ci.yml` would add
  indirection for negative net value at this size. The duplication
  is marked with a "Mirror of scripts/pre-commit" comment in the
  workflow so future readers see the link.

The Test Plan step (open a draft PR, introduce a failure, confirm
red→green) requires `git push` and so is deferred to the user — out
of scope for an autonomous run per the project's no-push-without-
approval rule.
