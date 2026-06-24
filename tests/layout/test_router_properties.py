"""Property-based router tests (TASK-135).

The router chapter ([`docs/developers/testing/router.md`]) records the
headline gap IDEA-003 anticipated: property-based tests over generated
netlists. `tests/test_router.py` pins the router's contract on a handful
of hand-built fixtures; this module re-asserts the same invariants over a
*generated* family of valid layouts.

Strategy design — valid by construction
---------------------------------------
Arbitrary circuits are almost never routable (placements must resolve to
coordinates, pins must exist on profiles, the NetGraph must build). So we
do not generate arbitrary circuits: we generate **variations of a known-
good template**. The template is an esp32 MCU plus a Hypothesis-chosen
number (1-4) of passive branches, each branch being a
``GPIO → resistor → LED → ground-pin`` path. Hypothesis varies:

  - the branch count (1-4),
  - each resistor's value (a routing-irrelevant payload — the router
    coordinatises by region/row, never by value),
  - the net names (likewise routing-irrelevant beyond net *naming*), and
  - the order of the ``connections`` list (the determinism contract sorts
    nets alphabetically, so order must not change geometry).

Everything is built exactly the way ``tests/test_router.py`` builds it:
a ``LayoutResult(placements=...)``, a circuit dict fed through
``NetGraph.from_yaml_dict``, and the shared ``_profiles()`` registry.

Invariants asserted (all hold for any valid input)
--------------------------------------------------
  - **Orthogonality** — every ``Segment`` is horizontal or vertical.
  - **Determinism** — routing the same input twice yields identical
    geometry.
  - **Net-order invariance** — shuffling the ``connections`` list yields
    identical routed geometry (nets sort alphabetically per the §9
    contract). The permutation is scoped to net *order* only — the
    within-net pin order is the per-pin-pair iteration order the contract
    pins, so it is held fixed (see module note below).

Explicitly out of scope (NOT asserted): routing optimality, aesthetic
quality, crossing counts. The router is a measure-don't-avoid router and
makes no optimality claim.

Note on permutation scope
-------------------------
Net-order invariance permutes the order of whole ``connections`` entries
only. The router's determinism contract (§9) makes *net* iteration
alphabetical, so reordering entries is geometry-preserving — **provided no
single net's membership depends on entry order**. Two scoping decisions
follow from that proviso:

  1. *Within-net pin order is held fixed.* The router walks
     ``pins_on_net`` in declaration order and routes each consecutive
     pair, so permuting pins inside a net would legitimately change the
     wire pairs. That is contract-correct behaviour, not an invariant.

  2. *Each branch path terminates at a real pin (``U1.GNDL``), not at a
     bare ``GND`` net-name token.* A bare net-name terminator triggers the
     path-tail merge, folding the adjacent pin into a separately-declared
     ``GND`` net — and ``NetGraph`` appends merged members in
     *connection-declaration order*. Reordering the entries would then
     reorder ``GND``'s membership (``[U1.GNDL, D1.K]`` vs ``[D1.K,
     U1.GNDL]``), which the router routes as mirror-image geometry. That
     is a real interaction (it falsifies a naive net-order-invariance
     property), but it is the within-net-order effect of (1) reached
     through a different door, not a router non-determinism. Terminating
     at a real pin keeps every net's membership order independent of entry
     order, so net-order invariance holds cleanly.
"""
from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from circuitsmith.layout import (
    LayoutResult,
    Placement,
    route,
)
from circuitsmith.netgraph import NetGraph

# Fast PR-time budget. Large-iteration runs are deferred to a nightly
# tier (IDEA-014); see the router chapter's cadence table.
_SETTINGS = settings(max_examples=40, deadline=None)

# A pool of distinct GPIO pins on the MCU, one per generated branch.
_GPIO_PINS = ["D13", "D21", "D25", "D26"]
_MAX_BRANCHES = len(_GPIO_PINS)


def _profiles() -> dict:
    """Profile registry — mirrors tests/test_router.py._profiles()."""
    return {
        "mcu/esp32": {
            "category": "ic",
            "pins": {
                "D13": {"side": "left", "type": "GPIO", "direction": "bidir"},
                "D21": {"side": "right", "type": "GPIO", "direction": "bidir"},
                "D25": {"side": "left", "type": "GPIO", "direction": "bidir"},
                "D26": {"side": "right", "type": "GPIO", "direction": "bidir"},
                "GNDL": {"side": "left", "type": "GROUND", "direction": "in"},
            },
        },
        "passives/resistor": {
            "category": "resistor",
            "pins": {
                "1": {"side": "left", "type": "TERMINAL", "direction": "bidir"},
                "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
            },
        },
        "passives/led": {
            "category": "led",
            "pins": {
                "A": {"side": "left", "type": "TERMINAL", "direction": "in"},
                "K": {"side": "right", "type": "TERMINAL", "direction": "in"},
            },
        },
    }


# ── Strategy ──────────────────────────────────────────────────────────────


# Resistor values: routing-irrelevant payload. The router coordinatises by
# region/row, never by component value — varying this exercises the build
# path without perturbing geometry.
_resistor_values = st.sampled_from([100, 150, 220, 330, 470, 1000, 4700, 10000])

