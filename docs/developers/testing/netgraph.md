---
subsystem: netgraph
covers: src/circuitsmith/netgraph.py
---

# NetGraph — test plan

[`netgraph.py`](../../../src/circuitsmith/netgraph.py) is the shared
contract (ADR-0003): it turns a schema-valid `.circuit.yml` dict into a
deterministic graph of nets and pins that every downstream stage
(layout, ERC, exporters) reads. Its tests therefore pin two things hard:
the **public API shape** and **determinism** — because a silent change
to either breaks every consumer at once.

Test files covering this subsystem:

```pytest
tests/test_netgraph.py
tests/test_netgraph_golden.py
tests/netgraph/test_sub_block_flattener.py
```

## Inputs and outputs

- **Input** — a circuit dict (`meta` / `components` / `connections`,
  optionally `sub-blocks` / `instances`), normally schema-validated
  first. `NetGraph.from_yaml_dict` transparently calls
  `flatten_sub_blocks` so consumers never see un-flattened input.
- **Output** — the documented API: `nets`, `net_meta`, `pin_index`,
  `pins_on_net`, `nets_containing_pin`, `flattened_segments`,
  `components_between`, and `canonical_hash`. `PinRef(ref, pin)` is the
  value type threaded through all of them.

## Unit tests

`tests/test_netgraph.py` (TASK-008) is the workhorse, grouped by the
four acceptance areas:

- **API surface** — `test_api_surface_is_present` asserts every
  documented attribute/method exists (a cheap guard against an
  accidental rename breaking consumers silently).
- **Connection-form semantics** — the three forms (`pins`, `path`,
  `bus`) each get membership tests. `path:` is the richest: segment
  naming (first segment keeps the declared net name, the rest are
  content-addressed `<net>__<a>__<b>`), `flattened_segments` ordering,
  merge of a path endpoint into a named net (`…__D1_K__GND` folds into
  `GND`), and the `ValueError` raised when `flattened_segments` /
  `components_between` are called on a non-path net.
- **`net_meta`** — carries `pull` and `bus_backbone_count`.
- **`pin_index`** — lookup by `PinRef`, a pin appearing on multiple
  nets (path-end merge), and the empty result for an unknown pin.

The sub-block flattener (`tests/netgraph/test_sub_block_flattener.py`,
TASK-116) is unit-tested independently of NetGraph: refdes minting
(`<local>_<instance>`, e.g. `R_FILT_A`), top-level connection rewrites
(`FILT_A.signal_in` → `R_FILT_A.1`), internal-net prefixing
(`FILT_A__filtered`), BOM-ordering adjacency, and the three error paths
(`SubBlockFlattenError` on empty sub-block, undeclared port, undeclared
sub-block reference).

## Integration tests

NetGraph's integration with its neighbours is covered from both sides
rather than in this chapter's own files:

- **Schema → NetGraph** — the flattener round-trip
  (`test_netgraph_round_trips_through_flattener`) confirms
  `from_yaml_dict` produces the same constituent refs and internal nets
  as a direct `flatten_sub_blocks` call.
- **NetGraph → layout / ERC / exporters** — exercised by
  `tests/test_full_pedal_fixture.py` and the per-rule layout tests
  (see [`layout-kernel.md`](layout-kernel.md)) which build a NetGraph
  and assert on placement, and by [`exporters.md`](exporters.md) which
  walks the graph.

## Golden / snapshot tests

`tests/test_netgraph_golden.py` (TASK-053) is the cross-release drift
guard. It freezes the `canonical_hash` of every shipped `.circuit.yml`
in `tests/fixtures/golden_hashes.json` and distinguishes two failure
modes with separate diagnostics:

- **Serialiser drift** — hash moved without the schema file changing.
  This is the bug the test exists to catch; the operator must
  investigate, *not* regenerate.
- **Stale golden** — the schema file changed (its sha256 is the
  `schema_version` source of truth) but the golden was not regenerated;
  fix is `python scripts/update_netgraph_golden.py --bump-schema-version`.

`test_drift_detection_mutation_guard` is a self-test: a deliberately
wrong hash must trip the comparison, so a broken assertion can never
make real drift pass silently.

## Property / fuzz tests

**None today.** Determinism is verified by *example*
(`test_canonical_hash_is_stable_across_parses`,
`test_canonical_hash_changes_with_topology`) and the three-form
equivalence by fixed fixtures, not by property-based generation over
randomised topologies. See *Known uncovered*.

## Performance budget

**No budget.** NetGraph construction is linear in connection count and
runs in well under the PR-time budget on every shipped circuit; there
is no pinned number because nothing has ever approached a concern.

## Known uncovered cases

- **Property-based form equivalence.** The `pins`/`path`/`bus`
  equivalence is asserted on hand-written fixtures, not generated
  topologies. Rationale: the canonical-hash golden already catches
  serialiser drift on real circuits, so randomised generation is
  lower-value than it looks; filed as a candidate, not a blocker.
- **Malformed-but-schema-valid input.** NetGraph assumes its input
  passed schema validation; it is not independently fuzzed with
  structurally-valid-but-semantically-broken dicts. Rationale: the
  schema layer (see [`schema.md`](schema.md)) owns that boundary, and
  the pipeline always validates before building the graph.
- **Deeply nested sub-blocks.** Only single-level instances are
  exercised; nested sub-blocks are rejected at the schema layer (no
  slash in a sub-block name), so the flattener is never asked to
  recurse. Documented here so the boundary is explicit.

## Cadence

| Test file | PR | Nightly | Release |
|---|:--:|:--:|:--:|
| `tests/test_netgraph.py` | ✓ | | |
| `tests/test_netgraph_golden.py` | ✓ | | |
| `tests/netgraph/test_sub_block_flattener.py` | ✓ | | |

All three run at PR-time via `pytest`. The golden test is *also* the
kind of check a nightly job would host if the suite ever grows a
nightly tier; today it is fast enough to stay at PR-time.
