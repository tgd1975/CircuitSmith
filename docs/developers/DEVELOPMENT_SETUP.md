# Development Setup

The canonical first-time-setup walk-through for CircuitSmith. Follow
top-to-bottom from a clean machine and you reach a green `pytest` run
without coming back with questions.

CircuitSmith is developed on both **Ubuntu** and **Windows 11**. Where
the two diverge, this doc spells out both invocations — pick the one
matching your shell.

## Tool prerequisites

| Tool | Version | Required? | Notes |
|---|---|---|---|
| Git | ≥ 2.35 | Yes | Any modern git works; older versions miss `git rev-parse --show-toplevel` quirks the hooks rely on. |
| Python | ≥ 3.11 | Yes | 3.11, 3.12, and 3.13 are all CI-tested. |
| Node.js | ≥ 20 | Yes | Solely to install `markdownlint-cli2`. |
| npm | bundled with Node | Yes | Used to install `markdownlint-cli2` globally. |
| `markdownlint-cli2` | latest | Yes | The pre-commit hook fails hard if this binary is missing. |
| `direnv` | ≥ 2.32 | Optional | Auto-loads the per-developer env vars in `.envrc`. |

Set up these binaries first; everything below assumes they are on
`PATH`.

## Step 1 — Clone the repo

```bash
git clone https://github.com/tgd1975/CircuitSmith.git
cd CircuitSmith
```

## Step 2 — Install the git hooks

**Run this before your first commit, not after.** Skipping this step
is the most common new-contributor failure: the pre-commit hook is
not just a linter, it also enforces the
[commit-policy provenance token](../../CLAUDE.md#commits-go-through-commit--always)
that `/commit` writes. Raw `git commit` is rejected.

**Ubuntu / WSL / Git Bash:**

```bash
bash scripts/install_git_hooks.sh
```

**Windows 11 (PowerShell):**

```powershell
bash scripts/install_git_hooks.sh
```

The script is bash-only by design; on Windows run it from Git Bash or
WSL. It installs:

- `pre-commit` — markdown lint + commit-policy enforcement wrapper.
- `pre-merge-commit`, `post-merge`, `pre-rebase` — security-review hooks
  that scan incoming changes from pulls/merges/rebases. Reports land at
  `.claude/security-review-latest.md`.

Re-run is idempotent. Existing hooks are backed up to
`.git/hooks/<name>.backup.<timestamp>`.

## Step 3 — Install `markdownlint-cli2`

```bash
npm install -g markdownlint-cli2
```

This is the binary the pre-commit hook calls. Without it, every commit
fails with `markdownlint-cli2: command not found`.

## Step 4 — Install the Python dev tooling

CircuitSmith is a `pip install -e .` project with a `[dev]` extra.
Activate a virtualenv first (any flavour — `venv`, `conda`, `pyenv`),
then:

**Ubuntu:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

**Windows 11 (PowerShell):**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements-dev.txt
```

That installs CircuitSmith in editable mode with the `[dev]` extra:
[`pytest`](https://docs.pytest.org/) and
[`ruff`](https://docs.astral.sh/ruff/), plus the runtime deps
(`schemdraw`, `matplotlib`, `jsonschema`, `ruamel.yaml`). The full
declared list lives in [`pyproject.toml`](../../pyproject.toml).

## Step 5 — Configure per-developer env vars (optional)

The repo ships [`.envrc.example`](../../.envrc.example) as a template
for paths and credentials that vary per developer (`ANTHROPIC_API_KEY`,
`CS_PARTSLEDGER_PATH`, `CS_PYTHON`).

If you use [`direnv`](https://direnv.net):

```bash
cp .envrc.example .envrc
# edit .envrc, fill in values
direnv allow
```

Otherwise, export the variables manually in your shell init file. The
project code references these as `$CS_*` and never hard-codes literal
paths — see [CLAUDE.md § Project env vars](../../CLAUDE.md#project-env-vars--use-cs_-never-hard-code-paths).

## Smoke test

From a clean clone, the following sequence should land you on a green
`pytest`:

```bash
git clone https://github.com/tgd1975/CircuitSmith.git
cd CircuitSmith
bash scripts/install_git_hooks.sh
npm install -g markdownlint-cli2
python3 -m venv .venv && source .venv/bin/activate     # Ubuntu
# py -m venv .venv; .\.venv\Scripts\Activate.ps1       # Windows 11
pip install -r requirements-dev.txt
pytest
```

`pytest` exits with `0 passed` (or a small number, growing over time)
and no errors. If you reach this, the setup is complete and you can
pick up a task from [`docs/developers/tasks/OVERVIEW.md`](tasks/OVERVIEW.md).
Style conventions and the test-layout reference live in
[`CODING_STANDARDS.md`](CODING_STANDARDS.md) and
[`TESTING.md`](TESTING.md).

## CI alignment

Local setup mirrors the CI workflow at
[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml). If your
local `pytest` is green but CI is red, suspect:

- A platform-specific path the doc didn't flag (file a doc fix).
- A missing dev dep declared in CI but not in `requirements-dev.txt`
  (or vice-versa).
- An auto-fixable lint issue committed without running the pre-commit
  hook (was the hook installed?).

## Common setup problems

### `markdownlint-cli2: command not found` on commit

You skipped Step 3, or `npm install -g` landed the binary somewhere
not on `PATH`. Re-run Step 3; if it still does not resolve, run
`npm config get prefix` and confirm `<prefix>/bin` is on `PATH`.

### `pip install -r requirements-dev.txt` complains about Python version

CircuitSmith requires Python ≥ 3.11. Check with `python3 --version`
(Ubuntu) or `py --version` (Windows). On Ubuntu, install a newer
interpreter via `pyenv` or the deadsnakes PPA; on Windows, fetch from
[python.org/downloads](https://www.python.org/downloads/) and re-run
Step 4 from a fresh shell.

### Commits are rejected with `commit-policy violation`

You ran raw `git commit` instead of the `/commit` skill. The pre-commit
hook validates a one-shot token at `.git/cs-commit-token` that
`scripts/commit-pathspec.sh` writes; raw `git commit` does not write
it. Use `/commit "<message>" <file> [<file> …]` — see
[CLAUDE.md § Commits go through /commit](../../CLAUDE.md#commits-go-through-commit--always).

### `git pull` rejected by the security-review hook

The `pre-merge-commit` hook scanned the incoming diff and flagged
something. Read `.claude/security-review-latest.md` for the report. If
the pull is known-good (e.g. your own branch coming back from a
re-base), bypass with:

```bash
CS_SKIP_SECURITY_REVIEW=1 git pull
```

The bypass is logged.

### `$CS_*` env vars unset

The code references `$CS_PARTSLEDGER_PATH`, `$CS_PYTHON`, and
`$ANTHROPIC_API_KEY` directly. If a script complains about an unset
or empty `$CS_*` variable, you skipped Step 5. Re-copy
`.envrc.example`, fill in the value, and re-load your shell (or
`direnv allow`).

### Hooks "stop working" after re-cloning the repo

`.git/hooks/` is not in the working tree and does not survive a
re-clone. Re-run Step 2 in the new clone.
