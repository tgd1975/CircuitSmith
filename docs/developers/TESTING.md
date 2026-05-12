# Testing

How CircuitSmith's tests are organised, what each layer is for, and
how to add a new one.

## Test layers

CircuitSmith uses three conceptual test layers, each with a distinct
scope and failure signal:

| Layer | Scope | Failure means |
|---|---|---|
| **Unit** | Pure helpers — no I/O, no fixtures. NetGraph construction, schema-predicate functions, ERC check predicates against synthetic inputs. | A helper's contract is wrong. Fast (<1s); runs on every push. |
| **Integration** | The pipeline end-to-end against committed `.circuit.yml` fixtures: schema → NetGraph → ERC → renderer. | A stage's contract with adjacent stages is broken. |
| **Contract / golden** | Boundary-import contract ([TASK-050](tasks/open/task-050-boundary-import-contract-test.md)), NetGraph golden-hash ([TASK-053](tasks/open/task-053-netgraph-golden-hash-contract-test.md)), schema-validation pre-commit self-tests ([TASK-052](tasks/open/task-052-schema-validation-pre-commit.md)), portability lint. | A cross-cutting invariant the codebase makes a commitment to. |

Layer is a **concept**, not a directory enforcement: tests can live
flat under `tests/test_*.py` while the suite is small (current state
plus first-wave tasks like `tests/test_netgraph.py`,
`tests/test_erc_engine.py`), and split into
`tests/unit/`, `tests/integration/`, `tests/contract/`
subdirectories once the file count makes flat browsing painful. The
acceptance gate is the same either way: the test file is collected by
`pytest` and asserts the right thing.

A second test root, `scripts/tests/`, exists for **task-system tooling
tests** (housekeep, code-owner hook, portability lint, etc.). These
are not product-code tests and do not move when the
[`.claude/skills/circuit/`](../../.claude/skills/circuit/) skill is
extracted into a standalone repo at Phase 7
([EPIC-006](tasks/open/epic-006-circuit-skill-packaging.md)).

## `pyproject.toml` configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "scripts/tests"]
```

Two test roots, one configuration. `pytest` from the repo root picks
up both. Missing directories are silently skipped — `tests/` does not
yet exist at concept stage; the first product-code test (TASK-005,
TASK-008 et al.) creates it.

## Framework choice — pytest

Pytest is the framework for **new** tests, written as plain functions
with parametrize and fixtures.

```python
# tests/unit/test_netgraph.py
import pytest
from circuit.netgraph import NetGraph

def test_minimal_construction():
    g = NetGraph()
    assert g.nets() == []

@pytest.mark.parametrize("form", ["pins", "path", "bus"])
def test_connection_forms_produce_equivalent_nets(form):
    ...
```

### Coexistence with existing `unittest.TestCase` files

`scripts/tests/` predates this decision and uses `unittest.TestCase`.
Pytest collects `TestCase` subclasses natively, so those files
**coexist as-is** — no rewrite. New tests under `scripts/tests/` may
be written either way; new tests under `tests/` are pytest-functions
only.

## Fixture layout

Fixtures live next to the layer they support, never at repo root:

- **Pipeline integration fixtures** — `tests/fixtures/*.circuit.yml`.
  Committed `.circuit.yml` source files, parametrize-loaded by the
  integration tests. A new fixture is one file; no Python wiring
  needed beyond the `pytest.fixture` loader.
- **Golden artefacts** — `tests/fixtures/*.json` (or `.txt`, per the
  contract). Generated artefacts captured under version control; the
  test re-renders and compares.
- **Unit-test fixtures** — inline in the test file as small Python
  literals. Don't reach for a fixture file for three lines of data.

Shared fixtures across layers go in a `conftest.py` at the lowest
common ancestor — typically `tests/conftest.py`.

## Writing a new test

### Pure-unit example

```python
# tests/test_schema_predicates.py
from circuit.schema import is_known_component

def test_known_component_recognised():
    assert is_known_component("esp32")

def test_unknown_component_rejected():
    assert not is_known_component("totally-fake-mcu")
```

Run with `pytest tests/test_schema_predicates.py`.

### Pipeline-integration example

```python
# tests/test_full_pipeline.py
from pathlib import Path
import pytest
from circuit.pipeline import run

FIXTURE_DIR = Path(__file__).parent / "fixtures"

@pytest.mark.parametrize("yaml_path", sorted(FIXTURE_DIR.glob("*.circuit.yml")))
def test_fixture_renders_without_errors(yaml_path):
    result = run(yaml_path)
    assert result.erc_report.errors == []
    assert result.svg is not None
```

Drop a new `.circuit.yml` in `tests/fixtures/` (or `tests/integration/fixtures/`
once the directory split lands) and it is picked up automatically.

### Updating a golden hash

When a NetGraph algorithmic change legitimately shifts the golden
hash (TASK-053):

1. Run the test, observe the new hash in the assertion failure.
2. Convince yourself the new hash is correct (the diff is an
   intentional behavioural change, not an accidental one).
3. Update `tests/fixtures/netgraph_golden.json` (the path the
   TASK-053 plan settles on) with the new value. Commit the update
   **in the same commit** as the algorithmic change so reviewers can
   correlate cause and effect.

Never update the golden file without re-reading the assertion
context — that is how regressions land.

## Coverage tracking

Coverage tooling (`pytest-cov`) is **deferred**. Rationale:

- At concept stage there is no product code to measure; coverage of
  scaffolding scripts is not informative.
- A premature coverage gate forces contributors to write low-value
  tests to clear a threshold, which trains the wrong habit.

Coverage will be revisited when the renderer pipeline lands
(EPIC-002) and we have enough surface to measure meaningfully.
That decision will be a separate task with its own ADR.

## Running the tests

```bash
pytest                            # whole suite
pytest tests/                     # one root
pytest tests/test_foo.py          # one file
pytest tests/test_foo.py::test_bar  # one test
pytest -k "schema"                # name match across the suite
pytest -x                         # stop on first failure
```

The CI workflow at [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
runs the equivalent of `pytest` on every push and PR.

## When tests fail in CI but not locally

The usual suspects, in order of likelihood:

1. **Different Python version.** Local is 3.11, CI tests on 3.11/3.12/3.13.
   Reproduce locally with `pyenv` or `tox`.
2. **Path assumptions.** A test wrote `tests/fixtures/foo.yml` (relative
   path) but CI runs from a different cwd. Use `Path(__file__).parent`
   instead of relative strings.
3. **Stale virtualenv.** Local `.venv` has a dep that requirements-dev.txt
   no longer pins. Recreate the venv.
4. **Golden artefact drift.** Platform-specific line endings or
   floating-point rounding can shift hashes. Pin the inputs explicitly;
   never rely on system locale.
