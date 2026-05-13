---
id: TASK-080
title: Publish circuitsmith package to PyPI (first real 0.1.0)
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Senior
human-in-loop: Main
epic: circuit-skill-packaging
order: 8
prerequisites: [TASK-042, TASK-081, TASK-082]
---

## Autonomy

`Main` HIL — pushes a build artefact to a public registry. PyPI
uploads are irreversible (the project name + version combination
cannot be re-used after publication). Agent prepares the build,
verifies the wheel, drafts `RELEASING.md`; user owns the
`pypi-publish` action.

## Description

Phase 7 of EPIC-006 under [ADR-0012](../../adr/0012-library-as-installable-package.md).
Replaces the retired standalone-skill-repo extraction path
(TASK-043 / TASK-044 / TASK-045) with a Python-native publication
flow.

Four sub-deliverables:

1. **Configure `python -m build`.** Verify `pyproject.toml` produces
   a wheel and sdist that contain the full `circuitsmith` package
   tree, including the `*.json` schemas under `circuitsmith/schema/`
   (the `package-data` entry from TASK-077 makes this work). The
   wheel must install cleanly into a fresh venv:
   `python -m venv /tmp/v && /tmp/v/bin/pip install dist/circuitsmith-*.whl`
   then `import circuitsmith` and a smoke render.
2. **Set up PyPI trusted publishing.** Register the project on PyPI
   (the name `circuitsmith` is reserved — see
   [pyproject.toml](../../../../pyproject.toml)). Configure
   [trusted publishing](https://docs.pypi.org/trusted-publishers/)
   tied to this GitHub repo so the publish action runs from the
   tagged release workflow without long-lived API tokens. Token-based
   publishing is the fallback if trusted publishing setup hits a
   blocker.
3. **Write `RELEASING.md`** in this repo (not a standalone skill
   repo — that model is obsolete under ADR-0012). Cover: when to cut
   a release, semver policy for the package surface, tag-naming
   convention (`v0.1.0`, `v0.1.1`, …), how `__version__` in
   `src/circuitsmith/__init__.py` and `version` in `pyproject.toml`
   stay in sync, and the GitHub release-workflow that triggers the
   PyPI upload on tag push.
4. **Cut the first real release.** Bump `__version__` from
   `0.1.0.dev0` to `0.1.0`, tag `v0.1.0` on `main`, push the tag;
   the release workflow publishes to PyPI. Confirm the package is
   installable via `pip install circuitsmith==0.1.0` from a fresh
   environment.

The soft prerequisite from the EPIC-006 body — "skill has been used
on at least one real circuit addition" — gates the version bump from
`0.1.0.dev0` to `0.1.0`. Agent should not bump unilaterally; user
decides when real-world use has accumulated enough to anchor a
stability claim.

## Acceptance Criteria

- [x] `python -m build` produces `circuitsmith-0.1.0-py3-none-any.whl`
      and `circuitsmith-0.1.0.tar.gz` under `dist/` (local build
      verified before the tag push).
- [x] The wheel installs into a fresh venv (verified against the
      local build before pushing).
- [x] PyPI trusted publishing is configured (GitHub `pypi` env with
      required-reviewer protection; trusted publisher registered on
      pypi.org); token-based fallback documented (commented out) in
      `release.yml` and `RELEASING.md`.
- [x] `RELEASING.md` exists at the repo root (shipped in TASK-081).
- [x] `circuitsmith==0.1.0` is installable from PyPI — verified by
      `pip install circuitsmith==0.1.0` in a fresh `/tmp/cs-pypi-verify/.venv`
      with `import circuitsmith; circuitsmith.__version__` returning
      `'0.1.0'`.
- [x] `v0.1.0` tag exists on `main` and the release workflow run
      against it is green (GitHub Actions run 25822431200: build 24s,
      publish 20s, github-release 7s — all ✓).

## Closure note

End-to-end PyPI publication landed on 2026-05-13 via the new
`/release` skill (TASK-082) driving the scaffolding from TASK-081:

- Squash-merge of `release/epic-006-circuit-skill-packaging`
  (commit `a8f7718`) shipped the `/circuit` skill, `/release` skill,
  `RELEASING.md`, `release.yml`, and the version-lockstep test.
- Release commit (`722d7f1`) bumped `__version__` and
  `[project] version` from `0.1.0.dev0` to `0.1.0` in lockstep,
  promoted `CHANGELOG.md` `[Unreleased]` to `[v0.1.0] — 2026-05-13`
  (and condensed it from ~880 to ~110 lines on user feedback —
  see [[feedback-changelog-concise]]), and wrote the
  `archive/v0.1.0/` task-system snapshots.
- Tag `v0.1.0` pushed to `origin/main`; `release.yml` ran clean:
  build → publish (trusted publishing via
  `pypa/gh-action-pypi-publish`) → GitHub Release. The user-driven
  approval gate on the `pypi` environment fired as designed.

The Node.js 20 deprecation warnings on the release.yml run
(`actions/checkout@v4`, `actions/setup-python@v5`,
`actions/upload-artifact@v4`, `actions/download-artifact@v4`,
`softprops/action-gh-release@v2`) are informational — refresh
to Node.js 24-compatible action versions before Sept 2026.
Tracked as a follow-up, not blocking this closure.

## Test Plan

Manual verification: build the wheel locally, smoke-install into a
throwaway venv, smoke-render a fixture circuit. After PyPI upload,
fresh-install in another throwaway venv to confirm the published
artefact matches the local build.

## Prerequisites

- **TASK-042** — Skill `docs/` must be finalised; `RELEASING.md`
  links into the skill docs from the published-package perspective.
- **TASK-081** — Release workflow scaffolding (RELEASING.md,
  release.yml, version-lockstep guard) must exist; this task is its
  first live consumer.
- **TASK-082** — `/release` skill must exist; this task drives the
  publish via the skill rather than ad-hoc shell.

TASK-041 (five-test acceptance ceremony) is **not** a prerequisite as
of the 2026-05-13 EPIC-006 reorganisation. The soft "skill has been
used on at least one real circuit addition" gate documented in the
EPIC-006 body still applies to the `0.1.0.dev0 → 0.1.0` version
bump; that gate is satisfied by ordinary skill use, not by the
formal five-test ceremony.

Implicit prerequisite (not an EPIC-006 task): TASK-077 (atomic
relocation to `src/circuitsmith/`) must have landed before this
task can run — there is no `circuitsmith` package to publish
otherwise. Cross-epic prerequisite into EPIC-010.

## Notes

The first real release crosses a one-way door: once `circuitsmith
0.1.0` is on PyPI, the name + version is reserved forever. Bump only
after the soft "real circuit use" gate is satisfied per the EPIC-006
body. Agent surfaces the build artefacts for user review; user
executes the upload.

`RELEASING.md` is the operational counterpart of
[ADR-0012](../../adr/0012-library-as-installable-package.md) — the
ADR records the decision, `RELEASING.md` records the procedure that
implements it.
