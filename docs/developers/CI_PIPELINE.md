# CI Pipeline

Inventory of CircuitSmith's CI workflows, what each step gates, and
what to do when the build is red. The authoritative source is
[`.github/workflows/`](../../.github/workflows/) — if this doc and the
YAML disagree, the YAML wins; fix the doc.

## Workflows

### `ci.yml` — `CI`

Triggered on every `push` and `pull_request`. Single job (`test`)
fanned out across an OS matrix.

| Field | Value |
|---|---|
| File | [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) |
| Trigger | `push`, `pull_request` |
| OS matrix | `ubuntu-latest`, `windows-latest` |
| Python | 3.11 (lower bound of `requires-python`) |
| Node | 20 |
| `fail-fast` | `false` — one OS failing does not abort the other |

Steps, in order:

| Step | What it does | Red means |
|---|---|---|
| Checkout | `actions/checkout@v4`. | Harness failure. |
| setup-python | Installs Python 3.11. | Harness failure. |
| setup-node | Installs Node 20. | Harness failure. |
| Install Python dev deps | `pip install -r requirements-dev.txt`. | A declared dep is missing from PyPI or the lock file diverged. |
| Install markdownlint-cli2 | `npm install -g markdownlint-cli2`. | npm registry issue. |
| Markdown lint | `markdownlint-cli2 "**/*.md" "#node_modules" "#.claude/security-review-latest.md"`. Mirror of the local pre-commit step. | A `.md` file violates the configured ruleset. Reproduce locally with the same command. |
| Portability lint | `python scripts/portability_lint.py src/circuitsmith`. No-op on missing dir, so safe pre-package-scaffold. | A path or import in `src/circuitsmith/` is OS-specific. |
| Pytest | `pytest`. Picks up both test roots (`tests`, `scripts/tests`) per [`pyproject.toml`](../../pyproject.toml). | A test failed. Reproduce locally per [`TESTING.md`](TESTING.md). |
| Tutorial + gallery regression gate (TASK-101) | `python scripts/check_gallery_regression.py`. Re-renders every committed `.circuit.yml` under `docs/users/{tutorial,examples}/` and diffs the SVG / sidecars against the committed artefacts. Skips circuits without a committed SVG (the EPIC-012 gallery entries blocked on IDEA-008 / IDEA-009). | A tutorial step or gallery example's committed artefact drifted from the renderer's current output. Reproduce locally with the same command; rebase with `--rebaseline` if the drift is intentional. |

## Local mirror — the pre-commit hook

Every CI gate that runs on a *file you committed* also runs locally
via the pre-commit hook installed by
[`scripts/install_git_hooks.sh`](../../scripts/install_git_hooks.sh):

| CI step | Local equivalent |
|---|---|
| Markdown lint | `scripts/pre-commit` invokes `markdownlint-cli2` on staged `*.md`. |
| Portability lint | `scripts/pre-commit` invokes `scripts/portability_lint.py` on staged paths under `src/circuitsmith/`. |
| Pytest | **Not** in the pre-commit hook — pytest is too slow for the per-commit budget. Run it manually before pushing. |
| Security review | `pre-merge-commit`, `post-merge`, `pre-rebase` hooks scan pulls/merges/rebases. Reports land at `.claude/security-review-latest.md`. |

The hook is the local insurance policy: if it's installed and green,
CI will be green for the same change. If the hook is bypassed
(`CS_COMMIT_BYPASS`) or skipped (`CS_SKIP_SECURITY_REVIEW`), CI is the
backstop.

## Gating policy

All CI steps in `ci.yml` are **blocking**. A red build prevents merge
once branch protection on `main` is enabled
([`BRANCH_PROTECTION_CONCEPT.md`](BRANCH_PROTECTION_CONCEPT.md);
see [TASK-072](tasks/open/task-072-author-branch-protection-doc.md) and
[TASK-073](tasks/open/task-073-apply-branch-protection.md)). There is
no "advisory" tier today — every job is on the required-status-checks
list.

