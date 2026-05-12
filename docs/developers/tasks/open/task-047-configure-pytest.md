---
id: TASK-047
title: Configure pytest (testpaths, discovery, coverage thresholds)
status: open
opened: 2026-05-12
effort: XS (<30m)
complexity: Junior
human-in-loop: No
epic: project-bootstrap
order: 2
prerequisites: [TASK-046]
---

## Description

Add a `[tool.pytest.ini_options]` section to `pyproject.toml` (or a
sibling `pytest.ini`) so test runs do not depend on the user's CWD or
the existence of `conftest.py`. The existing tests under `scripts/tests/`
are unittest-style; pytest discovers them natively.

Minimum config:

- `testpaths = ["scripts/tests"]` — discovery anchored, no manual paths
- `python_files = "test_*.py"` — default but explicit
- `addopts = "-ra --strict-markers"` — short failure summary; refuse undeclared markers

Pre-existing test failures in `scripts/tests/test_housekeep.py` (3 fail,
1 error as of e75dc55) are out of scope here — this task only configures
the runner; fixing those failures belongs in a separate task in EPIC-007
or as a follow-up.

## Acceptance Criteria

- [ ] `pytest` invoked from repo root with no arguments discovers and runs every test under `scripts/tests/`.
- [ ] `pyproject.toml` (or `pytest.ini`) declares `testpaths`, `python_files`, and `addopts` as above.
- [ ] Running pytest with a misspelled marker (`@pytest.mark.slowww`) errors out due to `--strict-markers`.

## Test Plan

`pytest` from repo root; verify exit code and that the discovered test
count matches `find scripts/tests -name 'test_*.py' | xargs grep -c '^    def test_'` (sanity-check, not strict).

## Notes

If the team later wants coverage gates, add `pytest-cov` to `requirements-dev.txt` and a `--cov=scripts --cov-fail-under=N` to `addopts` — but not yet. A coverage gate without test stability is theatre.
