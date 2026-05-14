"""EPIC-014 / TASK-123 — active-device ERC rules E16..E18.

Each rule has a failing fixture (positive case) and a clean
negative fixture. The shared circuit base is a minimal active-
device topology that exercises the BJT / op-amp / 555 profiles
from TASK-120..122.
"""
from __future__ import annotations

from circuitsmith.erc_engine import run
from circuitsmith.netgraph import NetGraph
from circuitsmith.schema.registry import load_profiles


# ─────────────────────────────────────────────────────────────────────
# E16 — BJT pin role unset.
# ─────────────────────────────────────────────────────────────────────


def _bjt_circuit() -> dict:
    return {
        "meta": {"title": "bjt-erc", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "Q1": {"type": "actives/bjt_npn"},
        },
        "connections": [
            {"net": "BASE",  "pins": ["U1.D2", "Q1.B"]},
            {"net": "COLL",  "pins": ["U1.VIN", "Q1.C"]},
            {"net": "GND",   "pins": ["U1.GNDL", "Q1.E"]},
        ],
    }


def test_e16_clean_negative_built_in_npn():
    """v1 `actives/bjt_npn` ships with `role:` on every pin — E16
    is silent."""
    circuit = _bjt_circuit()
    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, profiles=load_profiles())
    e16 = [f for f in findings if f.check == "E16"]
    assert e16 == [], findings


def test_e16_fires_on_role_unset_profile():
    """A handcrafted BJT-category profile with no `role:` on its pins
    triggers E16."""
    profiles = dict(load_profiles())
    # Subclass-by-replacement: a synthetic profile with the right
    # category but no role keys.
    from circuitsmith.schema.registry import Profile
    bad_pins = {
        "B": {"side": "left",  "type": "SIGNAL_INPUT", "direction": "in"},
        "C": {"side": "right", "type": "POWER_INPUT",  "direction": "in"},
        "E": {"side": "right", "type": "GROUND_RETURN", "direction": "out"},
    }
    profiles["actives/bjt_legacy"] = Profile(
        type="actives/bjt_legacy",
        file="actives",
        name="bjt_legacy",
        pins=frozenset(bad_pins),
        category="transistor",
        pins_detail=bad_pins,
        metadata={"label": "Q", "kind": "transistor"},
    )
    circuit = _bjt_circuit()
    circuit["components"]["Q1"]["type"] = "actives/bjt_legacy"
    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, profiles=profiles)
    e16 = [f for f in findings if f.check == "E16"]
    assert e16, findings
    assert e16[0].ref == "Q1"
    assert "B" in e16[0].pin and "C" in e16[0].pin and "E" in e16[0].pin


# ─────────────────────────────────────────────────────────────────────
# E17 — Op-amp power pin floating.
# ─────────────────────────────────────────────────────────────────────


def _opamp_circuit(*, omit_v_plus: bool = False, omit_v_minus: bool = False) -> dict:
    conns = [
        {"net": "SIG_IN",  "pins": ["U1.D2",   "A1.IN+"]},
        {"net": "BUF_OUT", "pins": ["A1.OUT",  "A1.IN-", "U1.D4"]},
    ]
    if not omit_v_plus:
        conns.append({"net": "V_PLUS",  "pins": ["U1.VIN",  "A1.V+"]})
    if not omit_v_minus:
        conns.append({"net": "V_MINUS", "pins": ["U1.GNDL", "A1.V-"]})
    return {
        "meta": {"title": "opamp-erc", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "A1": {"type": "ic/opamp_dual_supply"},
        },
        "connections": conns,
    }


def test_e17_clean_negative_both_supplies_wired():
    circuit = _opamp_circuit()
    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, profiles=load_profiles())
    e17 = [f for f in findings if f.check == "E17"]
    assert e17 == [], findings


def test_e17_fires_on_floating_v_plus():
    circuit = _opamp_circuit(omit_v_plus=True)
    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, profiles=load_profiles())
    e17 = [f for f in findings if f.check == "E17"]
    assert e17, findings
    assert e17[0].ref == "A1"
    assert e17[0].pin == "V+"


def test_e17_fires_on_floating_v_minus():
    circuit = _opamp_circuit(omit_v_minus=True)
    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, profiles=load_profiles())
    e17 = [f for f in findings if f.check == "E17"]
    assert e17, findings
    assert e17[0].ref == "A1"
    assert e17[0].pin == "V-"


# ─────────────────────────────────────────────────────────────────────
# E18 — 555 pin-naming drift.
# ─────────────────────────────────────────────────────────────────────


def _timer_circuit(use_silicon: bool = False) -> dict:
    if use_silicon:
        connections = [
            {"net": "VCC",     "pins": ["U1.VIN",  "T1.VCC"]},
            {"net": "GND",     "pins": ["U1.GNDL", "T1.GND"]},
            {"net": "OUT_SIG", "pins": ["T1.OUT",  "U1.D4"]},
        ]
    else:
        connections = [
            {"net": "VCC",     "pins": ["U1.VIN",  "T1.8"]},
            {"net": "GND",     "pins": ["U1.GNDL", "T1.1"]},
            {"net": "OUT_SIG", "pins": ["T1.3",    "U1.D4"]},
        ]
    return {
        "meta": {"title": "555-erc", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "T1": {"type": "ic/555"},
        },
        "connections": connections,
    }


def test_e18_clean_negative_silkscreen_only():
    circuit = _timer_circuit(use_silicon=False)
    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, profiles=load_profiles())
    e18 = [f for f in findings if f.check == "E18"]
    assert e18 == [], findings


def test_e18_warns_on_silicon_aliases():
    circuit = _timer_circuit(use_silicon=True)
    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, profiles=load_profiles())
    e18 = [f for f in findings if f.check == "E18"]
    # Three silicon-name pin references — VCC, GND, OUT — should each
    # generate one warning.
    assert len(e18) == 3, e18
    severities = {f.severity for f in e18}
    assert severities == {"warning"}, severities
    # The suggestion text names the silkscreen replacement.
    pins_referenced = {f.pin for f in e18}
    assert pins_referenced == {"VCC", "GND", "OUT"}, pins_referenced
    # Each finding's message should name the silkscreen pin number.
    for f in e18:
        if f.pin == "VCC":
            assert "T1.8" in f.message, f.message
        elif f.pin == "GND":
            assert "T1.1" in f.message, f.message
        elif f.pin == "OUT":
            assert "T1.3" in f.message, f.message
