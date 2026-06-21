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

**None — and this is the subsystem's notable gap.** IDEA-003 anticipated
property tests over randomised netlists (the router is the natural home
for them). Today every invariant is checked on a handful of
hand-constructed layouts. The invariants a property suite *would*
assert: every segment orthogonal, every net routable, determinism under
input permutation. The properties deliberately **out of scope**:
asymptotic optimality and aesthetic quality (the router makes no
optimality claim). Filed as the headline TASK-090 candidate for this
chapter.

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

- **Property-based routing.** No randomised-netlist generation (see
  above). Rationale: the invariant set is small and well-covered by
  examples, but generated topology is the right long-term guard —
  TASK-090 candidate.
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

Runs at PR-time. A property-based router suite, when added, would be a
natural **nightly** citizen (large iteration counts), keeping the
PR-time slice fast.
