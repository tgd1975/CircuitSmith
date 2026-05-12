---
id: TASK-055
title: Code-owner skills registry and PreToolUse hook
status: closed
closed: 2026-05-12
opened: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: architecture-fitness-functions
order: 3
prerequisites: []
---

## Description

Add a registry that maps file globs to "code-owner" skills, plus a
`PreToolUse` hook in `.claude/settings.json` that fires before `Edit`
and `Write` tool calls, resolves the target path against the registry,
and surfaces the matched skill's invariants — *before* the edit lands.

This is the local edit-time analogue of GitHub CODEOWNERS, fitted to
the current solo, Claude-driven workflow. The hook catches load-bearing
edits the moment they begin, not at PR review. Per the architecture
review (item 7), this is a better fit than literal CODEOWNERS until a
second contributor joins; at that point the two layers compose (skill
at write-time, CODEOWNERS at PR-time).

This task delivers the **mechanism** — the registry and the hook
itself. The actual skill content for the first three load-bearing
files lands in [TASK-056](task-056-author-initial-code-owner-skills.md).

Components:

- `.claude/codeowners.yaml` — YAML list of `{pattern, skill}` entries.
  Globs follow the same syntax as `.gitignore`-style patterns; skill
  names map to the `co-<name>` skills authored in TASK-056.
- `scripts/codeowner_hook.py` — the hook entry point. Reads the target
  path from the hook payload, matches against the registry, prints a
  reminder block to stdout that lists: which invariants the file is
  expected to preserve, where they are sourced from in the dossier, and
  which downstream consumers a breaking change here will affect.
- `.claude/settings.json` (or `.claude/settings.local.json`) —
  registers the hook under `hooks.PreToolUse` for the `Edit` and `Write`
  tools.

The hook is silent (exits 0, no output) when the path does not match
any registry entry. It never blocks an edit; it only surfaces context.
Blocking is the contract test's job (TASK-050) — the hook is
informational.

## Acceptance Criteria

- [x] `.claude/codeowners.yaml` exists with at least one placeholder entry and a documented schema (in the file itself as a header comment).
- [x] `scripts/codeowner_hook.py` resolves a target path against the registry: matched paths emit a reminder block on stdout; unmatched paths emit nothing.
- [x] Hook is registered in `.claude/settings.json` under `hooks.PreToolUse` for `Edit` and `Write`.
- [x] `tests/test_codeowner_hook.py` covers: matched pattern emits reminder; unmatched path is silent; missing registry file is silent (not an error); malformed registry file produces a clear error and exits non-zero.
- [x] A short README in `docs/developers/` (or an `adr` entry from TASK-054) documents the pattern and how to add a new code-owner skill.

## Test Plan

Unit-test the resolver function with an in-memory registry and a
handful of paths. Integration-test the hook script by invoking it with
a fixture path and asserting the stdout shape. Manually verify the
`.claude/settings.json` integration in one Claude session by editing a
registered file and observing the reminder.

## Prerequisites

None. The mechanism is independent of the modules it eventually owns —
those skills land in TASK-056 and grow as new load-bearing files arrive.

## Notes

The hook fires only during Claude-driven edits. A human editing the
same file directly in their editor bypasses it. That is acceptable for
the current solo workflow; when a second contributor joins, layer
literal GitHub CODEOWNERS on top — they catch each other's edit paths.

### Implementation notes (closure)

- **YAML parsing.** A tiny stdlib parser (`parse_registry` in the hook
  module) handles the constrained format (`entries: list of {pattern,
  skill}`). No `ruamel.yaml`/`PyYAML` dependency at hook-invocation
  time — keeps the per-edit overhead minimal and avoids a dev-env
  setup pitfall (the hook would otherwise crash silently if dev deps
  weren't installed).
- **Glob semantics.** Implemented as gitignore-flavoured via
  `_glob_to_regex` (not Python's `fnmatch`, whose `*` crosses `/`).
  Supports `**`, `*`, `?` plus literal chars; directory-only patterns,
  negation, and explicit anchoring are out of scope.
- **Skill body extraction.** `skill_body` reads
  `.claude/skills/<skill>/SKILL.md`, strips the YAML frontmatter
  block if present, and returns the rest verbatim. Skills carry
  their own structure (invariants checklist / authority / consumers);
  the hook doesn't impose one.
- **Block-vs-warn split.** The hook exits non-zero **only** on a
  malformed registry — the AC's "clear error and exits non-zero"
  path. All other failure modes (missing registry, missing referenced
  skill, payload parse error, non-Edit/Write tool, path outside repo)
  exit 0 silently or with a stderr warning. This honours the
  "informational, never blocks" contract.
- **Docs location.** Chose `docs/developers/CODE_OWNERS.md` rather
  than a new ADR-0009 — the mechanism is documentation, not a load-
  bearing architectural decision that would warrant an immutable
  record.
- **Tests.** 26 cases in `scripts/tests/test_codeowner_hook.py`
  covering the parser, matcher, body extractor, the full `run()`
  flow with synthetic payloads, and a round-trip of the checked-in
  registry. All pass; full suite still 158 / 158 green.

Item 7 of the architecture-review recommendations
([EPIC-008](epic-008-architecture-fitness-functions.md) summary).
