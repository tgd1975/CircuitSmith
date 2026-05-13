# Releasing CircuitSmith

How CircuitSmith cuts a release — the operational counterpart of
[ADR-0012](docs/developers/adr/0012-library-as-installable-package.md)
(the *decision* to publish as a Python package) and
[`docs/developers/COMMIT_POLICY.md`](docs/developers/COMMIT_POLICY.md)
(the *mechanics* of how the bump commit lands).

The agent-facing driver is the [`/release`](.claude/skills/release/SKILL.md)
skill — point it at a target version and it walks the steps in this
document. This document is the *source of truth*; the skill is the
*operational driver*.

## When to cut a release

- **Closed-epic boundary.** When an epic with public-API surface
  closes (renderer / ERC / exporter / skill changes that callers see),
  cut a minor or patch release so consumers can pin to a tag.
- **Fix rollup.** A handful of patch-worthy fixes have landed since
  the last release and at least one consumer is asking for them.
- **Manual trigger.** The maintainer wants to anchor a stability
  claim against the most recent `main`.

There is no fixed cadence. CircuitSmith ships when there is something
worth shipping, not on a calendar.

## Semver policy

`circuitsmith` follows [Semantic Versioning](https://semver.org/) for
the package's **public Python API** — the names exposed via
`from circuitsmith import …` and the documented CLI surfaces
(`python -m circuitsmith.{renderer,erc_engine,markdown,knowledge.validate_catalog}`).

| Bump | When |
|------|------|
| `MAJOR` (X.0.0) | Backwards-incompatible removal or rename of a public symbol, CLI flag, or `.circuit.yml` schema field. |
| `MINOR` (0.Y.0) | New public symbol, new CLI flag, additive `.circuit.yml` field, new ERC check (S/E IDs are stable per `docs/erc-checks.md`). |
| `PATCH` (0.0.Z) | Bug fix, internal refactor, documentation, layout-rubric tweak that doesn't change the public surface. |

Until the first non-`dev` release, `0.x` versions are considered
pre-stable; consumers should pin to an exact version. Once `1.0.0`
ships, semver applies as documented above.

## Tag-naming convention

Tags use the literal `v` prefix followed by the semver triple:

```text
v0.1.0
v0.1.1
v0.2.0
```

This mirrors AwesomeStudioPedal so a maintainer fluent in either
project's release flow doesn't have to relearn the tag shape. The
`v` prefix is reserved for **tags only**; both
`src/circuitsmith/__init__.py` and `pyproject.toml` carry the
unprefixed triple (`0.1.0`).

## Version lockstep — two files, one truth

The package version is mirrored in exactly two files:

| File | Field | Format |
|------|-------|--------|
| `src/circuitsmith/__init__.py` | `__version__ = "X.Y.Z"` | unprefixed semver |
| `pyproject.toml` | `[project] version = "X.Y.Z"` | unprefixed semver |

Both must be edited in the same commit. A drift between the two is a
shipping bug — the wheel built from `pyproject.toml` reports one
version while `import circuitsmith; circuitsmith.__version__` reports
another.

The lockstep is enforced by
[`scripts/tests/test_version_lockstep.py`](scripts/tests/test_version_lockstep.py):
the test parses both files and asserts equality. It runs in the
default `pytest` invocation, so the local pre-commit hook, the CI
gate, and `/release`'s dry-run all catch drift before a tag lands.

## CHANGELOG promotion

`CHANGELOG.md` follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
On release, the working `[Unreleased]` section is renamed to
`[vX.Y.Z] — YYYY-MM-DD` and a fresh empty `[Unreleased]` block is
seeded above it:

```diff
+ ## [Unreleased]
+
- ## [Unreleased]
+ ## [vX.Y.Z] — 2026-05-13

  ### Added
  - …
```

The promotion is **manual** — `/release` performs it as part of the
bump commit. No bullets are reordered, reworded, or merged during
promotion; the section as-built is what ships. Per the
"CHANGELOG release-promotion rides with the release commit" rule in
[CLAUDE.md](CLAUDE.md#changelog-release-promotion-rides-with-the-release-commit),
the promotion is part of the same commit that bumps the version
files — not a follow-up.

## Task-system snapshot

After the release commit lands (but before tagging) the live
`OVERVIEW.md` / `EPICS.md` / `KANBAN.md` get frozen into a
per-release snapshot:

```bash
python scripts/release_snapshot.py vX.Y.Z
```

The script writes `archive/<version>/{OVERVIEW,EPICS,KANBAN}_vX.Y.Z.md`,
stripping the auto-generation markers so `housekeep.py` doesn't try
to touch them on later runs. The snapshot answers "what was the task
state as of this release" without forcing later edits to leave
historical entries untouched.

## Burn-up regeneration

The cumulative burn-up at the top of `OVERVIEW.md` gets re-rendered:

```bash
python scripts/release_burnup.py
```

This block lives between `<!-- BURNUP:START -->` and
`<!-- BURNUP:END -->` markers and counts closed tasks / closed epics
/ effort hours since the last tag. Rides into the same commit as the
version bump and CHANGELOG promotion.

## Tag-and-push hand-off to release.yml

The final step is an annotated tag pushed to GitHub:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push
git push --tags
```

The `git push` invocations are **remote-effecting actions** and
require explicit per-invocation user approval per
[`docs/developers/AUTONOMY.md` § No-published-effect-without-approval](docs/developers/AUTONOMY.md#no-published-effect-without-approval).
The `/release` skill must not push without surfacing a confirmation
prompt.

The tag push triggers [`.github/workflows/release.yml`](.github/workflows/release.yml),
which:

1. Checks out the tag.
2. Sets up Python 3.11 (the lower bound of `requires-python`).
3. Runs `python -m build` to produce `dist/circuitsmith-X.Y.Z-py3-none-any.whl`
   and `dist/circuitsmith-X.Y.Z.tar.gz`.
4. Publishes both artefacts to PyPI via
   [trusted publishing](https://docs.pypi.org/trusted-publishers/)
   using `pypa/gh-action-pypi-publish`. No long-lived API tokens.
5. Creates a GitHub Release on the tag with the `dist/*` files
   attached and the matching `CHANGELOG.md` slice as the release
   body.

Trusted publishing requires a one-time registration on pypi.org tying
this GitHub repository to the `circuitsmith` project. The
**token-based fallback** is documented for completeness but not wired
by default: if PyPI trusted publishing is unavailable, generate an
API token scoped to the `circuitsmith` project on pypi.org, store it
as the GitHub secret `PYPI_API_TOKEN`, and uncomment the
`password: ${{ secrets.PYPI_API_TOKEN }}` line in `release.yml`.

## End-to-end summary

The `/release vX.Y.Z` skill drives this whole flow. The verbatim step
order it follows is:

1. Verify clean working tree on `main`.
2. Confirm the new version with the user.
3. Bump `__version__` in `src/circuitsmith/__init__.py` and
   `version` in `pyproject.toml`.
4. Promote CHANGELOG `[Unreleased]` → `[vX.Y.Z] — YYYY-MM-DD`.
5. Regenerate task overviews (`/housekeep`) and burn-up
   (`release_burnup.py`); snapshot overviews
   (`release_snapshot.py vX.Y.Z`).
6. Commit the bump + CHANGELOG + snapshot + burn-up via `/commit`.
7. Create annotated tag `vX.Y.Z`.
8. Push commit + tag (requires explicit user approval).
9. Print the `release.yml` workflow URL so the user can watch the
   PyPI upload and GitHub Release publish.

If any step fails before the tag push, every edit is locally
reversible. After the push, the PyPI upload is **irreversible** —
PyPI does not permit file-name reuse for a given `(project, version)`
combination.

## Cross-references

- [ADR-0012](docs/developers/adr/0012-library-as-installable-package.md) — why CircuitSmith ships as a Python package.
- [`docs/developers/CI_PIPELINE.md`](docs/developers/CI_PIPELINE.md) — CI workflows including the release gate.
- [`docs/developers/AUTONOMY.md`](docs/developers/AUTONOMY.md) — autonomy contract, including the push-approval rule.
- [`docs/developers/COMMIT_POLICY.md`](docs/developers/COMMIT_POLICY.md) — pathspec form, provenance tokens, bypass policy.
- [`CHANGELOG.md`](CHANGELOG.md) — the log this flow promotes from.
- [`/release` skill](.claude/skills/release/SKILL.md) — the agent-facing driver for this procedure.
