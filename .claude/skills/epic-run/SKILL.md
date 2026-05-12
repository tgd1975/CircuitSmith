---
name: epic-run
description: Drive an epic to completion autonomously — walks tasks in topological order, composes over /ts-task-active, /commit, /housekeep, /ts-task-done; stops at Main/Support HIL stop-lines and surfaces a review packet.
---

# epic-run

Invoked as `/epic-run EPIC-NNN`. Drives the named epic to
completion in autonomous-implementation mode per
[`docs/developers/AUTONOMY.md`](../../../docs/developers/AUTONOMY.md).

This skill is a **composer** over existing task-system skills. It
does not re-implement state transitions. Every move through the
loop goes through `/ts-task-active`, `/commit`, `/housekeep`,
`/ts-task-done`, and `/check-branch` — bugs in those skills surface
at the composer level rather than hiding behind a wrapper.

## Preconditions

Before invoking `/epic-run`:

- [ ] Current branch matches the epic's `branch:` frontmatter
      (typically `release/epic-NNN-<slug>`). If not, `/ts-task-active`
      will nag on the first task; resolve via the `[s]witch` or
      `[c]ontinue` path before the loop starts in earnest.
- [ ] Working tree is clean (`git status` empty). The loop
      accumulates uncommitted edits while it walks; a foreign
      starting state breaks the "commit only your own work" rule.
- [ ] The user has briefed the agent on epic-specific context that
      isn't in the epic file or the dossier (rare, but
      sometimes necessary for the first task).

## Work phase

For each iteration in the work phase:

1. **Pick next task.** Walk the epic's tasks (any file under
   `docs/developers/tasks/{open,active}/` with the matching
   `epic:` field), filter to those whose `prerequisites:` are all
   closed, sort by `order:` ascending. The first remaining task is
   "next". If none, the epic is done — go to **Commit phase**.

2. **Check HIL stop-lines.** Inspect the picked task's
   `human-in-loop:` field:

   - `No` → proceed silently.
   - `Clarification` → proceed; pause for one batched
     `AskUserQuestion` call **only** if the task body explicitly
     names a decision the user must own. Otherwise, treat as `No`.
   - `Support` → proceed up to the task body's stop-line, then go
     to **Commit phase** with what's accumulated so far and exit.
   - `Main` → do not enter the task body. Go to **Commit phase**
     with what's accumulated so far and exit.

3. **Activate.** Run `/ts-task-active TASK-NNN`. This handles the
   epic/branch nag, the open→active transition, and the index
   regeneration. Skip if the task is already `active` (e.g.
   resuming a paused mid-run).

4. **Implement.** Do the task's work — edits, tests, debugging,
   ADRs filed under the
   [ADR-on-ambiguity rule](../../../docs/developers/AUTONOMY.md#adr-on-ambiguity).
   Mid-task `AskUserQuestion` calls are **not** part of the loop;
   if the agent reaches one, that's a Clarification-HIL pause and
   the protocol applies.

5. **Definition-of-done gate.** Run the checklist from
   [AUTONOMY.md § Definition of done](../../../docs/developers/AUTONOMY.md#definition-of-done).
   Every item must pass. A failure aborts the loop with a
   diagnostic; the agent fixes and re-runs.

6. **Close in-tree.** Edit the task file frontmatter:
   `status: closed`, `closed: <today>`, `effort_actual: <size>` per
   the no-peek rule. Tick acceptance-criteria boxes. Run
   `python scripts/housekeep.py --apply` — the task file moves
   from `active/` to `closed/` and the indexes regenerate.
   **No commit is made here.** Changes accumulate in the working
   tree.

7. **Loop.** Back to step 1.

## Commit phase

When the work phase finishes, the working tree contains the
accumulated changes from every task closed in the batch. Now split
those changes into **per-task commits**:

For each task closed in this batch, in dependency order (i.e. the
order they were closed):

1. Identify the files **that task owns** — its new files, the
   files only it modified, and the task body's open→closed rename.
2. `/commit "close TASK-NNN: <title>" <pathspec>` with just those
   files.

Shared files (the registries, settings file, OVERVIEW / EPICS /
KANBAN indexes, CHANGELOG, `scripts/README.md`) ride with the
**most relevant commit**, typically the last one in the batch.
Do not roll back shared files to reproduce an intermediate state
for earlier commits — forward references inside a coordinated
branch are acceptable.

The final task's commit also carries the cumulative regen of the
indexes + scripts/README + the CHANGELOG bullets covering every
task in the batch.

If a task naturally bundles with another (e.g. TASK-055's hook
mechanism + TASK-056's first three skills using that mechanism),
a single combined commit is fine — but the default is one commit
per task closure.

## Exit

On exit (epic done OR Main/Support stop-line OR
definition-of-done failure):

1. Verify the working tree is clean (every accumulated change is
   committed).
2. Surface the
   [review packet](../../../docs/developers/AUTONOMY.md#review-packet)
   to the user.
3. Stop. Do not start the next iteration. Wait for the user.

## Anti-patterns

These are the failure modes the protocol exists to prevent — do
not reach for any of them.

- **Skipping `/ts-task-active`.** The epic/branch nag and the
  status transition are load-bearing; bypassing them silently
  breaks `/check-branch`, `/housekeep`, and the index files.
- **Batching commits across tasks.** Each task closure is its own
  commit on the epic's branch. The squash-merge to `main` collapses
  them — that is the user's call at merge time, not the loop's.
- **Mid-loop user prompts that aren't HIL-defined.** If you find
  yourself wanting to ask "should I continue with the next task?",
  re-read AUTONOMY.md — the answer is no, the loop drives itself
  until a defined stop-line. End-of-turn "continue?" checkpoints
  are forbidden by [`CLAUDE.md`](../../../CLAUDE.md).
- **Resolving ambiguity by stopping.** If a decision has a
  defensible default, file an ADR and continue. Stopping is the
  exception, not the default.
- **Touching files outside the task's scope.** "While I'm in
  here" edits clobber the squash-merge story and pollute the
  commit. New tasks for new work.

## When NOT to use

- The user is sitting next to you and wants to drive task-by-task.
  Use `/ts-task-active` / `/ts-task-done` directly.
- The epic has no `branch:` field, has `branch: main`, or has tasks
  with unfixed `prerequisites:` that point outside the epic. Fix
  the metadata first.
- The epic is in a half-finished state from a prior run (some
  active tasks, no clear next-up). Resolve the active task by
  hand, then re-invoke.

## Status

`/epic-run` is a **protocol scaffold** for now — the SKILL.md
above is the operational contract the agent follows; the agent
itself is the executor. A future iteration may extract the loop
into a Python driver that orchestrates the underlying skills
explicitly, with the SKILL.md retained as documentation.
