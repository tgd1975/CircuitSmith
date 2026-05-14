---
id: IDEA-013
title: Senior-developer + senior-architect review pass and refactor
description: Commission a senior-dev / senior-architect review of everything shipped so far — score correctness, readability, maintainability, test coverage, and docs; produce a prioritised good / improve / bad punch list driving a refactor epic.
category: 🛠️ tooling
---

CircuitSmith has accumulated a meaningful surface area across EPIC-001..014:
schema, netgraph, ERC engine, renderer, sub-block flattener, component-profile
library, CLI, skill, tutorial, and the task-system installation. None of it has
had a deliberate top-down review by someone wearing a senior-engineer or
senior-architect hat — the work was driven task-by-task with local correctness
as the bar.

This idea proposes a dedicated review pass, conducted as if by a senior
developer + senior architect pair, evaluating every implemented module against
four axes:

- **Correctness** — does the code do what the spec / ADRs / tests say, and are
  the invariants the modules claim actually enforced? Cross-check against the
  code-owner reminders ([`co-schema`](../../../.claude/skills/co-schema/SKILL.md),
  [`co-erc-engine`](../../../.claude/skills/co-erc-engine/SKILL.md),
  [`co-netgraph`](../../../.claude/skills/co-netgraph/SKILL.md)) and the ADR
  log.
- **Readability** — is the code legible to a newcomer? Naming, function size,
  module boundaries, comment quality, dead code, premature abstraction.
- **Maintainability** — coupling, layering, extension points, test seams,
  error-path discipline, deprecation handling.
- **Test coverage + documentation** — does every module have tests that
  exercise its real failure modes (not just the golden path)? Is the public
  surface documented at a level a contributor can pick up cold?

Output is a triaged punch list per module:

- **Good** — keep as-is; document the pattern so future work mirrors it.
- **Improve** — known smell, worth a follow-up task, not a blocker.
- **Bad** — must-fix before further feature work; spawns a TASK or short epic.

## Scope (modules in front of the reviewer)

- `src/circuitsmith/schema/` — JSON schema + validator
- `src/circuitsmith/netgraph.py` — net resolution + topology
- `src/circuitsmith/erc_engine.py` — rule catalog + execution
- `src/circuitsmith/renderer*.py` — SVG renderer + multi-page support
- `src/circuitsmith/sub_blocks.py` — sub-block flattener (TASK-116..118)
- `src/circuitsmith/profiles/` — component-profile library (LED, BJT, 555,
  op-amp, generic IC kernel)
- `src/circuitsmith/cli.py` + `.claude/skills/circuit/` — user-facing entry
  points
- `scripts/` — task-system installation + project-local tooling
- `docs/developers/` — ADRs, task-system docs, tutorial, README

## Open questions

- **Single agent or pair?** The "senior dev" and "senior architect" hats look
  at different things; a single reviewer may collapse the two perspectives.
  Likely answer: two passes (or two agents in parallel) with a synthesis step.
- **Reference standard for "good"?** Do we anchor against a published style
  guide (PEP-8, Google Python Style), an internal one (none yet), or just
  apply professional judgement? An ADR may need to settle this before the
  review starts.
- **Coverage instrumentation?** Currently no `coverage.py` runs in CI — the
  test-coverage axis is qualitative unless we wire that up first. Possibly a
  prerequisite TASK.
- **Output format?** A markdown punch list under `docs/developers/reviews/`,
  one file per module, indexed by an `OVERVIEW.md`. Per-finding severity
  (good / improve / bad) drives whether it becomes a TASK.

## Rough approach

1. Stand up a prerequisite — coverage instrumentation if we want it
   quantitative; otherwise skip.
2. Run the review in two passes: architect-hat (boundaries, layering,
   extension model, ADR coherence) and senior-dev-hat (line-level
   correctness, readability, idiom, test quality).
3. Synthesise a `docs/developers/reviews/REVIEW-001-<scope>.md` per module
   with the good / improve / bad triage.
4. Convert every **bad** finding into a TASK in a new refactor epic
   (`EPIC-NNN-post-014-review-cleanup` or similar). **Improve** findings
   become low-priority backlog tasks. **Good** patterns get a one-paragraph
   write-up in the relevant code-owner reminder so future edits preserve
   them.
5. Land the refactor epic before the next feature epic — the point of the
   review is to clear technical debt while the surface is still small enough
   to fix cheaply.

## Why now

EPIC-014 (circuit library + renderer v2) is in flight; once it closes the
active-device + sub-block surface stabilises. That's a natural pause point —
the codebase is large enough that a review yields real signal, but small
enough that fixes are still local. Waiting until EPIC-015+ adds more layers
makes the review more expensive and the refactor more invasive.
