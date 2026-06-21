---
subsystem: router
covers: src/circuitsmith/layout/router.py
---

# Manhattan router — test plan

The router takes a placed `LayoutResult` plus the `NetGraph` and emits
orthogonal wire geometry, reporting two quality counts the rubric then
judges: `crossings` and `intra_component_intersections`. It is
deliberately a *measure-don't-avoid* router today — it routes the direct
orthogonal path and counts problems rather than re-routing around them
(routing-around-bodies is a post-v0.1 enhancement).

Covers [`router.py`](../../../src/circuitsmith/layout/router.py).

Test files covering this subsystem:

```pytest
tests/test_router.py
tests/layout/test_router_properties.py
```

## Inputs and outputs

- **Input** — `route(layout, graph, profiles)`: a `LayoutResult`, the
  `NetGraph`, and the profile registry (for pin sides).
- **Output** — `RouterResult(routes, crossings,
  intra_component_intersections)`, where each `WireRoute` carries
  orthogonal `Segment`s.

## Unit tests

`tests/test_router.py` (TASK-010) pins the four contract properties on
hand-built fixtures:

- **Orthogonality** — every segment of every wire is axis-aligned
  (`seg.is_orthogonal`); no diagonals.
- **Determinism** — two `route()` calls on the same input produce
  byte-identical segment lists and the same `crossings` count.
- **Crossing detection** — a constructed H/V layout where two wires
  cross at right angles reports `crossings >= 1`; the pure
  `_segments_cross` helper is unit-tested directly (perpendicular
  segments cross; parallel same-axis segments do not).
- **Body intersections** — when a wire's interior passes through a
  non-endpoint component cell, `intra_component_intersections` is
  incremented (and is `0` for an isolated two-component layout). The
  router *records* this; the rubric decides if it is acceptable.

## Integration tests

The router runs inside the renderer pipeline on every shipped circuit;
that path is exercised by `tests/test_full_pedal_fixture.py` and the
rubric integration (see [`renderer.md`](renderer.md) and
[`layout-kernel.md`](layout-kernel.md)). There is no router-specific
integration file — its neighbours own those assertions.

## Golden / snapshot tests

The byte-identical-across-runs assertion is the snapshot guard; there is
no committed golden geometry file. Wire geometry is validated by
invariant (orthogonality, crossing count) rather than by pinning exact
coordinates, which would be brittle against placement tweaks.

## Property / fuzz tests

`tests/layout/test_router_properties.py` (TASK-135) closes what was this
chapter's headline gap — IDEA-003 anticipated property tests over
generated netlists, and they now exist. Rather than generate arbitrary
circuits (almost never routable), the suite generates **variations of a
known-good template**: an esp32 MCU plus a Hypothesis-chosen number (1–4)
of `GPIO → resistor → LED → ground-pin` branches, with Hypothesis-varied
resistor values, net names, and `connections` ordering. The layout and
NetGraph are built exactly as the example-based `tests/test_router.py`
does, so every generated case is valid by construction.

Invariants asserted (PR-time, `max_examples=40`, `deadline=None`):

- **Orthogonality** — every `Segment` of every routed wire is horizontal
  or vertical.
- **Determinism** — routing the same input twice yields byte-identical
  geometry (segment lists, crossings, body-intersection counts).
- **Net-order invariance** — shuffling the `connections` list yields
  identical routed geometry, because the §9 contract sorts nets
  alphabetically before routing.

Deliberately **out of scope** (not asserted): asymptotic optimality,
aesthetic quality, crossing counts (the router makes no optimality claim).

**Scoping note discovered while writing the suite.** Net-order invariance
holds only when no single net's *membership* depends on entry order. A
path that terminates at a bare `GND` net-name token triggers the path-tail
merge, and `NetGraph` appends the merged pin into `GND` in
connection-declaration order — so reordering entries reorders `GND`'s
membership and the router routes it as mirror-image geometry. That is the
within-net-order effect (which is contract-correct, not an invariant)
reached through a different door, not router non-determinism. The strategy
sidesteps it by terminating each branch at the real `U1.GNDL` pin, keeping
every net's membership order entry-order-independent. Permutation is
therefore scoped to net order; within-net pin order is held fixed.

## Performance budget

**No automated benchmark today.** On the shipped fixtures the router is
sub-perceptible — the six router tests are a negligible slice of the
~9 s full-suite run. Provisional budget until a benchmark lands:
a single `route()` on a shipped-scale circuit should stay well under
~1 s; investigate if it ever exceeds that.

**Known slow / degenerate input class:** high-fan-out nets on a small
grid. Because the router measures rather than avoids body intersections,
a dense net can drive `intra_component_intersections` up without the
router slowing materially — the cost shows up as rubric failures, not
runtime. A dedicated perf gate is a TASK-090 candidate.

## Known uncovered cases

- **Property-based routing over *arbitrary* topology.** The property
  suite (TASK-135) generates variations of a known-good template, not
  arbitrary circuits — arbitrary circuits are almost never routable, so
  template-variation is the high-signal strategy. Generation over a wider
  topology space (multiple regions, attached chains, bus nets) remains a
  candidate; the current suite covers the orthogonality / determinism /
  net-order invariants over the passive-branch family.
- **Route-around-bodies.** The router counts
  `intra_component_intersections` but does not re-route to avoid them.
  Rationale: intentional v0.1 scope; resolution is a post-v0.1
  enhancement, documented so the count's meaning is unambiguous.
- **No perf benchmark.** Runtime is asserted nowhere; the budget above
  is a target, not a gate. Rationale: nothing has approached a concern;
  a gate is cheap to add when the degenerate class shows up in practice.

## Cadence

| Test file | PR | Nightly | Release |
|---|:--:|:--:|:--:|
| `tests/test_router.py` | ✓ | | |
| `tests/layout/test_router_properties.py` | ✓ | | |

Both run at PR-time. The property suite uses a fast
`max_examples=40` budget so it stays a negligible slice of the PR-time
run; the large-iteration variant (`max_examples` in the thousands) is the
designated **nightly** citizen once the nightly tier (IDEA-014) exists.
