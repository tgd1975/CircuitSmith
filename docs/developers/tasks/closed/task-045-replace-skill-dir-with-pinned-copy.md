---
id: TASK-045
title: Replace skill dir with pinned copy; update doc links; write RELEASING.md and README
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: XS (<30m)
complexity: Medium
human-in-loop: Main
epic: circuit-skill-packaging
order: 7
prerequisites: [TASK-044]
---

## Closure note (2026-05-13)

Retired under [ADR-0012](../../adr/0012-library-as-installable-package.md).
Pinned folder copies of `.claude/skills/circuit/` are obsolete: the
skill folder stays in this repo as the canonical location, and the
library ships as the `circuitsmith` PyPI package. There is no
external pinned copy to replace.

`RELEASING.md` survives the rewrite — it migrates to the **CircuitSmith
repo root** (not a standalone repo) as part of TASK-080
(`publish-circuitsmith-to-pypi`), documenting the PyPI release flow
rather than the folder-copy procedure described below.

Superseded by **TASK-080** (`publish-circuitsmith-to-pypi`). See
[EPIC-006](epic-006-circuit-skill-packaging.md) § "Retired tasks"
and [`idea-002`](../../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md)
for the full reckoning.

The acceptance criteria below are preserved as historical record; do
not act on them.

## Autonomy

`Main` kept per TASK-060 sweep. Replaces the in-repo skill with a
pinned copy from the standalone repo — touches the dependency-pin
policy and changes the project's relationship with the published
skill. User reviews the swap before commit.

## Description

Close out EPIC-006 with the four standalone-extraction tail items:

1. **Replace** `.claude/skills/circuit/` in this project with a pinned
   directory copy of the standalone repo at `v0.1.0`. (Submodule only
   if the standalone repo will ship on an independent release cadence
   — default is pinned copy per the Phase 7 decision rule.)
2. **Update** `docs/builders/` cross-references and the MkDocs nav
   (IDEA-022, if landed) to point at the standalone repo's docs
   (GitHub raw or published Pages site).
3. **Write `RELEASING.md`** in the standalone repo documenting the
   tag-and-release process: when to cut a release, how to tag, how to
   update consumers.
4. **Finalise `README.md`** in the standalone repo for the GitHub
   landing-page context: install, quick-start, link to docs/index.md,
   contribution guidelines.

## Acceptance Criteria

- [ ] `.claude/skills/circuit/` in this project is the pinned copy at `v0.1.0` (verified by file diff).
- [ ] All `docs/builders/` cross-references resolve to the standalone repo's docs.
- [ ] `RELEASING.md` is committed to the standalone repo with at least: tag-naming convention, release-note template, downstream-consumer update procedure.
- [ ] `README.md` is committed to the standalone repo with install, quick-start, and contribution sections.

## Test Plan

Manual verification: clone the standalone repo fresh into a sibling directory, follow `README.md` install instructions, render the demo circuit — must work with no project-specific knowledge.

## Prerequisites

- **TASK-044** — standalone repo with full history is the pinned target.

## Notes

This closes out EPIC-006 and IDEA-001 as a whole. (IDEA-001 was
already archived on 2026-05-12 on conversion to EPIC-001..006 — no
further `/ts-idea-archive` step needed here.)

## Predecessor source

[IDEA-022 (MkDocs site)](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-022-mkdocs-documentation-site.md)
is an AwesomeStudioPedal idea — its landing status is tracked there.
`docs/builders/` cross-references in this task target the consumer project's
build guide tree (originally
[AwesomeStudioPedal's](https://github.com/tgd1975/AwesomeStudioPedal/tree/main/docs/builders)).
