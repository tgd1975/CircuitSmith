---
id: TASK-046
title: Add pyproject.toml and requirements-dev.txt
status: closed
closed: 2026-05-12
opened: 2026-05-12
effort: Small (<2h)
effort_actual: XS (<30m)
complexity: Junior
human-in-loop: No
epic: project-bootstrap
order: 1
---

## Description

Add machine-readable Python project configuration so dependencies are not
declared in prose. Two files land:

1. `pyproject.toml` — project metadata (name, version, Python version
   requirement), the runtime dependency set the skill needs
   (`schemdraw`, `matplotlib`, `jsonschema`, `ruamel.yaml>=0.17`), and a
   `[project.optional-dependencies]` table with a `dev` extra for test
   tooling (`pytest`, `pytest-cov` if desired).
2. `requirements-dev.txt` — pinned set for the dev extra, generated from
   `pyproject.toml` for direct `pip install -r` use without a build step.

The runtime deps come straight from
`docs/developers/ideas/archived/idea-001.skill-packaging.md` §Dependencies.
The version requirement on `ruamel.yaml` is load-bearing (insertion-order
preservation) and must be carried through.

## Acceptance Criteria

- [ ] `pyproject.toml` exists at repo root with `[project]` table and dependencies.
- [ ] `requires-python = ">=3.11"` — modern enough to assume the type-hint
      syntax used throughout (`list[...]`, `dict[...]`, `X | None`) without
      `from __future__ import annotations`, available on both Windows 11 and
      Ubuntu without backports.
- [ ] `ruamel.yaml` constraint is `>=0.17` to match the skill-packaging contract.
- [ ] `requirements-dev.txt` installs the test toolchain cleanly into a fresh venv.
- [ ] `pip install -e .` from the repo root succeeds and the runtime deps resolve.

## Test Plan

In a throwaway venv: `pip install -e .` then `pip install -r requirements-dev.txt`; verify both succeed and that `python -c "import schemdraw, jsonschema, ruamel.yaml"` works.

## Notes

Do not adopt a build backend with surprise behaviour (poetry, hatchling, etc.) unless there is a concrete reason. Plain `setuptools` is the right default — the project is a directory of scripts, not a wheel.
