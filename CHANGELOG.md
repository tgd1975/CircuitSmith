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
- TASK-047 closed: pytest configured (`testpaths = ["scripts/tests"]`,
  `python_files = "test_*.py"`, `addopts = "-ra"`, `strict_markers = true`).
  Pytest 9.0.2 silently drops `--strict-markers` from `addopts`, so the
  flag is set as a proper ini option. 114 tests discovered and green.
- TASK-048 closed: GitHub Actions CI workflow at
  `.github/workflows/ci.yml` — runs on `ubuntu-latest` and
  `windows-latest`, mirroring the pre-commit hook (markdownlint + pytest)
  so a `CS_COMMIT_BYPASS` cannot land broken code.
- TASK-061 closed: `ruff` adopted as the Python linter — minimal initial
  ruleset (`select = ["E4", "E7", "E9", "F"]`). Wired symmetrically into
  `pyproject.toml`, `scripts/pre-commit`, the `/commit` fixer registry
  (`*.py → ruff check --fix <files>`), and the `.claude/settings.json`
  allowlist. Baseline cleanup of `scripts/` — 10 findings fixed (4
  auto-fixed unused imports + 1 multi-import line; 6 `E741` ambiguous
  `l` in `test_housekeep.py` renamed to `ln`).
- **EPIC-007 (Project Bootstrap) closed** — all attributed tasks done.
- Pre-commit hook: exclude `.claude/security-review-latest.md` from the
  markdownlint glob. The file is gitignored runtime state written by
  the security-review hook on every merge; markdownlint-cli2 doesn't
  consult `.gitignore`, so the exclude is set explicitly.

### Planning

- EPIC-008 (Architecture Fitness Functions and Governance) scaffolded
  with the Phase 2b trigger-gate tasks (TASK-049..059) — structural
  KiCad netlist test, portability lint, schema-validation pre-commit,
  netgraph golden-hash contract, ADR seed, and the
  `check-phase2b-trigger` release gate.
- TASK-060 scaffolded — seed for autonomous-implementation mode
  (AUTONOMY.md protocol, `/epic-run` driver, branch hygiene, HIL sweep)
  to drive EPIC-007 end-to-end as the first pilot.
- TASK-060 body extended with the planned `sed/awk/head/tail` deny
  entries for `.claude/settings.json` (observed during the EPIC-007
  pilot run) and a note that the existing allowlist is non-empty
  contrary to the original description.

### Policy

- `CLAUDE.md`: forbid diagnostic suffixes (`; echo "EXIT=$?"`,
  `&& echo OK`) on Bash invocations — the permission-allowlist matcher
  checks the whole command string, so the suffix would force a prompt
  even when the primary command is allowed.
- `CLAUDE.md`: forbid end-of-turn "continue?" checkpoints. The agent
  keeps going until the requested scope is done or a real stop-line is
  hit; the user suspends via laptop lid, not via question.

### Developer experience

- VSCode workspace: subtle copper window accent for visual identification
  of CircuitSmith windows (`titleBar.activeBackground` etc. in
  `.vscode/settings.json`).

Nothing under `.claude/skills/circuit/` exists yet — see
[EPIC-001..006](docs/developers/tasks/EPICS.md), `Phase 0` (EPIC-007),
and the governance gates in [EPIC-008](docs/developers/tasks/EPICS.md).