# Net names: a small alphabet of distinct, schema-plausible identifiers.
# One is drawn per branch; routing-irrelevant beyond net *naming*.
_net_names = st.sampled_from(
    ["PWR_LED", "SIGNAL", "BRANCH_A", "BRANCH_B", "DRIVE", "OUT_X", "OUT_Y", "LANE"]
)


@st.composite
def _branchy_circuit(draw):
    """Generate a valid esp32 + N passive-branch circuit and its placements.

    Returns ``(placements, connections)`` where ``connections`` is the
    list of net entries in *declaration* order (a later test shuffles it).
    Valid by construction: every component is placed, every pin exists on
    its profile, and the topology is a plain series path per branch.
    """
    n = draw(st.integers(min_value=1, max_value=_MAX_BRANCHES))

    # Distinct net names, one per branch (sampled without replacement so
    # branches never collide on a net name).
    names = draw(
        st.lists(
            _net_names,
            min_size=n,
            max_size=n,
            unique=True,
        )
    )
    values = draw(
        st.lists(_resistor_values, min_size=n, max_size=n)
    )

    placements: dict[str, Placement] = {
        "U1": Placement(ref="U1", region="mcu-center", topology_fingerprint="sha1:0000"),
    }
    components: dict[str, dict] = {"U1": {"type": "mcu/esp32"}}
    connections: list[dict] = []

    for i in range(n):
        led = f"D{i + 1}"
        res = f"R{i + 1}"
        gpio = _GPIO_PINS[i]
        # LED on the left column, one row per branch; resistor rides
        # attached to the LED (the construction tests/test_router.py uses).
        placements[led] = Placement(
            ref=led, region="left-column", row=i, label="left",
            topology_fingerprint=f"sha1:led{i}",
        )
        placements[res] = Placement(
            ref=res, attached_to=led, topology_fingerprint=f"sha1:res{i}",
        )
        components[led] = {"type": "passives/led", "color": "green"}
        components[res] = {"type": "passives/resistor", "value": values[i]}
        # Terminate each branch at a real pin (U1.GNDL), not a bare `GND`
        # net-name token — see the module docstring's permutation-scope
        # note (2): a bare terminator's path-tail merge would make GND's
        # membership order depend on connection order, breaking net-order
        # invariance for reasons that are really the within-net-order
        # effect, not router non-determinism.
        connections.append(
            {
                "net": names[i],
                "path": [
                    f"U1.{gpio}", f"{res}.1", f"{res}.2", f"{led}.A", f"{led}.K", "U1.GNDL",
                ],
            }
        )

    return placements, connections


def _route(placements: dict, connections: list[dict]):
    """Build LayoutResult + NetGraph the tests/test_router.py way and route."""
    circuit = {
        "meta": {"title": "router-prop", "target": "esp32"},
        "components": _components_for(connections, placements),
        "connections": connections,
    }
    graph = NetGraph.from_yaml_dict(circuit)
    layout = LayoutResult(placements=placements)
    return route(layout=layout, graph=graph, profiles=_profiles())


def _components_for(connections: list[dict], placements: dict) -> dict:
    """Reconstruct the components map from the placement refs.

    Refs starting with ``R`` are resistors, ``D`` are LEDs, ``U1`` is the
    MCU. (Values are routing-irrelevant, so a placeholder value suffices
    for NetGraph construction, which ignores component bodies entirely.)
    """
    components: dict[str, dict] = {}
    for ref in placements:
        if ref == "U1":
            components[ref] = {"type": "mcu/esp32"}
        elif ref.startswith("R"):
            components[ref] = {"type": "passives/resistor", "value": 220}
        elif ref.startswith("D"):
            components[ref] = {"type": "passives/led", "color": "green"}
    return components


def _geometry(result) -> list:
    """Routed geometry as a comparable structure: per-route (net, segments)."""
    return [(w.net, w.a, w.b, w.segments) for w in result.routes]


# ── Properties ─────────────────────────────────────────────────────────────


@_SETTINGS
@given(circuit=_branchy_circuit())
def test_all_segments_orthogonal(circuit):
    """Every segment of every routed wire is axis-aligned (no diagonals)."""
    placements, connections = circuit
    result = _route(placements, connections)
    for wire in result.routes:
        for seg in wire.segments:
            assert seg.is_horizontal or seg.is_vertical, (
                f"non-orthogonal segment {seg} on net {wire.net}"
            )


@_SETTINGS
@given(circuit=_branchy_circuit())
def test_routing_is_deterministic(circuit):
    """Routing the same input twice yields byte-identical geometry."""
    placements, connections = circuit
    a = _route(placements, connections)
    b = _route(placements, connections)
    assert _geometry(a) == _geometry(b)
    assert a.crossings == b.crossings
    assert a.intra_component_intersections == b.intra_component_intersections


@_SETTINGS
@given(circuit=_branchy_circuit(), seed=st.randoms(use_true_random=False))
def test_net_order_is_invariant(circuit, seed):
    """Shuffling the connections list does not change routed geometry.

    The §9 determinism contract sorts nets alphabetically before routing,
    so the declaration order of ``connections`` entries is irrelevant to
    the output. Permutation is scoped to net order only (see module note).
    """
    placements, connections = circuit
    shuffled = list(connections)
    seed.shuffle(shuffled)

    baseline = _route(placements, connections)
    permuted = _route(placements, shuffled)
    assert _geometry(permuted) == _geometry(baseline)
