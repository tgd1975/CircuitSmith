# Project: CircuitSmith

> *CircuitSmith forges schematics. PartsLedger keeps the record CircuitSmith reads.*

CircuitSmith generates schematics from declarative component descriptions. It is
the schematic-design sibling of [PartsLedger](https://github.com/tgd1975/PartsLedger)
(the parts inventory) and the spiritual successor to
[`IDEA-027`](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-027-circuit-skill.md)
in [AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal).

The repo is currently at concept stage — the inherited dossier (`idea-001.*`)
lives in [`docs/developers/ideas/archived/`](docs/developers/ideas/archived/);
it was copied from AwesomeStudioPedal's IDEA-027 companion files and archived
on conversion to EPIC-001..006. Predecessor artefacts the dossier references —
`scripts/generate-schematic.py`, `data/config.json`, `docs/builders/wiring/` —
live in the AwesomeStudioPedal repo, not here.

## OS context

This project is developed on both **Windows 11** and **Ubuntu**. At the start
of every session, check the platform from the system environment info (or run
`uname -s`) and apply the correct shell syntax. Run `/os-context` if in doubt.

## Missing executables

When a CLI tool is not found (e.g. `markdownlint`, `jq`):

1. Try once with the most obvious alternative (`npx`, full path).
2. If it still fails, **stop and ask the user** to install it — do not spiral
   through fallback strategies or reimplement the tool's logic.

## Human interaction — batch questions, don't loop

If N questions can be asked simultaneously, ask all N at once. Only use a
sequential loop when each answer genuinely depends on the previous one.

## Auto-activate tasks when work begins

As soon as you actually start working on a task — i.e. you are about to make
edits in service of `TASK-NNN` — invoke `/ts-task-active TASK-NNN` **before
the first such action**. Pure reading / planning does not count. Do not commit
the activation; it rides along with the first real commit for the task.

## Commits go through /commit — always

Every commit must flow through the `/commit` skill, which uses git's pathspec
form (`git commit -m "..." -- <files>`) via `scripts/commit-pathspec.sh`. The
script writes a one-shot token at `.git/cs-commit-token`; the pre-commit hook
validates it and rejects raw `git commit` invocations.

**Bypass:** `CS_COMMIT_BYPASS="<reason>"` in the env. Logged to
`.git/cs-commit-bypass.log`. Reserved for interactive rebase, recovery from a
broken `/commit` skill, and rare manual repo surgery.

Stage and commit only the files **you** changed. If `git status` shows files
you did not touch, leave them alone unless the user explicitly says
"commit everything".

## Project env vars — use `$CS_*`, never hard-code paths

Per-developer paths and credentials live in `.envrc` and are exposed as
`$CS_PARTSLEDGER_PATH`, `$CS_PYTHON`, `$ANTHROPIC_API_KEY`. Reference these
in commands and skills — never retype literal paths or keys inline. Template
is at [.envrc.example](.envrc.example).

## Task-system regen — use /housekeep

After any task-system file change (status edits, idea moves, epic edits),
invoke `/housekeep` rather than running `python scripts/housekeep.py --apply`
directly.

The four index files (`docs/developers/tasks/{OVERVIEW,EPICS,KANBAN}.md`,
`docs/developers/ideas/OVERVIEW.md`) are entirely generated. If they show as
modified in `git status`, sweep them into any commit — they have no per-author
authorship.

## Task-system installation

The task-system scripts (`scripts/housekeep.py`, `update_*.py`, etc.) and
skills (`.claude/skills/ts-*`) are an **installed copy** of the upstream
`awesome-task-system` package. This repo is not the package's home — edits
land here directly, and the upstream is consulted by hand if drift becomes
a problem. There is no in-repo sync mechanism.

## Skill registration

When adding a new skill (creating `.claude/skills/<name>/SKILL.md`), always
also add `<name>` to `enabled_skills` in [.vibe/config.toml](.vibe/config.toml).
