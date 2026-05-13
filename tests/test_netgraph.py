"""
NetGraph tests for TASK-008.

Covers the four acceptance criteria:

1. The documented API (`nets`, `net_meta`, `pin_index`, `pins_on_net`,
   `nets_containing_pin`, `flattened_segments`, `components_between`).
2. Construction determinism — two parses produce structurally
   identical graphs (canonical_hash match).
3. The three connection forms (`pins`, `path`, `bus`) flatten to the
   same canonical net representation for equivalent topology.
4. Pin-index lookup by (component, pin_name).

Plus the portability contract (no host-project imports) as a smoke
test — see `test_components.py` for the broader portability lint.
"""
from __future__ import annotations

import pytest

from circuitsmith.netgraph import NetGraph, PinRef


# ── Fixtures ─────────────────────────────────────────────────────────────


def _pins_form_circuit() -> dict:
    """Button on D13 to GND, expressed entirely with `pins:` joins."""
    return {
        "meta": {"title": "pins form", "target": "esp32"},
        "components": {
            "U1":  {"type": "mcu/esp32"},
            "SW1": {"type": "passives/pushbutton"},
        },
        "connections": [
            {"net": "BTN_A", "pins": ["U1.D13", "SW1.1"]},
            {"net": "GND",   "pins": ["U1.GNDL", "SW1.2"]},
        ],
    }


def _path_form_circuit_with_pulls() -> dict:
    """Button on D13 to GND, expressed with a `path:` and a `pull:`."""
    return {
        "meta": {"title": "path form", "target": "esp32"},
        "components": {
            "U1":  {"type": "mcu/esp32"},
            "SW1": {"type": "passives/pushbutton"},
        },
        "connections": [
            {
                "net":  "BTN_A",
                "path": ["U1.D13", "SW1.1", "SW1.2", "GND"],
                "pull": "firmware",
            },
            {"net": "GND", "pins": ["U1.GNDL"]},
        ],
    }


def _led_path_circuit() -> dict:
    """GPIO → resistor → LED → GND — three nodes-between-edges, two real segments."""
    return {
        "meta": {"title": "led path", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor", "value": 220},
            "D1": {"type": "passives/led", "color": "green"},
        },
        "connections": [
            {
                "net":  "PWR_LED",
                "path": ["U1.D25", "R1.1", "R1.2", "D1.A", "D1.K", "GND"],
            },
            {"net": "GND", "pins": ["U1.GNDL"]},
        ],
    }


def _bus_circuit() -> dict:
    """3-device I²C bus: MCU + sensor on backbone, second sensor on a tap."""
    return {
        "meta": {"title": "bus form", "target": "esp32"},
        "components": {
            "U1":  {"type": "mcu/esp32"},
            "IC1": {"type": "sensors/bme280"},
            "IC2": {"type": "sensors/bme280"},
        },
        "connections": [
            {
                "net":      "I2C_SDA",
                "bus":      True,
                "backbone": ["U1.D21", "IC1.SDA"],
                "taps":     ["IC2.SDA"],
            },
        ],
    }


# ── 1. Documented API ───────────────────────────────────────────────────


def test_api_surface_is_present():
    g = NetGraph.from_yaml_dict(_pins_form_circuit())
    assert hasattr(g, "nets")
    assert hasattr(g, "net_meta")
    assert hasattr(g, "pin_index")
    assert callable(g.pins_on_net)
    assert callable(g.nets_containing_pin)
    assert callable(g.flattened_segments)
    assert callable(g.components_between)
    assert callable(g.canonical_hash)


def test_pins_form_membership():
    g = NetGraph.from_yaml_dict(_pins_form_circuit())
    assert g.pins_on_net("BTN_A") == [PinRef("U1", "D13"), PinRef("SW1", "1")]
    assert g.pins_on_net("GND") == [PinRef("U1", "GNDL"), PinRef("SW1", "2")]


def test_net_meta_carries_pull():
    g = NetGraph.from_yaml_dict(_path_form_circuit_with_pulls())
    assert g.net_meta["BTN_A"].pull == "firmware"


def test_net_meta_carries_bus_backbone_count():
    g = NetGraph.from_yaml_dict(_bus_circuit())
    # backbone has 2 pins; bus_backbone_count records the prefix length
    assert g.net_meta["I2C_SDA"].bus_backbone_count == 2
    assert g.pins_on_net("I2C_SDA") == [
        PinRef("U1", "D21"),
        PinRef("IC1", "SDA"),
        PinRef("IC2", "SDA"),
    ]


# ── 2. Determinism via canonical_hash ────────────────────────────────────


def test_canonical_hash_is_stable_across_parses():
    a = NetGraph.from_yaml_dict(_led_path_circuit())
    b = NetGraph.from_yaml_dict(_led_path_circuit())
    assert a.canonical_hash() == b.canonical_hash()


def test_canonical_hash_changes_with_topology():
    a = NetGraph.from_yaml_dict(_led_path_circuit())
    altered = _led_path_circuit()
    altered["connections"][0]["path"] = ["U1.D26", "R1.1", "R1.2", "D1.A", "D1.K", "GND"]
    b = NetGraph.from_yaml_dict(altered)
    assert a.canonical_hash() != b.canonical_hash()


def test_canonical_hash_is_hex_sha256():
    g = NetGraph.from_yaml_dict(_pins_form_circuit())
    digest = g.canonical_hash()
    assert len(digest) == 64
    int(digest, 16)  # parses cleanly as hex


# ── 3. Three connection forms flatten to one canonical representation ────


