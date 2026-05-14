"""EPIC-014 / TASK-122 — `ic/opamp_dual_supply` profile: symbolic
pin keys (IN+ / IN- / OUT / V+ / V-), no `alt:` aliases, power-pin
direction invariant, and the shared generic-IC kernel rule."""
from __future__ import annotations

from circuitsmith.schema.registry import load_profiles
from circuitsmith.schema.validator import validate


def _opamp_buffer_circuit() -> dict:
    """Non-inverting buffer — single-net feedback collapses
    A1.OUT, A1.IN-, U1.D4 onto BUF_OUT so the multi-net-pin ERC
    check (E10) does not fire."""
    return {
        "meta": {"title": "opamp-buf", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "A1": {"type": "ic/opamp_dual_supply"},
        },
        "connections": [
            {"net": "V_PLUS",  "pins": ["U1.VIN",  "A1.V+"]},
            {"net": "V_MINUS", "pins": ["U1.GNDL", "A1.V-"]},
            {"net": "SIG_IN",  "pins": ["U1.D2",   "A1.IN+"]},
            {"net": "BUF_OUT", "pins": ["A1.OUT",  "A1.IN-", "U1.D4"]},
        ],
    }


def test_opamp_profile_discovered():
    profiles = load_profiles()
    assert "ic/opamp_dual_supply" in profiles, sorted(profiles)
    # Registry override path: the auto-derived name leaks nowhere.
    assert "ics/ic_opamp_dual_supply" not in profiles


def test_opamp_pin_shape_symbolic_keys():
    profiles = load_profiles()
    prof = profiles["ic/opamp_dual_supply"]
    assert prof.category == "ic_opamp"
    assert prof.pins == frozenset({"IN+", "IN-", "OUT", "V+", "V-"})
    assert prof.metadata["symbol"] == "Opamp"
    # Power pins are unconditionally `direction: in` — never `bidir`.
    # The power-pin-floating ERC rule (TASK-123) reads this invariant.
    assert prof.pins_detail["V+"]["direction"] == "in"
    assert prof.pins_detail["V-"]["direction"] == "in"
    assert prof.pins_detail["V+"]["type"] == "POWER_INPUT"
    assert prof.pins_detail["V-"]["type"] == "POWER_INPUT"
    # Symbolic-pin profiles do not carry `alt:` lists — they ARE the
    # canonical form.
    for pin in ("IN+", "IN-", "OUT", "V+", "V-"):
        assert "alt" not in prof.pins_detail[pin]


def test_opamp_circuit_validates():
    findings = validate(_opamp_buffer_circuit(), profiles=load_profiles())
    assert findings == [], findings


def test_opamp_special_pin_chars_resolve():
    """A1.IN+ / A1.V- contain `+` / `-` — the schema's pin-token
    pattern allows them, and the post-schema validator does the same."""
    circuit = _opamp_buffer_circuit()
    # Just exercise both: SIG_IN already uses IN+; V_MINUS uses V-.
    findings = validate(circuit, profiles=load_profiles())
    s5 = [f for f in findings if f.check == "S5"]
    assert s5 == [], s5


def test_opamp_kernel_placement():
    """Generic-IC rule lands the op-amp in a side column. With two
    left pins (IN+, IN-), one right (OUT), and two on top/bottom
    (V+, V-), the dominant-side heuristic resolves to `left`."""
    from circuitsmith.layout.kernel import place
    from circuitsmith.netgraph import NetGraph

    circuit = _opamp_buffer_circuit()
    graph = NetGraph.from_yaml_dict(circuit)
    result = place(circuit=circuit, graph=graph, profiles=load_profiles())

    a1 = result.placements["A1"]
    assert a1.region == "left-column"
    assert a1.row == 0
