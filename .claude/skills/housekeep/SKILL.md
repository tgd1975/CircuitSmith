---
name: housekeep
description: Run scripts/housekeep.py --apply and report the move/regen summary. The regenerated task-system index files (OVERVIEW.md, EPICS.md, KANBAN.md, ideas OVERVIEW) are NOT staged here — they ride along in the caller's next `/commit` pathspec. Use this after any task-system file change instead of running the script directly.
---

# housekeep

Invoked as `/housekeep` whenever you would otherwise run
`python scripts/housekeep.py --apply` by hand — i.e. after any of:

- a task `status:` change you didn't make via `/ts-task-active` /
  `/ts-task-done` / `/ts-task-pause` / `/ts-task-reopen` (those skills
  already invoke housekeep internally),
- a manual idea move under `docs/developers/ideas/`,
- an epic edit (rename, owner change, frontmatter tweak),
- any other ad-hoc OVERVIEW regen.

The skill is a thin wrapper that owns the canonical invocation and
prints the move summary housekeep emits. It does **not** stage
anything — staging happens at the next `/commit` invocation via the
pathspec, per the project's "pass files inline to /commit, never
`git add` standalone" rule.

## Steps

1. Run housekeep:

   ```bash
   python scripts/housekeep.py --apply
   ```

   The script prints a summary of file moves and which index files
   it regenerated. Pass that summary through to the user verbatim —
   do not paraphrase, the move list is the receipt.

2. Note the regenerated files for the next `/commit`. The four index
   paths are:

   - `docs/developers/tasks/OVERVIEW.md`
   - `docs/developers/tasks/EPICS.md`
   - `docs/developers/tasks/KANBAN.md`
   - `docs/developers/ideas/OVERVIEW.md`

   If housekeep performed file moves (`MOVE old-path -> new-path`
   lines in the summary), the **old** and **new** paths must both
   appear in the next `/commit` pathspec for git to record the
   rename.

3. Do **not** run `git add`. The "no git add — use /commit pathspec"
   rule applies even (and especially) to housekeep-generated files;
   `git add` defeats the atomic-pathspec contract that
   `scripts/commit-pathspec.sh` and the pre-commit hook rely on.

4. Do **not** create a commit. The regenerated index files ride
   along with the change that triggered the regen — the caller's
   next `/commit` carries them.

5. Do **not** touch files housekeep did not regenerate. Per the
   project's "commit only your own work" rule, foreign working-tree
   changes from parallel sessions stay where they are.

## When NOT to use

- Inside `/ts-task-active`, `/ts-task-done`, `/ts-task-pause`,
  `/ts-task-reopen` — those skills already run housekeep themselves.
- For a `--check` (read-only) audit. Run `python scripts/housekeep.py`
  without `--apply` directly; this skill is the apply-side wrapper.

## Skill registration

Registered in [.vibe/config.toml](../../../.vibe/config.toml)'s
`enabled_skills` list per the project's CLAUDE.md skill-registration
rule.
