---
id: TASK-081
title: Author release workflow scaffolding (RELEASING.md + release.yml + version lockstep)
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Senior
human-in-loop: No
epic: circuit-skill-packaging
order: 10
prerequisites: []
---

## Description

Author the general release workflow scaffolding for CircuitSmith, mirroring
the shape of AwesomeStudioPedal's release flow (see
`../../../../../../AwesomeStudioPedal/docs/developers/RELEASE_CHECKLIST.md`)
but adapted for a single-deliverable Python package under
[ADR-0012](../../adr/0012-library-as-installable-package.md).

This task ships the *infrastructure* — the docs, workflow file, and
version-bump conventions. TASK-082 ships the agent-facing `/release`
skill that drives this infrastructure. TASK-080 (first real `0.1.0`
publish) is the first consumer.

Four sub-deliverables:

1. **`RELEASING.md`** at the repo root. Covers:
   - When to cut a release (closed-epic boundary, fix rollup, manual
     trigger) — analogue of ASP's `RELEASE_CHECKLIST.md` but Python-only.
   - Semver policy for the package surface (what counts as MAJOR /
     MINOR / PATCH for `circuitsmith`'s public API).
   - Tag-naming convention (`vX.Y.Z` with literal `v` prefix to mirror
     AwesomeStudioPedal; semver triple after).
   - Version-lockstep table — `__version__` in `src/circuitsmith/__init__.py`
     and `version` in `pyproject.toml` must stay in sync; the lockstep is
     shorter than ASP's (two files, not five) but the policy is the same.
   - CHANGELOG promotion procedure (`[Unreleased]` → `[vX.Y.Z] — YYYY-MM-DD`,
     manual, performed by `/release`).
   - Task-system snapshot step (`python scripts/release_snapshot.py vX.Y.Z`
     — the script already exists in CircuitSmith).
   - Burn-up regeneration (`python scripts/release_burnup.py` — already exists).
   - Tag-and-push handoff to `.github/workflows/release.yml`, which
     publishes to PyPI.

2. **`.github/workflows/release.yml`** — GitHub Actions workflow that
   triggers on tag push matching `v*`. Steps:
   - Checkout, set up Python 3.11.
   - `python -m pip install --upgrade build`.
   - `python -m build` → produces wheel + sdist under `dist/`.
   - Publish to PyPI via [trusted publishing](https://docs.pypi.org/trusted-publishers/)
     using the `pypa/gh-action-pypi-publish` action. Token-based fallback
     documented but not wired by default (per TASK-080 acceptance).
   - Create a GitHub Release on the tag with the `dist/*` artefacts
     attached and the relevant CHANGELOG slice as the release body
     (mirror ASP's `release.yml` shape).

3. **CHANGELOG promotion convention** — verify the existing
   `CHANGELOG.md` follows Keep-a-Changelog, document the
   `[Unreleased]` → `[vX.Y.Z] — YYYY-MM-DD` move in `RELEASING.md`, and
   add a one-line policy note to `CLAUDE.md` ("CHANGELOG release
   promotion rides with the release commit" — analogue of the existing
   "CHANGELOG updates ride with the merge" rule).

4. **Version-lockstep guard** — small test under `scripts/tests/`
   (e.g. `test_version_lockstep.py`) asserting that
   `circuitsmith.__version__` equals the `[project] version` in
   `pyproject.toml`. Cheap defence against forgetting one of the two
   files on bump. Wired into the existing pytest run; no new CI job.

## Acceptance Criteria

- [x] `RELEASING.md` exists at the repo root with the six sections named above.
- [x] `.github/workflows/release.yml` exists, parses as valid YAML, and is
      referenced from `RELEASING.md`.
- [x] PyPI publishing is configured for **trusted publishing**;
      token-based fallback is documented (commented out in `release.yml`)
      in `RELEASING.md` § "Tag-and-push hand-off" and inline in the
      workflow.
- [x] `scripts/tests/test_version_lockstep.py` exists and is green.
- [x] `CLAUDE.md` carries the CHANGELOG-release-promotion note as a
      sibling to "CHANGELOG updates ride with the merge".
- [x] `docs/developers/CI_PIPELINE.md` documents `release.yml` under
      `## Workflows` (moved from the prior "Future workflows"
      placeholder).

## Test Plan

- `python -m build` runs locally and produces a wheel + sdist under
  `dist/`.
- `pytest scripts/tests/test_version_lockstep.py` is green.
- `release.yml` parses as valid GitHub Actions YAML (loaded via
  `yaml.safe_load`; no live workflow run in this task — that happens in
  TASK-080 with the first tag).
- Manual smoke-read of `RELEASING.md` for completeness against the
  acceptance criteria.

## Prerequisites

None within EPIC-006. Implicit cross-epic prerequisite: TASK-077 (atomic
relocation to `src/circuitsmith/`, EPIC-010) — already closed — so the
package surface that `release.yml` builds against exists.

## Notes

Mirrors AwesomeStudioPedal's release shape per the
[Mirror AwesomeStudioPedal](../../../../../.claude/projects/-home-tobias-Dokumente-Projekte-CircuitSmith/memory/feedback-mirror-awesomestudiopedal.md)
feedback memory — for governance/onboarding artefacts shared between the
two repos, the sister project's shape is the default, unless a
CircuitSmith-specific concern overrides.

The `release_snapshot.py` and `release_burnup.py` scripts are already
ported to CircuitSmith from ASP; this task wires them into the
documented release flow rather than (re-)authoring them.

PyPI trusted publishing requires a one-time registration step on
pypi.org tying this GitHub repo to the `circuitsmith` project. Per
[no-published-effect-without-approval](../../AUTONOMY.md#no-published-effect-without-approval),
the registration itself is a remote action — agent prepares the
configuration; user performs the click-through on pypi.org. That click
happens in TASK-080, not here; this task only writes the workflow that
will *use* the trust relationship.
