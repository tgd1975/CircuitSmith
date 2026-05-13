---
name: release
description: Cut a CircuitSmith release — bump __version__ in src/circuitsmith/__init__.py and pyproject.toml in lockstep, promote CHANGELOG [Unreleased] → [vX.Y.Z], snapshot task overviews, regenerate burn-up, commit, tag, and push. The tag push triggers .github/workflows/release.yml which builds the wheel + sdist, publishes to PyPI via trusted publishing, and creates a GitHub Release. RELEASING.md is the canonical procedure; this skill is the operational driver.
---

# release

Invoked as `/release vX.Y.Z` (e.g. `/release v0.1.0`). If no version is
given, read the current version from `src/circuitsmith/__init__.py`
and ask the user for the target.

The canonical procedure lives in [`RELEASING.md`](../../../RELEASING.md).
This skill is the **operational driver**; if a step in this file
contradicts `RELEASING.md`, `RELEASING.md` wins and this skill gets
a correcting PR. Step order mirrors AwesomeStudioPedal's `/release`
so a maintainer fluent in either project can drive both.

## Steps

1. **Verify clean state.** Run `git status --short`. If anything is
   uncommitted, **stop** — a release must be cut from a clean working
   tree. Tell the user which files are dirty and ask them to commit
   or stash before re-invoking.

2. **Verify branch.** Run `git rev-parse --abbrev-ref HEAD`. CircuitSmith
   releases tag `main` directly — there is no `release/*` branch flow.
   If the current branch is not `main`, **stop** and ask the user to
   switch.

3. **Read current version.** Open
   [`src/circuitsmith/__init__.py`](../../../src/circuitsmith/__init__.py)
   and extract `__version__`. Read the `[project] version` from
   [`pyproject.toml`](../../../pyproject.toml). They **must** match
   (per the lockstep guard in
   [`scripts/tests/test_version_lockstep.py`](../../../scripts/tests/test_version_lockstep.py));
   if they don't, surface the drift and stop — the working tree is
   broken and the user needs to resolve it before a release makes
   sense.

4. **Confirm the new version.** Display the current version and the
   target (`v0.1.0.dev0 → v0.1.0`, for example). Ask the user to
   confirm before making any changes. Remind them that the canonical
   form is the **unprefixed semver triple** in both files; the `v`
   prefix lives **only** on the git tag.

5. **Bump in lockstep.** Edit both files:

   ```python
   # src/circuitsmith/__init__.py
   __version__ = "X.Y.Z"
   ```

   ```toml
   # pyproject.toml — under [project]
   version = "X.Y.Z"
   ```

   Do not edit any other version field — there is no Android
   `versionCode`, no `pubspec.yaml`, no `VERSION` file. Just the two
   above.

