---
name: status
description: Run the routine git reconnaissance bundle as four parallel Bash calls — current branch, last 3 commits, staged short, working short. Use this instead of separate ad-hoc invocations or compound shell commands.
---

# status

Invoked as `/status` whenever you would otherwise reach for any of:

- `git status` / `git status --short`
- `git log --oneline -3` (or `-5`, `-8`, `-10`)
- `git rev-parse --abbrev-ref HEAD` / `git branch --show-current`
- Composites like `git log --oneline -3 && git status --short`

The skill emits **four independent Bash calls in a single tool-use
turn** (parallel). Each call is a plain `git` invocation that matches
a dedicated allowlist entry, so the bundle does not force a
permission prompt the way a compound `{ printf …; git …; … }` does.

## Steps

Issue these four calls in parallel — one message, four Bash tool
blocks:

| # | Command | Purpose |
|---|---|---|
| 1 | `git rev-parse --abbrev-ref HEAD` | Current branch. |
| 2 | `git log --oneline -3` | Last three commits. |
| 3 | `git diff --cached --name-status` | Staged-file summary. |
| 4 | `git status --short` | Working-tree summary. |

After the four results return, format them as a short prose report
in your reply — headed sections (`Branch:`, `Last commits:`,
`Staged:`, `Working tree:`) keep it scan-friendly. Do **not** add a
shell `printf`/`echo` to label the output: that's what your prose is
for, and pulling text-emitting commands into the bundle defeats the
allowlist.

If any of the four fails (e.g. not in a git repo), let the error
surface — do not swallow it.

## Why not one compound call

A compound like `{ printf '...'; git rev-parse ...; git status ...; }`
requires the project's permission allowlist to grant **every**
segment, including `printf`. The project deliberately does not
allow-list `printf:*` / `echo:*` to discourage the broader
shell-chaining habit (see CLAUDE.md § Bash commands — no diagnostic
suffix). Four parallel `git` calls each match a `git:*` rule cleanly
and produce no extra prompts.

## When to use

- At the start of a session to anchor on current state before deciding next steps.
- After a commit or branch switch to confirm the new state.
- Whenever you'd otherwise reach for two or more of the recon commands above.

## When NOT to use

- When you only need one specific piece (e.g. just the branch name for a
  conditional). Reach for the targeted command — `/status` is for the bundle.
- For diff content. Use `git diff` / `git diff --cached` directly.
