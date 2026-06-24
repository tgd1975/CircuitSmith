# Testing

How to write and run CircuitSmith's tests. **The canonical coverage plan —
what is tested, per subsystem, and where the gaps are — lives in
[`testing/`](testing/README.md); this doc is the practical how-to.**

## Test layers

Three conceptual layers, each with a distinct scope and failure signal. The
[coverage matrix](testing/README.md) maps every test file to a subsystem and
a layer:

| Layer | Scope | Failure means |
|---|---|---|
| **Unit** | Pure helpers — no I/O, no fixtures. NetGraph construction, schema predicates, ERC check predicates against synthetic inputs. | A helper's contract is wrong. Fast (<1s); runs on every push. |
| **Integration** | The pipeline end-to-end against committed `.circuit.yml` fixtures: schema → NetGraph → ERC → renderer. | A stage's contract with an adjacent stage is broken. |
| **Contract / golden** | Boundary-import contract, NetGraph golden-hash, schema-validation self-tests, portability lint. | A cross-cutting invariant the codebase commits to. |

Layer is a *concept*, not a directory: tests live flat under
`tests/test_*.py` while the suite is small, and split into `tests/unit/`,
`tests/integration/`, `tests/contract/` once flat browsing gets painful. The
acceptance gate is the same either way — `pytest` collects the file and it
asserts the right thing.

## Two test roots

| Root | Holds | Ships to PyPI? |
|---|---|---|
| `tests/` | Product-code tests for the [`circuitsmith`](../../src/circuitsmith/) package. | Yes — with the library. |
| `scripts/tests/` | Task-system tooling tests (housekeep, code-owner hook, portability lint). | No — repo-local. |

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "scripts/tests"]
```

`pytest` from the repo root picks up both; missing directories are silently
skipped.

## Writing a new test

Pytest is the framework — plain functions with `parametrize` and fixtures.
Rather than reproduce drift-prone snippets here, read the tests themselves as
templates: the [coverage matrix](testing/README.md) names the covering test
file for each subsystem and layer. Imports follow the package's public API —
`from circuitsmith.netgraph import NetGraph`,
`from circuitsmith.renderer import render`, and so on.

Fixtures live next to the layer they support:

- **Integration fixtures** — `tests/fixtures/*.circuit.yml`, parametrize-loaded.
- **Golden artefacts** — committed under `tests/fixtures/`; the test
  re-renders and compares.
- **Unit-test data** — inline literals; don't reach for a file for three
  lines of data.

Shared fixtures go in a `conftest.py` at the lowest common ancestor.

### Updating a golden hash

When an algorithmic change legitimately shifts a golden hash (e.g. the
NetGraph golden-hash contract):

1. Run the test; observe the new hash in the failure.
2. Convince yourself the new value is correct — an intentional behavioural
   change, not an accident.
3. Update the golden file **in the same commit** as the change, so reviewers
   can correlate cause and effect.

Never update a golden file without re-reading the assertion context — that is
how regressions land.

## Running the tests

```bash
pytest                              # whole suite
pytest tests/                       # one root
pytest tests/test_foo.py           # one file
pytest tests/test_foo.py::test_bar # one test
pytest -k "schema"                 # name match across the suite
pytest -x                          # stop on first failure
```

CI runs the equivalent on every push and PR — see
[`CI_PIPELINE.md`](CI_PIPELINE.md) and the
[`ci-gates`](testing/ci-gates.md) chapter for the full gate inventory.

## Coverage tracking

Coverage tooling (`pytest-cov`) is not yet a gate. A premature threshold
trains the wrong habit — writing low-value tests to clear a number. The
[coverage matrix](testing/README.md) tracks coverage by *subsystem and
intent* instead; a measured-coverage gate, if it is added, will be its own
task with an ADR.

## When tests fail in CI but not locally

The usual suspects, in order of likelihood:

1. **Different Python version.** CI runs a version matrix; reproduce locally
   with `pyenv` or `tox`.
2. **Path assumptions.** Use `Path(__file__).parent`, never relative strings
   that assume a working directory.
3. **Stale virtualenv.** Recreate `.venv` when `requirements-dev.txt` drifts.
4. **Golden artefact drift.** Platform line endings or float rounding shift
   hashes; pin inputs explicitly, never rely on system locale.
