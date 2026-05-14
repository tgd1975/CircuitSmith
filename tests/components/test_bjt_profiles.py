"""EPIC-014 / TASK-120 — bjt_npn and bjt_pnp profile auto-discovery,
schema validation, per-pin `role:` annotation, and the BJT canonical-
slot kernel rule (ADR-0015)."""
from __future__ import annotations

from circuitsmith.schema.registry import load_profiles
from circuitsmith.schema.validator import validate


def _bjt_switch_circuit(bjt_type: str = "actives/bjt_npn") -> dict:
    """Worked NPN low-side switch driving an LED indicator.

    The fixture exercises the v1 kernel's BJT rule plus the
    base-drive resistor pairing (`RULE_RESISTOR_WITH_BJT`) — the
    canonical pattern named in ADR-0015's *Decision* section.
    """
    return {
        "meta": {"title": "bjt-switch", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "Q1": {"type": bjt_type},
            "R_B": {"type": "passives/resistor", "value": 10000},
            "R_L": {"type": "passives/resistor", "value": 220},
            "D1": {"type": "passives/led", "color": "red"},
        },
        "connections": [
            {"net": "BASE_DRIVE",
             "path": ["U1.D2", "R_B.1", "R_B.2", "Q1.B"]},
            {"net": "LOAD",
             "path": ["U1.VIN", "R_L.1", "R_L.2", "D1.A", "D1.K", "Q1.C"]},
            {"net": "GND",
             "pins": ["Q1.E", "U1.GNDL"]},
        ],
    }


def test_bjt_profiles_discovered():
    """Registry auto-discovery picks up actives.py without per-file
    registration."""
    profiles = load_profiles()
    assert "actives/bjt_npn" in profiles, sorted(profiles)
    assert "actives/bjt_pnp" in profiles, sorted(profiles)


def test_bjt_npn_pin_shape():
    profiles = load_profiles()
    prof = profiles["actives/bjt_npn"]
    assert prof.category == "transistor"
    assert prof.pins == frozenset({"B", "C", "E"})
    # Per-pin role: live on the same dict as side/type/direction
    # (no separate metadata.bjt_terminals map per the EPIC-014
    # frozen-decisions table).
    assert prof.pins_detail["B"]["role"] == "base"
    assert prof.pins_detail["C"]["role"] == "collector"
    assert prof.pins_detail["E"]["role"] == "emitter"
    assert prof.metadata["symbol"] == "Bjt"


def test_bjt_pnp_pin_shape():
    profiles = load_profiles()
    prof = profiles["actives/bjt_pnp"]
    assert prof.category == "transistor"
    assert prof.pins == frozenset({"B", "C", "E"})
    assert prof.pins_detail["B"]["role"] == "base"
    assert prof.pins_detail["C"]["role"] == "collector"
    assert prof.pins_detail["E"]["role"] == "emitter"
    assert prof.metadata["symbol"] == "BjtPnp"


def test_bjt_circuit_validates_no_s4_or_s5():
    """A circuit referencing a BJT profile validates clean — no
    component-type-unknown (S4) or pin-reference-unknown (S5)
    findings."""
    findings = validate(_bjt_switch_circuit(), profiles=load_profiles())
    assert findings == [], findings


def test_bjt_pnp_circuit_validates():
    findings = validate(_bjt_switch_circuit("actives/bjt_pnp"),
                         profiles=load_profiles())
    assert findings == [], findings


def test_bjt_kernel_placement():
    """ADR-0015 — BJT lands in right-column at next-free row, base-drive
    resistor attaches to it. Collector and emitter resistors are NOT
    attached (would cause rubric overlaps if they were)."""
    from circuitsmith.layout.kernel import place
    from circuitsmith.netgraph import NetGraph

    circuit = _bjt_switch_circuit()
    graph = NetGraph.from_yaml_dict(circuit)
    result = place(circuit=circuit, graph=graph, profiles=load_profiles())

    q1 = result.placements["Q1"]
    assert q1.region == "right-column"
    assert q1.row == 0

    r_b = result.placements["R_B"]
    assert r_b.attached_to == "Q1"

    # R_L is on the LED's path, not the BJT's base — it must attach
    # to the LED, not to Q1.
    r_l = result.placements["R_L"]
    assert r_l.attached_to == "D1"
