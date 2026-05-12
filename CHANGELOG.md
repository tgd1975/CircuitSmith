# Changelog

All notable changes to CircuitSmith are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) at
a relaxed cadence — bullet lists per release, no per-PR enumeration. The
project version follows [Semantic Versioning](https://semver.org/) once the
first tag is cut; until then the `[Unreleased]` section is the only entry.

## [Unreleased]

### Bootstrap

- Repository initialised from the IDEA-027 dossier in
  [AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal).
- Task system installed (45 → 49 open tasks across 7 epics).
- Pre-commit hook + `/commit` wrapper for atomicity and message-policy
  enforcement.
- Security-review git hooks (`pre-merge-commit`, `post-merge`, `pre-rebase`)
  ported from AwesomeStudioPedal; install via `bash scripts/install_git_hooks.sh`.

### Tooling

- TASK-046 closed: `pyproject.toml` (`requires-python = ">=3.11"`) and
  `requirements-dev.txt` landed — first Phase 0 prerequisite for EPIC-001
  cleared.

### Planning

- EPIC-008 (Architecture Fitness Functions and Governance) scaffolded
  with the Phase 2b trigger-gate tasks (TASK-049..059) — structural
  KiCad netlist test, portability lint, schema-validation pre-commit,
  netgraph golden-hash contract, ADR seed, and the
  `check-phase2b-trigger` release gate.
- TASK-060 scaffolded — seed for autonomous-implementation mode
  (AUTONOMY.md protocol, `/epic-run` driver, branch hygiene, HIL sweep)
  to drive EPIC-007 end-to-end as the first pilot.

Nothing under `.claude/skills/circuit/` exists yet — see
[EPIC-001..006](docs/developers/tasks/EPICS.md), `Phase 0` (EPIC-007),
and the governance gates in [EPIC-008](docs/developers/tasks/EPICS.md).
