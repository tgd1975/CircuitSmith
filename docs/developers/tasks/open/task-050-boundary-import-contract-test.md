---
id: TASK-050
title: Boundary-import contract test for circuit-skill modules
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: architecture-fitness-functions
order: 5
prerequisites: [TASK-008, TASK-012, TASK-031, TASK-033]
---

## Description

Promote the decoupling claims in
[idea-001-circuit-skill.md §Architecture](../../ideas/archived/idea-001-circuit-skill.md#architecture)
from prose to machine-checked invariants. The dossier names three
forbidden edges explicitly:

- `bom_exporter` walks `components` directly and **never touches `NetGraph`**.
- `netlist_exporter` walks `NetGraph` and **never reads component internals**.
- `renderer` does not directly import `layout_engine.ai_placer` — it
  consumes pre-committed `layout.yml` via `layout.py`, keeping the AI
  containment property of the architecture intact.

This test catches the drift case: a refactor that "just" imports the
adjacent module because it's convenient. The decoupling is part of why
extraction (Phase 7) and AI containment (Phase 2b) work; a silent
violation undermines both.

Implementation: AST-walk each module under `src/circuitsmith/`,
collect its import set, and assert the disallowed-edge table. AST
walking (rather than runtime import) avoids ordering dependencies on
the rest of the package being importable in test scope.

**Scope note (2026-05-13).** Under
[ADR-0012](../../adr/0012-library-as-installable-package.md), the
library code moved from `.claude/skills/circuit/` to
`src/circuitsmith/` (EPIC-010 / TASK-077). The boundary this test
guards therefore shifts with it — the contract itself is unchanged.

## Acceptance Criteria

- [ ] `tests/test_module_boundaries.py` exists and is picked up by pytest.
- [ ] Asserts: `bom_exporter` does not import (directly or transitively at the source level) anything named `netgraph`.
- [ ] Asserts: `netlist_exporter` does not import any module from `src/circuitsmith/components/` (i.e. no `from circuitsmith.components.*` imports).
- [ ] Asserts: `renderer` does not import `layout_engine.ai_placer`.
- [ ] Test fails with a structured diagnostic that names the offending file, the forbidden import, and the dossier section that defines the rule.
- [ ] Self-test: a deliberately-violating fixture module in `tests/fixtures/` confirms the test catches a violation (mutation-test the rule, not just the happy path).

## Test Plan

For each forbidden edge: load the target module's AST, assert the
forbidden module name is not in the union of `ast.Import` /
`ast.ImportFrom` targets. Self-test fixture: a `bad_bom_exporter.py`
that imports `netgraph` and is fed to the same checker — must fail.

## Prerequisites

- **TASK-008** — `netgraph.py` must exist so its name resolves.
- **TASK-012** — `renderer.py` must exist.
- **TASK-031** — `bom_exporter.py` must exist.
- **TASK-033** — `netlist_exporter.py` must exist.

## Notes

This is item 1 of the architecture-review recommendations
([EPIC-008](epic-008-architecture-fitness-functions.md) summary).
Pairs with TASK-055/TASK-056 (code-owner skills): the skill nudges
*during* the edit; this test fails *after* the edit if the nudge was
ignored. Two layers of the same enforcement.
