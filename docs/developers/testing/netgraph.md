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
tests/netgraph/test_form_equivalence_properties.py
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

`tests/netgraph/test_form_equivalence_properties.py` (TASK-135) closes
the form-equivalence-over-generated-topologies gap this chapter flagged.
It generates a chain topology — a Hypothesis-varied number of series
2-pin resistors between an MCU GPIO and the MCU ground pin — and expresses
the **same** connectivity two ways:

- the `pins` form (one connection per junction, each listing its two
  pins), versus
- the `path` form (a single `path:` listing the ordered chain).

The headline assertion is that both induce the same **canonical net
membership** — the set of pin-sets, independent of the net *names* the
author chose, which is exactly the contract downstream consumers depend on
(ADR-0003). A companion property covers `bus` vs `pins` over a generated
single multi-drop net (the backbone/tap split is Hypothesis-varied and
must not change membership). All run PR-time (`max_examples=40`,
`deadline=None`).

Two deliberate scoping decisions:

- **Paths terminate at a real pin, not a bare net-name node.** A bare
  net-name terminator emits an extra single-pin tail segment *and* a merge
  into the named net, which the plain `pins` form has no counterpart for —
  the two forms would then not be membership-equivalent by construction.
  Terminating at `U1.GNDL` makes the path's segments exactly the chain's
  junctions, one per `pins`-form net.
- **`canonical_hash()` equality is asserted *within* each form, not
  across forms.** The hash folds in the `PATH_SEGMENTS` table that the
  `path` form populates and `pins` does not, so it is intentionally
  unequal across forms even for identical connectivity. The cross-form
  invariant is membership; the hash's own contract (stability across
  parses, the TASK-053 golden guard) is asserted per form.

## Performance budget

**No budget.** NetGraph construction is linear in connection count and
runs in well under the PR-time budget on every shipped circuit; there
is no pinned number because nothing has ever approached a concern.

## Known uncovered cases

- **Property-based form equivalence over *richer* topologies.**
  `tests/netgraph/test_form_equivalence_properties.py` (TASK-135) now
  covers `pins`-vs-`path` over a generated series chain and `bus`-vs-`pins`
  over a generated multi-drop net. Generation over branching trees, mixed
  forms in one circuit, or `path` tails that merge into named nets remains
  a candidate; the merge-ordering interaction is deliberately excluded
  (see the property file's scoping note) because it is a within-net-order
  effect, not a form-equivalence one.
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
| `tests/netgraph/test_form_equivalence_properties.py` | ✓ | | |

All four run at PR-time via `pytest`. The golden test is *also* the
kind of check a nightly job would host if the suite ever grows a
nightly tier; the property suite's large-iteration variant is a second
nightly candidate (IDEA-014); today both are fast enough to stay at
PR-time.
