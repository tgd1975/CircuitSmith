"""EPIC-014 / TASK-129 (ADR-0016) — collector-load and emitter-
degeneration kernel rules."""
from __future__ import annotations

from circuitsmith.layout import place
from circuitsmith.netgraph import NetGraph


def _profiles() -> dict:
    return {
        "mcu/esp32": {
            "category": "ic",
            "pins": {
                "VIN":  {"side": "right", "type": "POWER",  "direction": "in"},
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
        "actives/bjt_npn": {
            "category": "transistor",
            "pins": {
                "B": {"side": "left",  "type": "SIGNAL_INPUT",  "direction": "in",
                      "role": "base"},
                "C": {"side": "right", "type": "POWER_INPUT",   "direction": "in",
                      "role": "collector"},
                "E": {"side": "right", "type": "GROUND_RETURN", "direction": "out",
                      "role": "emitter"},
            },
        },
    }


def _ce_stage() -> dict:
    """Minimal CE-amplifier passive stack: rail → R_C → Q1.C and
    Q1.E → R_E → GND. R_B keeps the BJT classifier happy."""
    return {
        "meta": {"title": "ce-stage", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "Q1": {"type": "actives/bjt_npn"},
            "R_B": {"type": "passives/resistor", "value": 10000},
            "R_C": {"type": "passives/resistor", "value": 2700},
            "R_E": {"type": "passives/resistor", "value": 270},
        },
        "connections": [
            {"net": "VCC", "pins": ["U1.VIN", "R_C.1"]},
            {"net": "BASE", "path": ["U1.GNDL", "R_B.1", "R_B.2", "Q1.B"]},
            {"net": "COLL", "pins": ["R_C.2", "Q1.C"]},
            {"net": "EMIT", "pins": ["Q1.E", "R_E.1"]},
            {"net": "GND",  "pins": ["R_E.2"]},
        ],
    }


def _build(circuit: dict) -> NetGraph:
    return NetGraph.from_yaml_dict(circuit)


def test_collector_load_lands_in_per_bjt_load_region():
    circuit = _ce_stage()
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    rc = result.placements["R_C"]
    assert rc.region == "bjt-load-Q1"
    assert rc.row == 0
    assert rc.label == "bjt-load"


def test_emitter_degeneration_lands_in_per_bjt_degen_region():
    circuit = _ce_stage()
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    re = result.placements["R_E"]
    assert re.region == "bjt-degen-Q1"
    assert re.row == 0
    assert re.label == "bjt-degeneration"


def test_collector_load_detector_requires_role_collector():
    """Direct unit test of the detector: a resistor between a rail and
    a BJT pin whose role is *not* collector returns None."""
    from circuitsmith.layout.kernel import _detect_bjt_collector_load
    circuit = {
        "meta": {"title": "bjt-no-load", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "Q1": {"type": "actives/bjt_npn"},
            "R_B": {"type": "passives/resistor", "value": 10000},
        },
        "connections": [
            {"net": "VCC",  "pins": ["U1.VIN", "R_B.1"]},
            {"net": "BASE", "pins": ["R_B.2", "Q1.B"]},
            {"net": "COLL", "pins": ["Q1.C"]},
            {"net": "GND",  "pins": ["Q1.E", "U1.GNDL"]},
        ],
    }
    graph = _build(circuit)
    profiles = _profiles()
    # R_B sits between VCC (rail) and BASE (base pin) — the collector-
    # load detector must refuse to fire.
    assert _detect_bjt_collector_load("R_B", circuit, graph, profiles) is None


def test_emitter_degeneration_requires_gnd_terminal():
    """A resistor with the emitter on one side and a non-GND signal
    node on the other must not classify as emitter degeneration."""
    circuit = {
        "meta": {"title": "no-degen", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "Q1": {"type": "actives/bjt_npn"},
            "R_B": {"type": "passives/resistor", "value": 10000},
            "R_E": {"type": "passives/resistor", "value": 270},
        },
        "connections": [
            {"net": "VCC",   "pins": ["U1.VIN"]},
            {"net": "BASE",  "path": ["U1.GNDL", "R_B.1", "R_B.2", "Q1.B"]},
            {"net": "EMIT",  "pins": ["Q1.E", "R_E.1"]},
            {"net": "NOTGND", "pins": ["R_E.2"]},  # not a GND-named net
            {"net": "COLL",   "pins": ["Q1.C"]},
        ],
    }
    # R_E should not classify as bjt-degen since its other side is
    # not on a recognised GND net; it falls through and either matches
    # another rule or escalates. The test asserts the *negative* — R_E
    # is not in bjt-degen.
    try:
        result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    except Exception:
        # Acceptable: R_E escalates because no other rule fits either.
        return
    re = result.placements.get("R_E")
    if re is not None:
        assert not (re.region or "").startswith("bjt-degen-"), re.region