The required-status-checks list for branch protection mirrors the job
names produced by `ci.yml`:

- `Test (ubuntu-latest)`
- `Test (windows-latest)`

Both must be green before a PR can merge to `main`.

## Red build — response

1. **Read the failing step.** Open the Actions tab; the failed step
   is named in the run summary.
2. **Reproduce locally** with the same command. CI commands are
   intentionally short so you can copy-paste them:
   - Markdown lint: `markdownlint-cli2 "**/*.md" "#node_modules" "#.claude/security-review-latest.md"`
   - Portability lint: `python scripts/portability_lint.py src/circuitsmith`
   - Pytest: `pytest`
3. **Fix and re-push.** No need to rerun the workflow by hand — a new
   push re-triggers it.
4. **Escalate** when the failure looks harness-side: pip/npm registry
   500s, a setup-python action regression, a Windows-runner glitch
   that does not reproduce locally on either OS. In those cases the
   first move is a fresh push (cheap re-run); the second is to open
   an issue in `.github/workflows/` rather than chase the code.

## Known gaps

The senior-review pre-implementation audit flagged that
[`ruff`](https://docs.astral.sh/ruff/) is configured and enforced in
the local pre-commit hook but **not yet** running as a CI step. The
gap is intentional in the current pre-implementation phase (no
substantive Python source tree yet), and will be closed as soon as
EPIC-001 landed real Python (now relocated to `src/circuitsmith/`
under [ADR-0012](adr/0012-library-as-installable-package.md) and
EPIC-010) — adding a `ruff check .` step to `ci.yml` is a one-line
change.

### `release.yml` — `Release`

Triggered on every git tag matching `v*` (and on `workflow_dispatch`).
Three jobs in series: `build` → `publish` → `github-release`.

| Field | Value |
|---|---|
| File | [`.github/workflows/release.yml`](../../.github/workflows/release.yml) |
| Trigger | tag push (`v*`), `workflow_dispatch` |
| Runner | `ubuntu-latest` |
| Python | 3.11 |
| Permissions | `contents: write` (GitHub Release), `id-token: write` (PyPI trusted publishing) |

Job summary:

| Job | What it does | Red means |
|---|---|---|
| `build` | `python -m build` produces wheel + sdist under `dist/`. Verifies the wheel installs into a fresh venv and `import circuitsmith` succeeds. Uploads `dist/*` as a build artefact. | Packaging regression — the wheel cannot be built or installed cleanly. Reproduce locally with `python -m build && pip install dist/circuitsmith-*.whl`. |
| `publish` | `pypa/gh-action-pypi-publish@release/v1` uploads the artefacts to PyPI via [trusted publishing](https://docs.pypi.org/trusted-publishers/). No long-lived token in the repo. | Trusted-publishing trust relationship broken, or the version was already published (PyPI does not permit file-name reuse). |
| `github-release` | Slices the matching `## [vX.Y.Z]` block out of `CHANGELOG.md`, creates a GitHub Release on the tag with `dist/*` attached and that block as the body. | CHANGELOG section missing for the tag (falls back to a one-line note), or GitHub API issue. |

The agent-facing driver for the bump-CHANGELOG-tag-push flow that
*triggers* this workflow is the [`/release`](../../.claude/skills/release/SKILL.md)
skill. Procedural details — when to cut, semver policy, version
lockstep, the manual click-throughs PyPI requires — live in
[`RELEASING.md`](../../RELEASING.md).

## Future workflows

Placeholders for workflows that do not yet exist; documented here so
they are not invented twice.

- **Docs site** — if [IDEA-022 (MkDocs)](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-022-mkdocs-documentation-site.md)
  is adopted, a Pages-deploy workflow joins the matrix.

Stays unimplemented until it is needed; this doc updates when it
lands.
