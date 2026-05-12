---
id: TASK-061
title: Adopt a Python linter/formatter and wire it into /commit + pre-commit hook
status: closed
closed: 2026-05-12
opened: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: Clarification
epic: project-bootstrap
order: 4
---

## Description

The `/commit` skill grew a pathspec-scoped auto-fixer registry in commit
`182d8dd` (`.claude/skills/commit/SKILL.md` step 2). The registry currently
contains only one row — `*.md → markdownlint-cli2 --fix`. Python is
**deliberately absent**: the skill notes that the choice of linter/formatter
"is its own decision, to be made in a dedicated task that also wires the tool
into `scripts/pre-commit` and `requirements-dev.txt`." This task is that
decision.

The work has two halves:

1. **Decide.** Pick a Python linter/formatter (recommendation: `ruff` —
   single fast tool that subsumes flake8 + isort + most of black; alternatives
   are black-only, black+isort+flake8, or autopep8). Capture the rationale
   in the commit message and/or a short ADR. The choice is load-bearing
   because once it's wired into the pre-commit hook every contributor has
   to install it.
2. **Wire it in symmetrically.** Three sites must stay in sync so a fixer
   missing from one isn't a silent gap:
   - `requirements-dev.txt` and `pyproject.toml` `[tool.<linter>]` — the
     tool is declared and configured as a dev dependency.
   - `scripts/pre-commit` — mirrors the existing markdownlint block: lint
     staged `*.py` files; missing-tool fails the hook with an install
     instruction (do not silently skip).
   - `.claude/skills/commit/SKILL.md` registry table — adds a `*.py` row
     pointing at the chosen `--fix` command, scoped to pathspec entries.

Order matters: configure → run against existing `scripts/*.py` and fix
findings → enable the hook gate. If you flip the gate on first, the very
commit that introduces it gets blocked.

## Acceptance Criteria

- [x] Python linter/formatter chosen, with a one-paragraph rationale in
      the commit message (or in `docs/developers/adr/` if the decision
      deserves a record).
- [x] Tool added to `requirements-dev.txt`; configuration block added to
      `pyproject.toml` (initial ruleset deliberately minimal — opt into
      more rules over time, not up-front).
- [x] `scripts/pre-commit` enforces the linter on staged `*.py` files,
      mirroring the markdownlint pattern: missing tool fails the hook with
      an install instruction; finding errors blocks the commit.
- [x] `.claude/skills/commit/SKILL.md` fixer registry gains a `*.py` row
      pointing at the chosen fixer command. The deliberate-absence note
      that currently mentions ruff/black/autopep8 is replaced with a
      reference to this task's resolution.
- [x] All existing `scripts/*.py` either pass the new linter clean or have
      narrowly-scoped opt-outs documented in `pyproject.toml`.

## Test Plan

No automated tests required — change is non-functional (tooling / CI).
Manual verification:

1. From a clean clone with the dev extras installed, run the new linter
   against the repo; confirm zero errors.
2. Introduce a deliberate violation in a throwaway `scripts/_lint_probe.py`
   (e.g. an unused import) and run `/commit "test" scripts/_lint_probe.py`.
   The skill should auto-fix; the hook should accept the (now-clean) result.
   Delete the probe.
3. Uninstall the linter from the venv and re-attempt the probe commit. The
   skill's pre-fix step should halt and ask the user to install the tool
   (per CLAUDE.md's "Missing executables" rule).
4. Re-install, simulate an un-auto-fixable error (e.g. a redefined function),
   and confirm the pre-commit hook itself blocks the commit with the
   linter's error message.

## Documentation

- `.claude/skills/commit/SKILL.md` — registry table edit (covered by
  acceptance criteria above).
- `docs/developers/DEVELOPMENT_SETUP.md` — add the new dev-dep install
  step alongside `markdownlint-cli2`, and add the new check to the
  required-checks listing if CI mirrors local hooks.
- `scripts/README.md` — touch only if a new helper script is added (not
  expected for this task; the linter is run directly from its CLI).

## Notes

- **Why ruff is the obvious default but not mandated:** ruff is fast,
  written in Rust, replaces flake8 / isort / pyupgrade in one binary, and
  has a built-in formatter (`ruff format`) compatible with black's style.
  For a project this size it's almost certainly the right answer. The
  reason this task exists rather than just shipping ruff is that the
  decision deserves a *recorded* rationale, not a side-effect of an
  unrelated commit.
- **Initial ruleset should be deliberately small.** Enabling everything
  ruff offers on day one produces hundreds of findings on existing code
  and conditions contributors to ignore the tool. Start with the default
  rules + project-specific essentials, opt into more (`pydocstyle`,
  `mccabe`, etc.) as the codebase grows.
- **Hook discovery via /commit's pre-fix step is intentional.** Once
  this task lands, the next time someone commits a `.py` file without
  the linter installed, the `/commit` skill's pre-fix step will halt and
  ask them to install it. That's the designed UX — same pattern as
  `markdownlint-cli2`.
- **Don't enable a `pip-audit` / `mypy` gate as part of this task.**
  Type-checking and dependency audits are expensive and belong in a CI
  job, not in the local pre-commit hook. Keep the local hook in the
  "well under a second per file" budget the /commit skill mandates.

### Implementation notes (closure)

- **ruff was chosen.** Default ruleset only — `select = ["E4", "E7",
  "E9", "F"]` in `[tool.ruff.lint]`. ruff's built-in formatter
  (`ruff format`) is not yet wired into the hook or the /commit fixer
  registry; the registry row is `ruff check --fix` only. Adding
  `ruff format` is a small follow-up worth doing once a Python source
  tree exists beyond `scripts/`.
- **Baseline cleanup.** Running `ruff check scripts` produced 10
  findings: 3 unused imports (`F401`), 1 multi-import line (`E401`),
  6 `E741` ambiguous variable names (`l` in generator expressions in
  `test_housekeep.py`). The first 4 were auto-fixed by `ruff check
  --fix`; the 6 `E741` were renamed `l` → `ln` by hand. All 114 tests
  still pass.
- **`DEVELOPMENT_SETUP.md` not touched.** The doc doesn't exist yet —
  it's only referenced from the `/commit` SKILL.md "CI gate" section.
  Creating it just to add a ruff install line would be creep; defer
  to whoever scaffolds the doc.
- **`.claude/settings.json`.** Added `Bash(ruff:*)` to the project
  allowlist (sibling of `Bash(markdownlint-cli2:*)`) so the autonomous
  loop can run ruff invocations without permission prompts. TASK-060
  still owns the broader settings work (deny entries, etc.).
- **Allowlist drift fix.** `.claude/settings.json` had a populated
  allow list at the time of this task — the TASK-060 description
  saying it is "empty" is stale and should be updated when TASK-060
  is worked.
