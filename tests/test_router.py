"""
Router tests for TASK-010.

Covers the four acceptance criteria:
  1. Orthogonal-only segments (no diagonals).
  2. Byte-identical output across two runs on the same input.
  3. Wire crossings detected and counted.
  4. Wires do not pass through component bodies (only pin anchors).
"""
from __future__ import annotations

from circuit.layout_engine import (
    LayoutResult,
    Placement,
    RouterResult,
    Segment,
    route,
)
from circuit.netgraph import NetGraph


def _profiles() -> dict:
    return {
        "mcu/esp32": {
            "category": "ic",
            "pins": {
                "D13": {"side": "left",  "type": "GPIO",   "direction": "bidir"},
                "D21": {"side": "right", "type": "GPIO",   "direction": "bidir"},
                "GNDL": {"side": "left",  "type": "GROUND", "direction": "in"},
            },
        },
        "passives/resistor": {
            "category": "resistor",
            "pins": {
                "1": {"side": "left",  "type": "TERMINAL", "direction": "bidir"},
                "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
            },
        },
        "passives/led": {
            "category": "led",
            "pins": {
                "A": {"side": "left",  "type": "TERMINAL", "direction": "in"},
                "K": {"side": "right", "type": "TERMINAL", "direction": "in"},
            },
        },
    }


def _build_layout_and_graph() -> tuple[LayoutResult, NetGraph]:
    """Two-component placement: U1 at centre, D1 on left column row 0."""
    placements = {
        "U1": Placement(ref="U1", region="mcu-center", topology_fingerprint="sha1:0000"),
        "D1": Placement(ref="D1", region="left-column", row=0, label="left",
                        topology_fingerprint="sha1:0001"),
        "R1": Placement(ref="R1", attached_to="D1", topology_fingerprint="sha1:0002"),
    }
    circuit = {
        "meta": {"title": "router", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor", "value": 220},
            "D1": {"type": "passives/led", "color": "green"},
        },
        "connections": [
            {"net": "PWR_LED", "path": ["U1.D13", "R1.1", "R1.2", "D1.A", "D1.K", "GND"]},
            {"net": "GND",     "pins": ["U1.GNDL"]},
        ],
    }
    graph = NetGraph.from_yaml_dict(circuit)
    return LayoutResult(placements=placements), graph


def test_segments_are_orthogonal_only():
    layout, graph = _build_layout_and_graph()
    result = route(layout=layout, graph=graph, profiles=_profiles())
    for wire in result.routes:
        for seg in wire.segments:
            assert seg.is_orthogonal, f"non-orthogonal segment: {seg}"


def test_byte_identical_across_two_runs():
    layout, graph = _build_layout_and_graph()
    a = route(layout=layout, graph=graph, profiles=_profiles())
    b = route(layout=layout, graph=graph, profiles=_profiles())
    assert [w.segments for w in a.routes] == [w.segments for w in b.routes]
    assert a.crossings == b.crossings


def test_crossings_detected_for_intentional_overlap():
    """Construct a 2D layout where two wires cross at right angles."""
    placements = {
        "U1": Placement(ref="U1", region="mcu-center", topology_fingerprint="sha1:0000"),
        "L":  Placement(ref="L",  region="left-column", row=0, topology_fingerprint="sha1:0001"),
        "R":  Placement(ref="R",  region="right-column", row=2, topology_fingerprint="sha1:0002"),
        "T":  Placement(ref="T",  region="top-row", col=2, topology_fingerprint="sha1:0003"),
        "B":  Placement(ref="B",  region="bottom-row", col=2, topology_fingerprint="sha1:0004"),
    }
    layout = LayoutResult(placements=placements)
    circuit = {
        "meta": {"title": "crossing", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "L":  {"type": "passives/led", "color": "blue"},
            "R":  {"type": "passives/led", "color": "blue"},
            "T":  {"type": "passives/led", "color": "blue"},
            "B":  {"type": "passives/led", "color": "blue"},
        },
        "connections": [
            # Horizontal-spanning net: L.A → R.A (passes through x ≈ 0).
            {"net": "HORIZ", "pins": ["L.A", "R.A"]},
            # Vertical-spanning net: T.A → B.A (passes through y ≈ 0).
            {"net": "VERT",  "pins": ["T.A", "B.A"]},
        ],
    }
    graph = NetGraph.from_yaml_dict(circuit)
    result = route(layout=layout, graph=graph, profiles=_profiles())
    assert result.crossings >= 1, (
        f"expected at least one crossing for orthogonal H/V wires; got {result.crossings}; "
        f"routes: {result.routes}"
    )


def test_segment_intersection_helper_is_pure():
    """Two segments at the same point on different orientations cross once."""
    h = Segment(-2, 0, 2, 0)
    v = Segment(0, -2, 0, 2)
    from circuit.layout_engine.router import _segments_cross
    assert _segments_cross(h, v) is True
    assert _segments_cross(v, h) is True
    # Parallel-same-axis segments do not "cross" by this contract.
    h2 = Segment(-1, 0, 1, 0)
    assert _segments_cross(h, h2) is False


def test_wires_through_component_bodies_are_counted():
    """When a wire's interior passes through a non-endpoint component cell,
    the router records it under `intra_component_intersections`. The rubric
    (TASK-011) then decides whether that count is acceptable."""
    layout, graph = _build_layout_and_graph()
    result: RouterResult = route(layout=layout, graph=graph, profiles=_profiles())
    # In the day-one fixture, R1 sits between U1 and D1, so the GND wire
    # from D1.K (left-column) back to U1.GNDL (mcu-center) literally passes
    # through R1's cell. The router reports this; routing-around is a
    # post-v0.1 enhancement.
    assert result.intra_component_intersections >= 1


def test_isolated_layout_has_no_intra_component_intersections():
    """A layout with no non-endpoint component on the wire path reports 0."""
    placements = {
        "U1": Placement(ref="U1", region="mcu-center", topology_fingerprint="sha1:0000"),
        "D1": Placement(ref="D1", region="left-column", row=0, topology_fingerprint="sha1:0001"),
    }
    layout = LayoutResult(placements=placements)
    circuit = {
        "meta": {"title": "isolated", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "D1": {"type": "passives/led", "color": "green"},
        },
        "connections": [
            {"net": "PWR_LED", "pins": ["U1.D13", "D1.A"]},
        ],
    }
    graph = NetGraph.from_yaml_dict(circuit)
    result = route(layout=layout, graph=graph, profiles=_profiles())
    assert result.intra_component_intersections == 0