6. **Promote CHANGELOG.** In [`CHANGELOG.md`](../../../CHANGELOG.md),
   rename `## [Unreleased]` to `## [vX.Y.Z] — YYYY-MM-DD` (today's
   date) and insert a fresh empty `## [Unreleased]` block above it.
   The bullets stay where they are — no reordering, no rewording, no
   collapsing. Per the CLAUDE.md rule
   ["CHANGELOG release-promotion rides with the release commit"](../../../CLAUDE.md#changelog-release-promotion-rides-with-the-release-commit),
   the promotion edit lands in the same commit as the version bump.

7. **Regenerate task overviews.** Run `/housekeep`. This is a no-op
   unless something changed since the last regen, but it's cheap and
   keeps the snapshot honest.

8. **Snapshot overviews.** Run:

   ```bash
   python scripts/release_snapshot.py vX.Y.Z
   ```

   The script writes
   `archive/<version>/{OVERVIEW,EPICS,KANBAN}_vX.Y.Z.md` and strips
   the auto-generation markers so `housekeep.py` won't try to touch
   them later. Note any failure (e.g. the Phase 2b gate refusing the
   release without an `Override:` ack) and surface it to the user
   before continuing.

9. **Regenerate burn-up.** Run:

   ```bash
   python scripts/release_burnup.py
   ```

   This refreshes the `<!-- BURNUP:START -->…<!-- BURNUP:END -->`
   block in `OVERVIEW.md` with the cumulative numbers since the last
   tag.

10. **Commit the release bump.** Use `/commit` with all the files
    touched in steps 5–9:

    ```text
    /commit "release: vX.Y.Z" \
      src/circuitsmith/__init__.py \
      pyproject.toml \
      CHANGELOG.md \
      docs/developers/tasks/OVERVIEW.md \
      docs/developers/tasks/EPICS.md \
      docs/developers/tasks/KANBAN.md \
      archive/vX.Y.Z/OVERVIEW_vX.Y.Z.md \
      archive/vX.Y.Z/EPICS_vX.Y.Z.md \
      archive/vX.Y.Z/KANBAN_vX.Y.Z.md
    ```

    If the pre-commit hook trips on a large multi-file edit (rare;
    usually only happens when the snapshot files conflict with the
    markdown-lint glob), fall back to `CS_COMMIT_BYPASS="release
    vX.Y.Z multi-file bump"` per
    [`docs/developers/COMMIT_POLICY.md`](../../../docs/developers/COMMIT_POLICY.md).
    The bypass is logged to `.git/cs-commit-bypass.log` and reviewed
    in the maintainer's next bypass audit.

11. **Create annotated tag.** Run:

    ```bash
    git tag -a vX.Y.Z -m "Release vX.Y.Z"
    ```

    The literal `v` prefix is part of the tag; the version files
    carry the unprefixed triple. No exceptions.

12. **Push commit + tag — REQUIRES EXPLICIT USER APPROVAL.** This is
    the one-way door. Per
    [`docs/developers/AUTONOMY.md` § No-published-effect-without-approval](../../../docs/developers/AUTONOMY.md#no-published-effect-without-approval),
    `git push` is a remote-effecting action and the agent must
    surface a confirmation prompt before invoking it. Show the user:

    > About to push `vX.Y.Z` to `origin/main`. This will trigger
    > `.github/workflows/release.yml`, which uploads to PyPI. PyPI
    > does **not** permit file-name reuse — once `circuitsmith
    > X.Y.Z` is published, the name + version is reserved forever.
    > Confirm push? `[y]es / [n]o`

    On `y`, run:

    ```bash
    git push
    git push --tags
    ```

    On `n`, **stop**. Everything before this point is locally
    reversible — the user can `git tag -d vX.Y.Z` and
    `git reset --hard HEAD~1` to undo the bump commit.

13. **Hand off to release.yml.** Print the workflow URL so the user
    can watch the PyPI upload and the GitHub Release creation:

    ```text
    Tag vX.Y.Z pushed. Watch the build:
      https://github.com/tgd1975/CircuitSmith/actions/workflows/release.yml
    PyPI page (after upload):
      https://pypi.org/project/circuitsmith/X.Y.Z/
    ```

    The release.yml workflow handles everything from here: wheel +
    sdist build, smoke install verification, PyPI publish via
    trusted publishing, GitHub Release with CHANGELOG slice as body.

## Anti-patterns

- **Don't drift the lockstep.** Editing only one of
  `src/circuitsmith/__init__.py` / `pyproject.toml` leaves the other
  stale. The version-lockstep test catches this in the pre-commit
  hook — don't bypass with `--no-verify`.
- **Don't push without approval.** Even when the user invokes
  `/release` expecting a full cycle, the step-12 prompt is the
  contract. The user has the option to stop after seeing the commit
  - tag locally.
- **Don't reuse a published version.** If the user asks to "redo
  v0.1.0" after a PyPI upload failed mid-way, the answer is bump to
  `v0.1.1` — PyPI does not permit `v0.1.0` to be re-uploaded under
  any circumstance.
- **Don't reorder or reword CHANGELOG entries during promotion.** The
  bullets as written are what shipped; the release commit just
  renames the section header. If the user wants edits, they make
  them as a separate commit *before* invoking `/release`.

## `/release-branch` variant — out of scope today

AwesomeStudioPedal ships a sibling `/release-branch` skill that
squash-merges a feature branch into `main` as part of the release
flow. CircuitSmith does not need that variant today because every
release cuts from a clean `main`. If a future workflow surfaces
where releasing from a feature branch is genuinely required, file
a follow-up task — do not retrofit this skill into a dual-purpose
driver.

## Skill registration

Registered in [.vibe/config.toml](../../../.vibe/config.toml)'s
`enabled_skills` list per the project's CLAUDE.md skill-registration
rule.
