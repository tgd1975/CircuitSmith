---
name: co-schema
description: Code-owner reminder for src/circuitsmith/schema/*.json — invariants surfaced before edit
---

# co-schema

Surfaces the invariants the JSON schemas in
`src/circuitsmith/schema/` are expected to preserve before an edit
lands. Bound by
[`.claude/codeowners.yaml`](../../codeowners.yaml).

Authoritative source:
[`docs/developers/ideas/archived/idea-001.yaml-format.md`](../../../docs/developers/ideas/archived/idea-001.yaml-format.md)
and
[`idea-001.layout-engine-concept.md §16`](../../../docs/developers/ideas/archived/idea-001.layout-engine-concept.md).

## Invariants (checklist, not prose)

- [ ] **Schema-version bump on any breaking change.** Removing a
      field, changing a type, tightening a constraint, or renaming a
      key is breaking. The top-level `schema_version` field bumps in
      the same commit, and downstream validators are updated to
      accept the new version (with or without back-compat for the
      previous, depending on the rollout plan).
- [ ] **`NetGraph` golden hash regenerated.** Any schema change
      that affects how `.circuit.yml` parses into `NetGraph` —
      effectively any field that flows through the graph — must
      regenerate the golden hash in the same commit (TASK-053).
      The CI contract test fails otherwise.
- [ ] **Downstream validators re-tested.** At minimum: the
      schema-validation pre-commit hook (TASK-052), the renderer,
      and the markdownlint regen step. Each consumes the schema or
      data derived from it; each must stay green.
- [ ] **Examples in `docs/` updated.** Any sample `.circuit.yml`
      shown in documentation must validate against the new schema.
      A schema change that lands but leaves the docs invalid is a
      revert candidate.
- [ ] **Portability contract holds.** Schema files contain no
      host-project paths or sibling-project references; the
      portability lint (TASK-051) catches accidents.

## Authority

[`idea-001.yaml-format.md`](../../../docs/developers/ideas/archived/idea-001.yaml-format.md) —
`.circuit.yml` format definition.
[`idea-001.layout-engine-concept.md §16`](../../../docs/developers/ideas/archived/idea-001.layout-engine-concept.md) —
`layout.yml` format definition.

## Downstream consumers

A breaking schema change ripples through:

- `src/circuitsmith/netgraph.py` — parses `.circuit.yml` into
  the graph (see [`co-netgraph`](../co-netgraph/SKILL.md)).
- `src/circuitsmith/renderer.py` — consumes `layout.yml`
  slot vocabulary.
- The schema-validation pre-commit hook (TASK-052) — refuses
  malformed inputs against the **current** schema; lagging it
  blocks every commit.
- The `NetGraph` golden-hash CI contract test (TASK-053).
- Any checked-in example `.circuit.yml` under `docs/`.
