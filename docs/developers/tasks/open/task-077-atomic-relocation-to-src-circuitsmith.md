---
id: TASK-077
title: Atomic relocation of circuit package to src/circuitsmith/
status: open
opened: 2026-05-13
effort: Large (8-24h)
complexity: Medium
human-in-loop: No
epic: circuitsmith-package
order: 2
prerequisites: [TASK-076]
---

## Description

Phase 2 of EPIC-010. One branch commit that moves the Python
library from `.claude/skills/circuit/` to `src/circuitsmith/`
and renames the importable package from `circuit` to
`circuitsmith`. Splitting this across multiple commits would
leave intermediate states where the pre-commit hook points at a
moved path; doing it atomically avoids that.

The work is mechanical — every step has an exact target listed
in the idea body's § "Phase 2 — Atomic relocation". Summary:

- **Tree move** (`git mv` to preserve blame):
  `.claude/skills/circuit/{netgraph.py, renderer.py, components/, schema/}`
  → `src/circuitsmith/{...}`; `layout_engine/` → `layout/`
  (directory rename — `_engine` suffix made sense inside a skill
  folder, not as a top-level package surface).
- **Package skeleton**: create `src/circuitsmith/__init__.py`
  (with `__version__`), `src/circuitsmith/render/__init__.py`,
  `src/circuitsmith/export/__init__.py` (latter two are empty
  placeholders for EPIC-002 reshuffle and BOM/netlist epics).
- **Import rewrites** across `src/**/*.py` and `tests/**/*.py`:
  `from circuit.layout_engine.` → `from circuitsmith.layout.`,
  `from circuit.netgraph` → `from circuitsmith.netgraph`, etc.
  Order matters (longer prefixes first to avoid partial matches).
- **Docstring path references** updated in `schema/registry.py`,
  `schema/validator.py`, `schema/__init__.py`, `netgraph.py`
  (ADR-0007 reference → ADR-0012), `layout_engine/__init__.py`.
- **`pyproject.toml` flip**: remove `py-modules = []`; add
  `[tool.setuptools.packages.find] where = ["src"]` and
  `[tool.setuptools.package-data] "circuitsmith.schema" = ["*.json"]`.
- **`tests/conftest.py` delete**: the `sys.path` splice is
  obsolete under `pip install -e .` editable install.
- **Portability lint retarget**: edit
  `scripts/portability_lint.py` to scan `src/circuitsmith/`
  instead of `.claude/skills/circuit/`. Rule set unchanged.
- **Pre-commit hook retarget**: edit `scripts/pre-commit:159`
  pattern `^\.claude/skills/circuit/` → `^src/circuitsmith/`.
  Update the comments at lines 15 and 155.
- **`scripts/generate-schematic.py`** — either replace the
  dynamic-import-by-path with `from circuitsmith.components import mcus`
  or delete the script (it is a predecessor-repo artefact per
  CLAUDE.md). Decision goes in the branch commit message.

## Acceptance Criteria

- [ ] `git ls-files src/circuitsmith/` lists all the relocated
      modules; blame survives (`git log --follow` traces back
      through the rename).
- [ ] `pip install -e .[dev]` succeeds in a clean venv.
- [ ] `pytest` is green.
- [ ] `python scripts/portability_lint.py` is green and scans
      `src/circuitsmith/`.
- [ ] `python -m build` produces a wheel containing
      `circuitsmith/schema/*.json`.
- [ ] `rg -n "from circuit\." -t py` and `rg -n "^import circuit$" -t py`
      both return zero hits across `src/` and `tests/`. Matches
      in `docs/developers/ideas/archived/` and ADR-0007's
      `## Supersession` link are expected and fine.
- [ ] `rg -n "\.claude/skills/circuit/" -t py` returns zero hits.
- [ ] A no-op edit inside `src/circuitsmith/` triggers the
      pre-commit hook against the new path (not the old).

## Test Plan

Full `pytest` run + `python scripts/portability_lint.py` +
`python -m build` wheel inspection. The package's existing test
suite already covers the renamed modules; success is "everything
imports and passes after the rename".

## Prerequisites

- **TASK-076** — ADR-0012 must be on paper before the code
  reorganisation it justifies lands. ADR-0007's invariant
  comment (`No host-project imports (ADR-0007 portability)`)
  becomes ADR-0012 as part of the docstring rewrite step.

## Sizing rationale

Intentionally Large — the idea's § "Phase 2" mandates one
atomic commit so the pre-commit hook never points at a moved
path. A refactor that breaks the build mid-way through a
multi-commit sequence is exactly the case the
[ts-task-new](../../../../.claude/skills/ts-task-new/SKILL.md)
sizing-rationale section is designed for.

## Notes

The full Phase 2 checklist with file:line references lives in
[`docs/developers/ideas/archived/idea-002-consolidate-skill-python-into-central-module.md`](../../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md)
§ "Phase 2 — Atomic relocation". Phase 0 (branch creation,
baseline capture, inventory of the rewrite surface) is the
natural prep that `/ts-task-active` triggers when this task
activates; Phase 5 verification gates ride with this task's
acceptance criteria.
