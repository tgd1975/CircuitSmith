---
id: TASK-053
title: NetGraph golden-hash CI contract test
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Medium
human-in-loop: No
epic: architecture-fitness-functions
order: 7
prerequisites: [TASK-008, TASK-014]
---

## Description

[TASK-008](task-008-implement-netgraph-data-model.md) asserts hash
determinism in the small: two parses of the same input produce
structurally identical graphs. That test catches non-determinism inside
one process — it does not catch the case where the serialiser drifts
between releases (e.g. a new optional field starts being included in the
canonical hash, key ordering changes after a refactor, default values
shift).

This task adds the regression guard: freeze the canonical hash of the
`full-pedal` fixture's `NetGraph` as a golden value committed to the
repo, and fail CI if the hash changes without an accompanying schema
version bump in `circuit.schema.json`.

Mechanism:

- `tests/test_netgraph_golden.py` parses the `full-pedal` fixture's
  `.circuit.yml`, builds the `NetGraph`, computes its canonical hash,
  asserts equality with the stored constant.
- `tests/fixtures/golden_hashes.json` carries `{circuit_name: {hash,
  schema_version}}` entries.
- A schema-version mismatch produces a distinct diagnostic from a hash
  mismatch: "schema bumped, regenerate the golden" vs. "hash changed
  without a schema bump — your serialiser drifted."
- `pytest --update-golden` (or an equivalent CLI flag) regenerates the
  hashes; running it without bumping the schema version is itself an
  error.

## Acceptance Criteria

- [ ] `tests/test_netgraph_golden.py` exists and runs in CI.
- [ ] `tests/fixtures/golden_hashes.json` carries the captured hash and the schema version it was captured against.
- [ ] A deliberate hash change (test fixture: insert a stray newline in the serialiser) fails CI with the "serialiser drifted" diagnostic.
- [ ] A deliberate schema-version bump without regenerating the golden fails with the "regenerate the golden" diagnostic.
- [ ] `--update-golden` CLI flag regenerates the file when a corresponding schema version bump is in the same commit.

## Test Plan

Three positive paths (clean run, schema bump + regen, no-change),
two negative paths (drift without bump; bump without regen). Use a
small mock `NetGraph` instance for the drift fixture so the test does
not depend on the full renderer pipeline.

## Prerequisites

- **TASK-008** — the `NetGraph` whose hash is being golden-tested.
- **TASK-014** — the `full-pedal` fixture's `.circuit.yml` is the corpus.

## Notes

This catches the silent-drift class of bug that is otherwise discovered
only when ERC, layout, or netlist export start producing
different-but-not-obviously-wrong output. The dossier names `NetGraph`
as the shared contract for three subsystems
([idea-001.erc-engine §Net graph data model](../../ideas/archived/idea-001.erc-engine.md));
a contract test at that seam is the right insurance.
