"""EPIC-014 / TASK-113 — kernel canonical rule: C + C decoupling pair."""
from __future__ import annotations

from circuitsmith.layout import place
from circuitsmith.netgraph import NetGraph


def _profiles() -> dict:
    return {
        "mcu/esp32": {
            "category": "ic",
            "pins": {
                "V33": {"side": "right", "type": "POWER", "direction": "in"},
                "GNDL": {"side": "left", "type": "GROUND", "direction": "in"},
            },
        },
        "passives/capacitor": {
            "category": "capacitor",
            "pins": {
                "1": {"side": "left", "type": "TERMINAL", "direction": "bidir"},
                "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
            },
        },
    }


def _pair_on_v33() -> dict:
    return {
        "meta": {"title": "cc-decoupling", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "C1": {"type": "passives/capacitor", "value": "100n"},
            "C2": {"type": "passives/capacitor", "value": "10u"},
        },
        "connections": [
            {"net": "V33", "pins": ["U1.V33", "C1.1", "C2.1"]},
            {"net": "GND", "pins": ["U1.GNDL", "C1.2", "C2.2"]},
        ],
    }


def _build(circuit: dict) -> NetGraph:
    return NetGraph.from_yaml_dict(circuit)


def test_cc_decoupling_pair_matches():
    circuit = _pair_on_v33()
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    c1 = result.placements["C1"]
    c2 = result.placements["C2"]
    assert c1.region == c2.region
    assert c1.region.startswith("cc-decoupling-")
    assert c1.label == "cc-decoupling"
    # Stable ordering: C1 (smaller refdes) → row 0, C2 → row 1.
    assert c1.row == 0
    assert c2.row == 1


def test_singleton_cap_falls_back_to_decoupling_cap_rule():
    """A single decoupling cap (no partner) must still classify, via the
    pre-existing RULE_DECOUPLING_CAP path."""
    circuit = {
        "meta": {"title": "single-decap", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "C1": {"type": "passives/capacitor", "value": "100n"},
        },
        "connections": [
            {"net": "V33", "pins": ["U1.V33", "C1.1"]},
            {"net": "GND", "pins": ["U1.GNDL", "C1.2"]},
        ],
    }
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    # Pre-existing rule → bus-V33 region.
    assert result.placements["C1"].region == "bus-V33"


def test_cc_decoupling_two_rails_distinct_regions():
    """Two decoupling pairs on different rails (V33 + VBAT) get distinct regions."""
    profiles = _profiles()
    profiles["mcu/esp32"]["pins"]["VBAT"] = {
        "side": "right", "type": "POWER", "direction": "in",
    }
    circuit = {
        "meta": {"title": "two-rails", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "C1": {"type": "passives/capacitor", "value": "100n"},
            "C2": {"type": "passives/capacitor", "value": "10u"},
            "C3": {"type": "passives/capacitor", "value": "100n"},
            "C4": {"type": "passives/capacitor", "value": "10u"},
        },
        "connections": [
            {"net": "V33", "pins": ["U1.V33", "C1.1", "C2.1"]},
            {"net": "VBAT", "pins": ["U1.VBAT", "C3.1", "C4.1"]},
            {"net": "GND", "pins": ["U1.GNDL", "C1.2", "C2.2", "C3.2", "C4.2"]},
        ],
    }
    result = place(circuit=circuit, graph=_build(circuit), profiles=profiles)
    v33_region = result.placements["C1"].region
    vbat_region = result.placements["C3"].region
    assert v33_region != vbat_region
    assert result.placements["C2"].region == v33_region
    assert result.placements["C4"].region == vbat_region
