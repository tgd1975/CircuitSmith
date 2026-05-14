"""EPIC-014 / TASK-111 — kernel canonical rule: R + C low-pass."""
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


def _single_low_pass() -> dict:
    """One RC low-pass: U1.D25 → R1 → FILT → C1 → GND."""
    return {
        "meta": {"title": "rc-low-pass", "target": "esp32"},
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


def _build(circuit: dict) -> NetGraph:
    return NetGraph.from_yaml_dict(circuit)


def test_single_rc_low_pass_matches():
    circuit = _single_low_pass()
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    r_place = result.placements["R1"]
    c_place = result.placements["C1"]
    assert r_place.region == c_place.region
    assert r_place.region.startswith("rc-low-pass-")
    # R on top (row 0), C below (row 1).
    assert r_place.row == 0
    assert c_place.row == 1
    assert r_place.label == "rc-low-pass"


def test_rc_low_pass_placement_is_deterministic():
    circuit = _single_low_pass()
    a = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    b = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    assert a.placements == b.placements


def test_rc_low_pass_pair_distinguishable_regions():
    """Two independent low-pass instances get distinct per-pair regions."""
    circuit = _single_low_pass()
    circuit["components"]["R2"] = {"type": "passives/resistor", "value": 10000}
    circuit["components"]["C2"] = {"type": "passives/capacitor", "value": "100n"}
    circuit["connections"][0]["pins"].append("R2.1")  # share signal-in net
    circuit["connections"].append(
        {"net": "FILT2", "pins": ["R2.2", "C2.1"]}
    )
    circuit["connections"][2]["pins"].append("C2.2")  # share GND
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    region_a = result.placements["R1"].region
    region_b = result.placements["R2"].region
    assert region_a != region_b
    assert result.placements["C1"].region == region_a
    assert result.placements["C2"].region == region_b


def test_rc_low_pass_fingerprint_invariant_across_pair():
    """Both halves share the same rule but their own shape-meta + fingerprint."""
    circuit = _single_low_pass()
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    # Both halves carry sha1: prefixed fingerprints.
    assert result.placements["R1"].topology_fingerprint.startswith("sha1:")
    assert result.placements["C1"].topology_fingerprint.startswith("sha1:")