def test_pins_and_path_produce_equivalent_btn_a_membership():
    """The button-to-GND topology is identical whether written as `pins:` or `path:`."""
    g_pins = NetGraph.from_yaml_dict(_pins_form_circuit())
    g_path = NetGraph.from_yaml_dict(_path_form_circuit_with_pulls())

    btn_pins = set(g_pins.pins_on_net("BTN_A"))
    btn_path = set(g_path.pins_on_net("BTN_A"))
    # `path:` form has segments BTN_A=[U1.D13, SW1.1] and a content-addressed
    # tail; the BTN_A segment carries the same pin pair as the `pins:` form
    # (the tail segment is the same wire, just under a different name).
    assert btn_pins == btn_path == {PinRef("U1", "D13"), PinRef("SW1", "1")}


def test_path_merge_into_named_net():
    """Path terminating at `GND` merges the adjacent pin into GND's membership."""
    g = NetGraph.from_yaml_dict(_led_path_circuit())
    gnd_members = g.pins_on_net("GND")
    # D1.K is the pin adjacent to the GND net-name endpoint, merged into GND.
    assert PinRef("D1", "K") in gnd_members
    # U1.GNDL came from the explicit `pins:` form in the same circuit.
    assert PinRef("U1", "GNDL") in gnd_members


def test_path_segment_naming():
    """First segment carries the declared name; remaining segments are content-addressed."""
    g = NetGraph.from_yaml_dict(_led_path_circuit())
    # 4 nodes ([U1.D25] [R1.1, R1.2] [D1.A, D1.K] [GND]) → 3 segments.
    assert "PWR_LED" in g.nets
    assert "PWR_LED__R1_2__D1_A" in g.nets
    assert "PWR_LED__D1_K__GND" in g.nets
    # First segment pins (declaration order):
    assert g.pins_on_net("PWR_LED") == [PinRef("U1", "D25"), PinRef("R1", "1")]
    # Middle segment:
    assert g.pins_on_net("PWR_LED__R1_2__D1_A") == [PinRef("R1", "2"), PinRef("D1", "A")]
    # Tail segment to GND net-name node — pin-side only:
    assert g.pins_on_net("PWR_LED__D1_K__GND") == [PinRef("D1", "K")]


def test_flattened_segments_iterates_in_declaration_order():
    g = NetGraph.from_yaml_dict(_led_path_circuit())
    segs = g.flattened_segments("PWR_LED")
    assert segs[0] == (PinRef("U1", "D25"), PinRef("R1", "1"))
    assert segs[1] == (PinRef("R1", "2"), PinRef("D1", "A"))
    # Net-name terminating segment — pair repeats the pin so callers get a stable shape.
    assert segs[2] == (PinRef("D1", "K"), PinRef("D1", "K"))


def test_flattened_segments_rejects_non_path_net():
    g = NetGraph.from_yaml_dict(_pins_form_circuit())
    with pytest.raises(ValueError, match="not a path-sourced net"):
        g.flattened_segments("BTN_A")


def test_bus_collapses_to_one_entry():
    g = NetGraph.from_yaml_dict(_bus_circuit())
    assert list(g.nets) == ["I2C_SDA"]
    assert g.pins_on_net("I2C_SDA") == [
        PinRef("U1", "D21"),
        PinRef("IC1", "SDA"),
        PinRef("IC2", "SDA"),
    ]


# ── 4. pin_index ─────────────────────────────────────────────────────────


def test_pin_index_lookup_by_component_and_pin():
    g = NetGraph.from_yaml_dict(_pins_form_circuit())
    nets_for_d13 = g.nets_containing_pin(PinRef("U1", "D13"))
    assert nets_for_d13 == ["BTN_A"]
    nets_for_gndl = g.nets_containing_pin(PinRef("U1", "GNDL"))
    assert nets_for_gndl == ["GND"]


def test_pin_index_handles_pin_on_multiple_nets():
    """A pin merged into a named net via path-end appears in both nets."""
    g = NetGraph.from_yaml_dict(_path_form_circuit_with_pulls())
    sw1_2_nets = g.nets_containing_pin(PinRef("SW1", "2"))
    # SW1.2 is in the content-addressed tail segment AND merged into GND.
    assert "GND" in sw1_2_nets
    assert any("__" in name for name in sw1_2_nets), (
        f"expected a content-addressed segment in {sw1_2_nets}"
    )


def test_pin_index_returns_empty_for_unknown_pin():
    g = NetGraph.from_yaml_dict(_pins_form_circuit())
    assert g.nets_containing_pin(PinRef("U1", "DOES_NOT_EXIST")) == []


# ── components_between (path traversal primitive) ───────────────────────


def test_components_between_walks_a_path():
    g = NetGraph.from_yaml_dict(_led_path_circuit())
    # Walking from the GPIO pin to the LED anode crosses R1.
    refs = g.components_between(PinRef("U1", "D25"), PinRef("D1", "A"))
    assert refs == ["R1"]


def test_components_between_rejects_pins_not_on_a_path():
    g = NetGraph.from_yaml_dict(_pins_form_circuit())
    with pytest.raises(ValueError, match="not co-located on any path-sourced net"):
        g.components_between(PinRef("U1", "D13"), PinRef("SW1", "1"))


# ── Portability smoke test (ADR-0012) ───────────────────────────────────


def test_module_has_no_host_project_imports():
    """netgraph.py must not import scripts.*, data.*, or CircuitSmith — ADR-0012."""
    import re
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src" / "circuitsmith" / "netgraph.py"
    text = src.read_text()
    forbidden = [
        r"\bimport\s+scripts\b",
        r"\bfrom\s+scripts\b",
        r"\bimport\s+data\b",
        r"\bfrom\s+data\b",
        r"\bCircuitSmith\b",
    ]
    leaks = [pat for pat in forbidden if re.search(pat, text)]
    assert not leaks, f"netgraph.py leaks host-project tokens: {leaks}"
