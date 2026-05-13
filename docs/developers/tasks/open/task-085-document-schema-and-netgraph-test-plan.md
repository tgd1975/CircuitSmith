---
id: TASK-085
title: Author the schema and netgraph subsystem test plans
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Medium
human-in-loop: Clarification
epic: test-plan-and-coverage
order: 3
prerequisites: [TASK-084]
---

## Description

Fill in two of the empty chapter files created in TASK-083:

- `docs/developers/testing/schema.md` — covers
  `src/circuitsmith/schema/*.json` validation, the
  schema-validation pre-commit hook (TASK-052), and the
  catalog-validation script (TASK-025).
- `docs/developers/testing/netgraph.md` — covers
  `src/circuitsmith/netgraph.py`, the NetGraph golden-hash CI
  contract test (TASK-053), and any serialiser-determinism tests.

Each chapter must follow the structure declared in IDEA-003:

1. **Inputs / outputs** the tests pin down.
2. **Unit tests** — pure functions, edge cases, error paths.
3. **Integration tests** — subsystem plus its immediate neighbours
   (schema with netgraph; netgraph with the layout kernel's input
   adapter).
4. **Golden / snapshot tests** — for netgraph, the canonical
   `.circuit.yml ↔ NetGraph(hash)` pairs.
5. **Property / fuzz tests** — where the input space is large.
6. **Performance budget** — only if one exists (likely not for these
   two; note "no budget" explicitly rather than omitting the heading).
7. **Known uncovered cases** with rationale.
8. **PR-time vs nightly vs release** axis.

The chapters reference test files by path; they do not duplicate test
code or assertions. Each "known uncovered" item must include a
sentence on *why* it is uncovered (cost, infrastructure, deferred to
a later epic) — silent gaps are the failure mode this whole epic
exists to prevent.

## Acceptance Criteria

- [ ] `schema.md` and `netgraph.md` are no longer empty placeholders.
- [ ] Both files cover every section in the structure above (with
      "no budget" / "no fuzz tests" notes where applicable, never
      omitted headings).
- [ ] Every test referenced exists in the inventory from TASK-084.
- [ ] Each "known uncovered" item has a one-sentence rationale.

## Test Plan

No automated tests required — change is non-functional (documentation).

Manual verification:

1. Cross-check every test-file path in the two chapters against the
   inventory; flag mismatches.
2. `markdownlint-cli2` passes on the new files.

## Prerequisites

- **TASK-084** — the inventory is the raw material for these chapters.

## Notes

- These two subsystems are paired because they sit at the start of
  the pipeline and their test surfaces overlap (the netgraph builder
  consumes schema-validated input). Splitting them across two tasks
  would force one to forward-reference the other.
- The catalog-validation script (TASK-025) is technically separate
  from schema validation, but is folded into `schema.md` because the
  catalog *is* a schema-validated artefact — anyone reading
  `schema.md` to understand schema testing will expect to find it
  there.
