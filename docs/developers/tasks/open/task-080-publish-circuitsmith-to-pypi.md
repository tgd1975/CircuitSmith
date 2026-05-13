---
id: TASK-080
title: Publish circuitsmith package to PyPI (first real 0.1.0)
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Main
epic: circuit-skill-packaging
order: 8
prerequisites: [TASK-041, TASK-042]
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

- [ ] `python -m build` produces `circuitsmith-0.1.0-py3-none-any.whl`
      and `circuitsmith-0.1.0.tar.gz` under `dist/`.
- [ ] The wheel installs into a fresh venv and a smoke render
      succeeds (`from circuitsmith.renderer import render; render(...)`
      against a fixture circuit).
- [ ] PyPI trusted publishing (or token-based fallback) is configured
      and documented in `RELEASING.md`.
- [ ] `RELEASING.md` exists at the repo root with the four sections
      named above.
- [ ] `circuitsmith==0.1.0` is installable from PyPI (verified by
      `pip download circuitsmith==0.1.0 --no-deps` in a clean env).
- [ ] `v0.1.0` tag exists on `main` and the release workflow run
      against it is green.

## Test Plan

Manual verification: build the wheel locally, smoke-install into a
throwaway venv, smoke-render a fixture circuit. After PyPI upload,
fresh-install in another throwaway venv to confirm the published
artefact matches the local build.

## Prerequisites

- **TASK-041** — Phase 6 acceptance tests must pass; the published
  package must be usable for the workflows the acceptance tests
  exercise.
- **TASK-042** — Skill `docs/` must be finalised; `RELEASING.md`
  links into the skill docs from the published-package perspective.

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
