"""EPIC-014 / TASK-112 — kernel canonical rule: R + C high-pass."""
from __future__ import annotations

from circuitsmith.layout import place
from circuitsmith.netgraph import NetGraph


def _profiles() -> dict:
    return {
        "mcu/esp32": {
            "category": "ic",
            "pins": {
                "D25": {"side": "left", "type": "GPIO", "direction": "bidir"},
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
        "passives/capacitor": {
            "category": "capacitor",
            "pins": {
                "1": {"side": "left", "type": "TERMINAL", "direction": "bidir"},
                "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
            },
        },
    }


def _single_high_pass() -> dict:
    """One RC high-pass: U1.D25 → C1 (series) → FILT → R1 → GND."""
    return {
        "meta": {"title": "rc-high-pass", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "C1": {"type": "passives/capacitor", "value": "100n"},
            "R1": {"type": "passives/resistor", "value": 10000},
        },
        "connections": [
            {"net": "SIG_IN", "pins": ["U1.D25", "C1.1"]},
            {"net": "FILT", "pins": ["C1.2", "R1.1"]},
            {"net": "GND", "pins": ["R1.2", "U1.GNDL"]},
        ],
    }


def _build(circuit: dict) -> NetGraph:
    return NetGraph.from_yaml_dict(circuit)


def test_single_rc_high_pass_matches():
    circuit = _single_high_pass()
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    r_place = result.placements["R1"]
    c_place = result.placements["C1"]
    assert r_place.region == c_place.region
    assert r_place.region.startswith("rc-high-pass-")
    # C on top (row 0, in series), R below (row 1, to GND).
    assert c_place.row == 0
    assert r_place.row == 1
    assert r_place.label == "rc-high-pass"


def test_high_pass_does_not_match_low_pass_topology():
    """Low-pass shape (R in-path, C-to-GND) must NOT classify as high-pass."""
    circuit = {
        "meta": {"title": "lp-not-hp", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor", "value": 10000},
            "C1": {"type": "passives/capacitor", "value": "100n"},
        },
        "connections": [
            {"net": "SIG_IN", "pins": ["U1.D25", "R1.1"]},
            {"net": "FILT", "pins": ["R1.2", "C1.1"]},
            {"net": "GND", "pins": ["C1.2", "U1.GNDL"]},
        ],
    }
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    assert result.placements["R1"].region.startswith("rc-low-pass-")


def test_rc_high_pass_placement_is_deterministic():
    circuit = _single_high_pass()
    a = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    b = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    assert a.placements == b.placements
