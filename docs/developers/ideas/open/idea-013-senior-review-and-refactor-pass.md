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

## Decisions

- **Reviewer model — single agent.** One pass, not a pair. Collapsing the
  architect-hat and senior-dev-hat into one reviewer keeps the operation
  simple; if signal is thin, a second pass can run later. `/ultrareview`
  ([research preview, Claude Code v2.1.86+](https://docs.claude.com/en/docs/claude-code))
  is the natural escalation if/when available locally — its "fleet of reviewer
  agents in a remote sandbox" is the pair-review at scale.
- **Reference standard — PEP-8.** Anchor against PEP-8 as the baseline; the
  Python ecosystem defaults (ruff, black) already enforce it. Project-specific
  deviations get documented in the code-owner reminders rather than spawning
  an internal style guide.
- **Coverage instrumentation — prerequisite TASK.** Wire `coverage.py` into
  CI before the review starts so the test-coverage axis is quantitative, not
  hand-wavy. Scaffolded when this idea is promoted to an epic.
- **Output format — punch list.** Markdown punch list under
  `docs/developers/reviews/`, one file per module, indexed by `OVERVIEW.md`.
  Per-finding severity (good / improve / bad) drives whether it becomes a
  TASK.

## Implementation plan

This idea promotes to an epic. The epic spans five phases: prerequisites,
reviewer setup, per-module review, synthesis, and triage into a refactor
epic. Each phase produces concrete artefacts (TASK files,
`REVIEW-NNN-<scope>.md` files, the spawned refactor epic, code-owner
reminder updates).

### Phase 0 — prerequisites

Before the review starts, three things must be true. If any prerequisite
slips, the review pass slips with it — do not start.

1. **Coverage instrumented in CI** (decided above). Spawn one TASK that
   wires `coverage.py` + a CI step emitting per-module line coverage. The
   numbers feed the *test coverage + documentation* axis.
2. **[TASK-041](task-041-run-five-acceptance-tests.md) closed.** The five
   acceptance tests must have run and any fallout absorbed; reviewing a
   surface that has not proven its own acceptance criteria wastes the
   reviewer's effort.
3. **[EPIC-013](epic-013-post-epic-006-doc-audit.md) closed (the doc-audit
   epic, unrelated to *this* IDEA-013).** Its tasks own the docs slice of
   every module. Running the senior review while the doc audit is still
   rewriting docs lands the docs axis on a moving target. Alternative: carve
   the docs axis out of the review and defer to the doc-audit output for it
   — but that's a decision to record when this idea promotes.

### Phase 1 — reviewer setup

A single fresh-context agent (no prior session memory of how this codebase
was built), loaded with a written reviewer brief at
`docs/developers/reviews/REVIEWER-BRIEF.md` containing:

- The four axes and what each one looks for.
- The triage scheme (good / improve / bad with severity rubric).
- PEP-8 as the reference baseline; project deviations called out
  explicitly (any `ruff` / `black` config that differs from defaults).
- Pointers to the code-owner reminders
  ([`co-schema`](../../../.claude/skills/co-schema/SKILL.md),
  [`co-erc-engine`](../../../.claude/skills/co-erc-engine/SKILL.md),
  [`co-netgraph`](../../../.claude/skills/co-netgraph/SKILL.md)) — these
  encode the invariants the reviewer must check against.
- Pointer to the ADR log at [`docs/developers/adr/`](../../adr/) — the
  reviewer must surface any "should have been an ADR" decisions.
- Explicit instruction: **findings only, no fixes inside the review files**.
  Fixes get TASKs in phase 4.

The brief is written once and reused for every module pass. It's the
closest thing the project has to an internal style guide and survives the
review as a durable artefact.

### Phase 2 — per-module review pass

One pass per module from an expanded scope list (the original Scope section
omitted four real surfaces — `tests/`, the wider `.claude/skills/` set,
packaging, and `CHANGELOG.md`):

| # | Scope | Output file |
|---|-------|-------------|
| 1 | [src/circuitsmith/schema/](../../../src/circuitsmith/schema/) | REVIEW-001-schema.md |
| 2 | [src/circuitsmith/netgraph.py](../../../src/circuitsmith/netgraph.py) | REVIEW-002-netgraph.md |
| 3 | [src/circuitsmith/erc_engine.py](../../../src/circuitsmith/erc_engine.py) | REVIEW-003-erc-engine.md |
| 4 | `src/circuitsmith/renderer*.py` | REVIEW-004-renderer.md |
| 5 | [src/circuitsmith/sub_blocks.py](../../../src/circuitsmith/sub_blocks.py) | REVIEW-005-sub-blocks.md |
| 6 | [src/circuitsmith/profiles/](../../../src/circuitsmith/profiles/) | REVIEW-006-profiles.md |
| 7 | [src/circuitsmith/cli.py](../../../src/circuitsmith/cli.py) + [.claude/skills/circuit/](../../../.claude/skills/circuit/) | REVIEW-007-cli-and-skill.md |
| 8 | [tests/](../../../tests/) — review quality of the suite, not just coverage | REVIEW-008-tests.md |
| 9 | [scripts/](../../../scripts/) — task-system installation + project-local tooling | REVIEW-009-scripts.md |
| 10 | [.claude/skills/](../../../.claude/skills/) (co-\*, ts-\*, commit, release, housekeep, epic-run, …) | REVIEW-010-skills.md |
| 11 | [pyproject.toml](../../../pyproject.toml) + packaging metadata | REVIEW-011-packaging.md |
| 12 | [CHANGELOG.md](../../../CHANGELOG.md) — adherence to [feedback-changelog-concise](../../../CLAUDE.md) | REVIEW-012-changelog.md |

Each REVIEW file follows a fixed structure:

```markdown
---
review_id: REVIEW-NNN
scope: <module path or glob>
reviewer: <agent identity / model>
date: YYYY-MM-DD
---

## Good
- finding (file:line) — one-line description

## Improve
- finding (file:line) — one-line description, why it's a smell

## Bad
- finding (file:line) — one-line description, why it blocks future work
```

Findings are line-cited (`netgraph.py:142` style). Severity within Improve /
Bad is implicit in the section heading; no numeric scoring.

### Phase 3 — synthesis + OVERVIEW

After all 12 module passes complete:

1. Write `docs/developers/reviews/OVERVIEW.md` — a one-table index, row per
   module, columns = good count / improve count / bad count, link to the
   file.
2. Run a synthesis pass that looks for **cross-cutting findings** no single
   module review surfaces (e.g. "three modules all reach into config the
   same wrong way," "every renderer test mocks the schema validator").
   These land in `OVERVIEW.md` under a separate "Cross-cutting findings"
   section.

### Phase 4 — triage into a refactor epic

For each finding:

- **Good** — one paragraph into the relevant code-owner reminder. Modules
  that don't have a `co-*` skill yet (renderer, profiles, sub_blocks)
  spawn one as part of the triage. The reminder grows; the REVIEW file is
  preserved unchanged.
- **Improve** — captured in `docs/developers/reviews/IMPROVE-BACKLOG.md`
  (one bullet per finding, with REVIEW-NNN reference). **Hard cap:** only
  the top-15 (by reviewer-rated impact) get pulled forward into TASKs in
  the refactor epic. The rest stay in `IMPROVE-BACKLOG.md` as record,
  never converted to work items. This is the explicit mitigation against
  improve-backlog ossification.
- **Bad** — spawns one TASK in a new refactor epic
  (`EPIC-NNN-post-014-review-cleanup`). Every Bad becomes a release-blocker
  for the next feature epic, per the "land the refactor epic before the
  next feature epic" commitment.

### Phase 5 — closure

This idea archives when:

- All 12 REVIEW files exist.
- `OVERVIEW.md` and `IMPROVE-BACKLOG.md` exist.
- The refactor epic exists with TASKs for every Bad finding (or is
  explicitly not created because zero Bads surfaced — record that verdict).
- Code-owner reminders carry the Good-pattern write-ups (existing skills
  updated; new `co-*` skills spawned for renderer / profiles / sub_blocks
  if surfaced).

The refactor epic *closing* is **not** a prerequisite for archiving this
idea — that's the refactor epic's own job.

### Expected scale

- 12 review files × 3–8 findings per file = ~40–100 findings total.
- Realistic distribution: ~30% Good, ~50% Improve, ~20% Bad.
- That projects to ~10–20 TASKs in the refactor epic. If the count blows
  past 30 Bad findings, that's a signal the four-axes rubric is being
  applied too aggressively — pause and re-calibrate before spawning the
  full task batch.

### Risks / things to watch

- **Reviewer drift across modules.** A single agent reviewing 12 modules
  in sequence may anchor to early findings and miss later ones. Mitigation:
  reset context between modules; carry only the reviewer brief, not the
  prior REVIEW files, into each next pass.
- **`/ultrareview` availability.** If `/ultrareview` becomes available on
  this Claude Code build before Phase 2 starts, switch to it — same
  review, parallelised and cheaper. The reviewer brief survives the switch
  unchanged.
- **Improve-backlog ossification.** Mitigated by the hard cap above.
- **Refactor-epic gating delays IDEA-012.** The "land refactor before next
  feature epic" rule means [IDEA-012](idea-012-revisit-original-concept-vs-0-1-0.md)
  waits behind this. Acknowledge the cost; do not soften the gate.

## Why now

EPIC-014 (circuit library + renderer v2) is in flight; once it closes the
active-device + sub-block surface stabilises. That's a natural pause point —
the codebase is large enough that a review yields real signal, but small
enough that fixes are still local. Waiting until EPIC-015+ adds more layers
makes the review more expensive and the refactor more invasive.
