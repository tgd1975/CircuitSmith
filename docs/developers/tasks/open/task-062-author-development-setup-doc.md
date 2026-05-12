---
id: TASK-062
title: Author docs/developers/DEVELOPMENT_SETUP.md as the canonical first-time-setup entry point
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: developer-docs-governance
order: 1
prerequisites: [TASK-046, TASK-047, TASK-048, TASK-061]
---

## Description

CircuitSmith's first-time setup today is spread across
[`README.md`](../../../../README.md) (concept overview),
[`CONTRIBUTING.md`](../../../../CONTRIBUTING.md) (four-step quickstart),
and [`.envrc.example`](../../../../.envrc.example) (env vars). A new
contributor has to stitch three sources together to know what binaries
they need, in what order, and how to verify the install. Consolidate
into one canonical doc.

Model: AwesomeStudioPedal's
[`DEVELOPMENT_SETUP.md`](../../../../../AwesomeStudioPedal/docs/developers/DEVELOPMENT_SETUP.md)
(553 lines, heavy on dev-container and hardware-USB content most of
which does not apply here). CircuitSmith's version should be ~150
lines covering: required tools, Ubuntu vs Windows 11 platform notes
(per [`CLAUDE.md`](../../../../CLAUDE.md) `## OS context`), step-by-step
install, smoke-test, and a "common setup problems" appendix.

## Acceptance Criteria

- [ ] `docs/developers/DEVELOPMENT_SETUP.md` exists and is reachable from `CONTRIBUTING.md` as the canonical setup pointer.
- [ ] Tool prerequisites section names every binary the dev needs: Python 3.11+, node 20+, npm, `markdownlint-cli2`, git, and (optional) direnv.
- [ ] Setup procedure is reproducible on both Ubuntu and Windows 11 — explicit per-OS commands where they diverge (shell syntax, `pip` vs `py -m pip`, etc.).
- [ ] CONTRIBUTING.md keeps its PR-workflow content but redirects "first-time setup" to this doc rather than duplicating it.
- [ ] A "common setup problems" appendix covers at minimum: missing markdownlint-cli2, wrong Python version, git hooks not installed, missing `$CS_*` env vars.
- [ ] Doc closes with a smoke-test sequence (clone → install → `pytest` green) that a contributor can copy-paste.

## Test Plan

No automated tests. Manual: from a clean directory on each of Ubuntu
and Windows 11, follow the doc verbatim and reach first green
`pytest`. Note any step that required tribal knowledge the doc did not
provide; fix until reproducible.

## Prerequisites

- **TASK-046** — `pyproject.toml` and `requirements-dev.txt` are the deps the doc points at.
- **TASK-047** — pytest config is the smoke-test target.
- **TASK-048** — CI workflow exists, so the doc can cross-reference the same setup gate.
- **TASK-061** — `ruff` is part of the dev-tooling chain the doc lists.

## Notes

Reference the
[`scripts/install_git_hooks.sh`](../../../../scripts/install_git_hooks.sh)
step explicitly — pre-commit hook installation is the most-skipped
step in new-contributor setup. The doc should call it out before the
Python install, not after.
