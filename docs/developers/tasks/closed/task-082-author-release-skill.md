---
id: TASK-082
title: Author /release skill and register in .vibe/config.toml
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Senior
human-in-loop: No
epic: circuit-skill-packaging
order: 11
prerequisites: [TASK-081]
---

## Description

Author the agent-facing `/release` skill that drives the release
workflow scaffolded in TASK-081. Mirrors the shape of
AwesomeStudioPedal's
`../../../../../../AwesomeStudioPedal/.claude/skills/release/SKILL.md`
— same step order, same safety checks — but adapted to CircuitSmith's
shorter lockstep (two version files vs ASP's five) and Python-only
delivery model.

Two sub-deliverables:

1. **`.claude/skills/release/SKILL.md`** — skill file invoked as
   `/release vX.Y.Z`. Required behaviour:
   - **Verify clean state**: `git status` is clean.
   - **Verify branch**: on `main` (CircuitSmith does not maintain
     `release/*` branches — releases tag `main` directly).
   - **Read current version** from `src/circuitsmith/__init__.py`
     (`__version__`), confirm with user before bumping.
   - **Bump in lockstep**: edit `__version__` in
     `src/circuitsmith/__init__.py` *and* `version` in `pyproject.toml`
     to the canonical `X.Y.Z` form (no `v` prefix in either file; the
     `v` prefix lives only on the git tag).
   - **Archive closed tasks** for the release using the existing
     task-system mechanics (`scripts/housekeep.py`'s archive step + a
     `--release vX.Y.Z` invocation, if supported; otherwise document
     the manual `git mv` analogue from ASP).
   - **Regenerate task overviews** via `/housekeep`.
   - **Snapshot overviews** with `python scripts/release_snapshot.py vX.Y.Z`.
   - **Regenerate burn-up** with `python scripts/release_burnup.py`.
   - **Promote CHANGELOG**: rename `[Unreleased]` to
     `[vX.Y.Z] — YYYY-MM-DD` and seed a fresh empty `[Unreleased]`
     section above it.
   - **Commit the bump+archive+CHANGELOG** through `/commit`. Falls
     back to `CS_COMMIT_BYPASS="release vX.Y.Z multi-file bump"` only
     if the pre-commit hook trips on a large file count — bypass is
     logged to `.git/cs-commit-bypass.log` per repo policy.
   - **Create annotated tag** `vX.Y.Z` (literal `v` prefix here, and
     only here).
   - **Push commit + tag**: `git push` then `git push --tags`. This
     step is remote-effecting and per
     [AUTONOMY.md § No-published-effect-without-approval](../../AUTONOMY.md#no-published-effect-without-approval)
     requires explicit user approval per invocation. The skill body
     must surface a confirmation prompt before running the push pair.
   - **Hand off** to `.github/workflows/release.yml` (triggered by the
     pushed tag) — skill prints the workflow URL for the user to watch.

2. **Register `release` in `.vibe/config.toml`** under
   `enabled_skills`. Per CLAUDE.md ("Skill registration"), no entry
   means no invocation.

A `/release-branch` companion (squash-merge variant) is **out of
scope** for this task. CircuitSmith currently follows the squash-merge
policy via `/commit` directly without a dedicated skill; if a
recurring need surfaces, file it as a follow-up task. (Rationale:
ASP's `/release-branch` exists because ASP releases sometimes cut from
feature branches; CircuitSmith's PyPI flow always cuts from `main`,
so the variant is dead weight today.)

## Acceptance Criteria

- [x] `.claude/skills/release/SKILL.md` exists with the step order and
      safety checks described above (13 steps mirroring ASP's
      `/release`, two-file lockstep, explicit push-approval gate at
      step 12).
- [x] `release` is added to `enabled_skills` in `.vibe/config.toml`
      (alphabetical position between `os-context` and `status`).
- [x] The SKILL.md body explicitly identifies `git push` +
      `git push --tags` as remote-effecting actions requiring
      per-invocation user approval (step 12 + the "Don't push
      without approval" anti-pattern).
- [x] The skill references TASK-081's `RELEASING.md` as the canonical
      procedure — "RELEASING.md is the canonical procedure; this
      skill is the operational driver" appears in the description
      sentence and in the body's preamble.
- [x] No code in the skill body promises behaviour the infrastructure
      from TASK-081 does not provide. `/release-branch` is
      explicitly out-of-scope and the body says so.

## Test Plan

- Dry-run rehearsal: invoke `/release v0.0.1-rehearsal` against a
  scratch branch in a throwaway clone; stop before the
  `git push`/tag-push step; verify version-bump edits, CHANGELOG
  promotion, snapshot output. Roll back the rehearsal commit.
- Manual review of the SKILL.md for: clean-state check, branch check,
  lockstep edits, push-approval gate.
- TASK-080 is the live end-to-end test — `/release v0.1.0` will be the
  first real invocation.

## Prerequisites

- **TASK-081** — `RELEASING.md` and `release.yml` must exist so the
  skill has a procedure to drive and a workflow to hand off to.

## Notes

Per the
[Mirror AwesomeStudioPedal](../../../../../.claude/projects/-home-tobias-Dokumente-Projekte-CircuitSmith/memory/feedback-mirror-awesomestudiopedal.md)
feedback memory, the skill mirrors ASP's `/release` step order so a
maintainer who has used the ASP version can use this one without
re-learning the flow. Differences from ASP are confined to the
two-file lockstep (vs five) and the PyPI-publishing hand-off (vs
ASP's firmware + APK + GitHub Release fan-out).

The push step is the one-way door. Until the tag is pushed, every
edit in the release flow is locally reversible. After the push,
`release.yml` will attempt a PyPI upload — and PyPI uploads are
irreversible per [PyPI policy](https://pypi.org/help/#file-name-reuse).
This is why the skill body must surface explicit approval at the
push step, not earlier.
