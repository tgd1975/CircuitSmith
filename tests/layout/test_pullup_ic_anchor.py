"""EPIC-014 / TASK-130 (ADR-0017) — pull-up resistor anchors widened
to accept IC SIGNAL_INPUT pins (e.g. 555 TRIG), not just MCU GPIO /
INPUT_ONLY pins."""
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
        "passives/pushbutton": {
            "category": "button",
            "pins": {
                "1": {"side": "left",  "type": "CONTACT", "direction": "bidir"},
                "2": {"side": "right", "type": "CONTACT", "direction": "bidir"},
            },
        },
        # Minimal ic_timer-shaped profile: VCC (POWER_INPUT) on the
        # rail-side, TRIG (SIGNAL_INPUT) on the signal-side, GND
        # (GROUND_RETURN) on the return side. Real 555 has more pins.
        "ic/555_min": {
            "category": "ic_timer",
            "pins": {
                "1": {"side": "left",  "type": "GROUND_RETURN", "direction": "in"},
                "2": {"side": "left",  "type": "SIGNAL_INPUT",  "direction": "in"},
                "8": {"side": "right", "type": "POWER_INPUT",   "direction": "in"},
            },
        },
    }


def _trig_pullup_circuit() -> dict:
    return {
        "meta": {"title": "ic-pullup", "target": "esp32"},
        "components": {
            "U1":     {"type": "mcu/esp32"},
            "J1":     {"type": "mcu/esp32"},  # second board to source GND for U2.1
            "U2":     {"type": "ic/555_min"},
            "R_TRIG": {"type": "passives/resistor", "value": 10000},
            "BTN":    {"type": "passives/pushbutton"},
        },
        "connections": [
            {"net": "VCC",  "pins": ["U1.VIN", "U2.8", "R_TRIG.1"]},
            {"net": "GND",  "pins": ["U1.GNDL", "U2.1", "BTN.2"]},
            {"net": "TRIG", "pins": ["U2.2", "R_TRIG.2", "BTN.1"]},
        ],
    }


def _build(circuit: dict) -> NetGraph:
    return NetGraph.from_yaml_dict(circuit)


def test_pullup_to_ic_signal_input_anchors_to_ic_pin():
    """A pull-up between VCC and an IC SIGNAL_INPUT pin (e.g. 555 TRIG)
    anchors to that IC pin, lands in `path-of-U2.2`, and does not
    escalate. Mirrors the canonical MCU pull-up's `path-of-U1.D2` shape."""
    circuit = _trig_pullup_circuit()
    profiles = _profiles()
    result = place(circuit=circuit, graph=_build(circuit), profiles=profiles)
    r_trig = result.placements["R_TRIG"]
    assert r_trig.region == "path-of-U2.2", r_trig.region


def test_pullup_anchor_skips_rail_coincident_signal_input():
    """When the rail (VCC) net carries an unrelated IC SIGNAL_INPUT (a
    RESET tied high, in the real 555), the pull-up anchor must come
    from the resistor's *non-rail* net, not the rail. Without this
    guard the anchor would land on the wrong pin."""
    profiles = _profiles()
    # Add a fake RESET pin (SIGNAL_INPUT on the rail-side IC). The
    # rail-skip in `_shape_meta_pullup` should prevent that pin from
    # being picked as the anchor.
    profiles["ic/555_min"]["pins"]["4"] = {
        "side": "left", "type": "SIGNAL_INPUT", "direction": "in",
    }
    circuit = _trig_pullup_circuit()
    # Tie U2.4 (RESET) high on the same VCC net the pull-up's rail side
    # belongs to. R_TRIG.1 and U2.4 are both on VCC; without the
    # rail-skip, R_TRIG would anchor to U2.4 instead of U2.2.
    for conn in circuit["connections"]:
        if conn["net"] == "VCC":
            conn["pins"].append("U2.4")
    result = place(circuit=circuit, graph=_build(circuit), profiles=profiles)
    assert result.placements["R_TRIG"].region == "path-of-U2.2"
