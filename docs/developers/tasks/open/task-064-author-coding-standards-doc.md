---
id: TASK-064
title: Author docs/developers/CODING_STANDARDS.md (naming, formatting, comment policy, type hints)
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: developer-docs-governance
order: 3
prerequisites: [TASK-061]
---

## Description

CircuitSmith has [ruff configuration](../../../../pyproject.toml) but
no human-readable summary of the Python style the project expects.
The comment-policy guidance from [`CLAUDE.md`](../../../../CLAUDE.md)
("Default to writing no comments. Only add one when the WHY is
non-obvious") is agent-facing — a human contributor will not find it
from a fresh clone. This task transcribes the load-bearing standards
into a discoverable doc.

Model: AwesomeStudioPedal's
[`CODING_STANDARDS.md`](../../../../../AwesomeStudioPedal/docs/developers/CODING_STANDARDS.md)
(74 lines). CircuitSmith's version covers Python instead of C++ but
keeps the same shape: naming conventions, formatting, commit-message
format (one-line pointer at `COMMIT_POLICY.md` from TASK-071),
branch naming, and a comment-policy section that mirrors the CLAUDE.md
guidance for human readers.

## Acceptance Criteria

- [ ] `docs/developers/CODING_STANDARDS.md` exists and is linked from CONTRIBUTING.md and DEVELOPMENT_SETUP.md.
- [ ] Naming conventions table covers: modules, classes, functions, constants, fixture files, test files.
- [ ] Ruff is named as the authoritative formatter/linter; the doc references `pyproject.toml`'s `[tool.ruff.lint] select` for the active ruleset.
- [ ] Comment policy mirrors CLAUDE.md's "WHY not WHAT" stance, with two concrete examples (good comment vs bad comment).
- [ ] Type-hint policy is recorded: when required, when optional, when forbidden (TBD — pick a defensible default; ADR if load-bearing).
- [ ] Branch-naming and commit-subject conventions are stated with examples (deeper rationale lives in TASK-071's COMMIT_POLICY.md).

## Test Plan

No automated tests. Manual: read the doc end-to-end; verify every
named tool (ruff, markdownlint-cli2) is installed by the steps
DEVELOPMENT_SETUP.md prescribes. If a tool is named but not installed
by the setup doc, fix one or the other.

## Prerequisites

- **TASK-061** — ruff is the chosen linter/formatter; this doc points at its config.

## Notes

The CLAUDE.md `## Auto-activate tasks when work begins` rule is
agent-only and should **not** be transcribed here — it belongs to the
agent operational protocol, not the human-facing style guide. Same
for the `/commit`-only rule: humans see it via COMMIT_POLICY.md
(TASK-071), agents see it via CLAUDE.md.

Keep the doc short. The temptation with style guides is comprehensive
coverage; the failure mode is unread length. Aim for ~80 lines.
