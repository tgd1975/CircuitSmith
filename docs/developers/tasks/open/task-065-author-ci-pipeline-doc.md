---
id: TASK-065
title: Author docs/developers/CI_PIPELINE.md inventorying CI jobs and gate semantics
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: developer-docs-governance
order: 4
prerequisites: [TASK-048]
---

## Description

[`.github/workflows/ci.yml`](../../../../.github/workflows/ci.yml)
runs four steps today (markdown lint, portability lint, pytest, plus
the matrix axis Ubuntu/Windows). The senior-review pre-implementation
audit flagged that ruff is configured but not running in CI; that gap
is being closed in this epic's adjacent work, but the broader issue
is that no doc tells a contributor what CI does, what gates a merge,
or what to do when CI is red. This task fills that hole.

Model: AwesomeStudioPedal's
[`CI_PIPELINE.md`](../../../../../AwesomeStudioPedal/docs/developers/CI_PIPELINE.md)
(93 lines, covers the test workflow, the docs workflow, and the
release process). CircuitSmith's version covers the single CI
workflow today; placeholders for future workflows (release, docs,
deploy) land as the project ramps.

## Acceptance Criteria

- [ ] `docs/developers/CI_PIPELINE.md` exists and is linked from CONTRIBUTING.md.
- [ ] Each CI job is listed with: trigger, OS axis, what it does, what a red build means.
- [ ] Pre-commit hook is documented as the local mirror of the CI gates (markdown lint, portability lint, security review on pulls).
- [ ] The doc states explicitly which CI failures are advisory vs blocking (today: all jobs blocking; document the policy).
- [ ] A "red build response" section names the standard sequence: read the failing step, reproduce locally, fix, re-push — and the escalation point (when the failure is in the harness, not the code).
- [ ] Cross-references: BRANCH_PROTECTION_CONCEPT.md (TASK-072) lists the same CI contexts as required status checks.

## Test Plan

No automated tests. Verify by spot-check: every job mentioned in the
doc exists in `ci.yml` with the documented name and step list. If
they diverge, fix the doc (CI is the source of truth).

## Prerequisites

- **TASK-048** — the CI workflow itself.

## Notes

Keep the format inventory-oriented: a table of jobs is more useful
than prose paragraphs. Contributors reading this doc want to answer
"what does this red `X` symbol mean?" not "what is CI for?"
