---
subsystem: ci-gates
covers: scripts/check_*.py, scripts/pre-commit, .github/workflows/ci.yml
---

# CI gates — test plan

The "gates" are the checks that block a commit or a PR: the pre-commit
hook chain ([`scripts/pre-commit`](../../../scripts/pre-commit)) and the
CI workflow ([`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml)).
Most gates are thin scripts under `scripts/`; this chapter catalogues
each gate's **failure mode** and **bypass**, then maps the tests that
keep the gate scripts themselves honest.

Covers `scripts/check_*.py`, `scripts/pre-commit`, the security-review
hooks under `scripts/git-hooks/`, and `ci.yml`.

Test files covering this subsystem:

```pytest
tests/test_module_boundaries.py
tests/test_schema_pre_commit.py
tests/test_precommit_hook.py
tests/test_renderer_staleness.py
tests/test_check_gallery_regression.py
scripts/tests/test_check_erc_reports.py
scripts/tests/test_phase2b_trigger.py
scripts/tests/test_release_phase2b_gate.py
scripts/tests/test_portability_lint.py
scripts/tests/test_version_lockstep.py
scripts/tests/test_security_review_personal_data.py
```

## Inputs and outputs

- **Input** — the staged change (pre-commit) or the pushed ref (CI).
- **Output** — a pass (exit 0) or a fail with an actionable message.
  Pre-commit gates fire only when the relevant file class is staged; CI
  gates run on every push/PR (Ubuntu golden-checks; Windows runs the
  OS-agnostic subset).

## Gate catalogue

What each gate looks like when it fires, and how to clear it.

| Gate | Fires when | Failure looks like | Fix / bypass |
|---|---|---|---|
| `/commit` provenance | every commit | "commit did not flow through /commit" | use `/commit`; bypass `CS_COMMIT_BYPASS="<reason>"` |
| Markdown lint | `*.md` staged / all CI | `markdownlint-cli2` rule violations | fix the Markdown; whole-hook bypass `--no-verify` |
| Ruff | `*.py` staged / CI | `ruff check` errors on staged files | fix the lint; whole-hook bypass `--no-verify` |
| `.circuit.yml` schema | `*.circuit.yml` staged / CI | `schema`/`S4`/`S5` finding | fix the YAML; no targeted bypass |
| Circuit-artefact regen | `data/*.circuit.yml` or `components/*.py` staged | "regeneration failed" or updated artefacts staged | let it regenerate + re-commit; bypass `CS_COMMIT_BYPASS` |
| ERC report staleness + ERROR | ERC inputs staged / CI | "erc-report.md is stale" or "ERC error [E…]" | re-render report + re-commit, or fix the error |
| Exporter staleness | export inputs staged / CI | "exporter artefacts … stale" | re-run exporters + re-commit |
| Catalog validation | `knowledge/` staged / CI | format / `enforced_by` / disclaimer / category-lint error | fix `rules.json`; offline via `CS_CATALOG_OFFLINE=1` |
| Portability lint | `src/circuitsmith/` staged / CI | host-project token leak in the package | remove the leak; **no bypass** (load-bearing per ADR-0012) |
| Gallery regression | CI | "FAIL `<circuit>`: `<diff>`" | fix, or `check_gallery_regression.py --rebaseline` + re-commit |
| NetGraph golden | CI (pytest) | serialiser drift / stale golden | investigate drift, or `update_netgraph_golden.py --bump-schema-version` |
| Version lockstep | CI (pytest) | `__version__` ≠ `pyproject` version | sync both (via `/release`) |
| Phase 2b trigger | release time | escalations present in committed `meta.yml` | review; bypass `CS_PHASE2B_BYPASS` |
| Module-boundary contract | CI (pytest) | a forbidden cross-module import | remove the import |
| Security review | pull / merge / rebase | flagged incoming change or personal-data leak | review report; bypass `CS_SKIP_SECURITY_REVIEW=1` |

## Unit tests

The gate scripts have their own tests, each constructing a temp tree and
asserting the gate's pass/fail behaviour:

- `tests/test_module_boundaries.py` (TASK-050) — the boundary contract
  plus a self-test (`bom_exporter_violator.py` fixture) proving the
  checker catches a real violation.
- `tests/test_schema_pre_commit.py` (TASK-052) — `check_circuit_schema.py`
  passes clean and fails on a planted bad circuit.
- `scripts/tests/test_check_erc_reports.py` (TASK-029),
  `test_phase2b_trigger.py` (TASK-058),
  `test_release_phase2b_gate.py` (TASK-059, with `CS_PHASE2B_BYPASS`),
  `test_portability_lint.py` (TASK-051),
  `test_version_lockstep.py`, and
  `test_security_review_personal_data.py` (TASK-074) — each pins its
  gate's clean-pass and planted-fail paths.

## Integration tests

- `tests/test_precommit_hook.py` (TASK-038) exercises the
  circuit-artefact regenerator that the pre-commit hook drives.
- `tests/test_renderer_staleness.py` (TASK-015) and
  `tests/test_check_gallery_regression.py` (TASK-101) drive the
  re-render-and-diff staleness gates end-to-end (the latter now covers
  the ERC-date normalisation that keeps the gate deterministic).

## Golden / snapshot tests

The staleness gates *are* the golden mechanism for their artefacts (SVG,
BOM, netlist, ERC report) — see [`renderer.md`](renderer.md),
[`exporters.md`](exporters.md), [`erc-engine.md`](erc-engine.md). This
chapter tests that the *gates* behave; the goldens themselves live with
their subsystems.

## Property / fuzz tests

**None.** Gate scripts are tested with constructed pass/fail trees.

## Performance budget

The pre-commit hook's budget is the real constraint: **well under a
second per file** (per `COMMIT_POLICY.md`), which is why walking-every-
test gates (e.g. the TASK-091 test-plan staleness check) are CI-only,
not pre-commit. No single number is pinned beyond that policy.

## Known uncovered cases

- **The pre-commit hook script as a whole.** Individual gate *scripts*
  are tested, but `scripts/pre-commit`'s orchestration (which gate fires
  for which staged-file class, the provenance-token flow) is exercised
  only by real commits, not a dedicated harness. Rationale: it is shell
  glue best validated in use; a bats-style test is a possible follow-up.
- **CI workflow YAML.** `ci.yml` step wiring has no test; a broken step
  surfaces on the next push. Rationale: workflow testing needs a CI
  emulator — out of scope.
- **Security-review hook beyond personal-data.** Only the personal-data
  detector is unit-tested; the broader diff-scan is manual. Rationale:
  the high-risk path (contact-info leaks) is the one pinned.

## Cadence

| Test file | PR | Nightly | Release |
|---|:--:|:--:|:--:|
| `tests/test_module_boundaries.py` | ✓ | | |
| `tests/test_schema_pre_commit.py` | ✓ | | |
| `tests/test_precommit_hook.py` | ✓ | | |
| `tests/test_renderer_staleness.py` | ✓ | | |
| `tests/test_check_gallery_regression.py` | ✓ | | |
| `scripts/tests/test_check_erc_reports.py` | ✓ | | |
| `scripts/tests/test_phase2b_trigger.py` | ✓ | | |
| `scripts/tests/test_release_phase2b_gate.py` | ✓ | | |
| `scripts/tests/test_portability_lint.py` | ✓ | | |
| `scripts/tests/test_version_lockstep.py` | ✓ | | |
| `scripts/tests/test_security_review_personal_data.py` | ✓ | | |

All run at PR-time. The Phase 2b trigger and version-lockstep gates are
*also* release-time concerns (the release flow re-checks them), but their
tests run per-PR. The catalog's online URL check is the one designated
nightly gate that has no workflow yet (see [`schema.md`](schema.md)).
