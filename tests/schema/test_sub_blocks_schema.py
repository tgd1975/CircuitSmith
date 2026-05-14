"""EPIC-014 / TASK-115 — schema extension for sub-blocks + instances."""
from __future__ import annotations

from circuitsmith.schema.validator import validate


def _profiles_stub() -> dict:
    from circuitsmith.schema.registry import Profile
    def mk(type_str: str, category: str, pin_names: list[str]) -> Profile:
        return Profile(
            type=type_str,
            file="test",
            name=type_str.split("/")[-1],
            pins=frozenset(pin_names),
            category=category,
            pins_detail={p: {} for p in pin_names},
            metadata={"kind": category},
        )
    return {
        "mcu/esp32": mk("mcu/esp32", "ic", ["D25", "GNDL"]),
        "passives/resistor": mk("passives/resistor", "resistor", ["1", "2"]),
        "passives/capacitor": mk("passives/capacitor", "capacitor", ["1", "2"]),
    }


def _rc_pair_circuit() -> dict:
    """Worked RC-pair example from IDEA-008."""
    return {
        "meta": {"title": "rc-pair", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
        },
        "sub-blocks": {
            "rc_lowpass": {
                "components": {
                    "R": {"type": "passives/resistor", "value": 10000},
                    "C": {"type": "passives/capacitor", "value": "100n"},
                },
                "ports": {
                    "signal_in": "R.1",
                    "signal_out": "R.2",
                    "gnd": "C.2",
                },
                "connections": [
                    {"net": "filtered", "pins": ["R.2", "C.1"]},
                ],
            },
        },
        "instances": {
            "FILT_A": {"sub-block": "rc_lowpass"},
            "FILT_B": {"sub-block": "rc_lowpass"},
        },
        "connections": [
            {"net": "SIG_A", "pins": ["U1.D25", "FILT_A.signal_in"]},
            {"net": "OUT_A", "pins": ["FILT_A.signal_out"]},
            {"net": "GND", "pins": ["U1.GNDL", "FILT_A.gnd", "FILT_B.gnd"]},
            {"net": "SIG_B", "pins": ["FILT_B.signal_in"]},
        ],
    }


def test_rc_pair_with_sub_blocks_validates():
    findings = validate(_rc_pair_circuit(), profiles=_profiles_stub())
    assert findings == [], findings


def test_nested_sub_block_rejected_via_schema_pattern():
    """The component-type regex `^[a-z][a-z0-9_]*/[a-z0-9_]+$` already
    rejects a sub-block name as a type (no slash). This is the structural
    line of defence — S6 in the validator is the *cross-reference* line of
    defence for cases where a sub-block happens to be named with the slash
    form (`foo/bar`)."""
    circuit = _rc_pair_circuit()
    circuit["sub-blocks"]["outer"] = {
        "components": {
            "INNER": {"type": "rc_lowpass"},  # nested ref (no slash)
        },
        "ports": {"x": "INNER.signal_in"},
    }
    findings = validate(circuit, profiles=_profiles_stub())
    # JSON Schema rejects this on the type-pattern alone.
    assert any(f.check == "schema" and "rc_lowpass" in f.message for f in findings)




def test_undeclared_sub_block_instance_rejected():
    """An instance referencing a non-existent sub-block is S7."""
    circuit = _rc_pair_circuit()
    circuit["instances"]["FILT_X"] = {"sub-block": "rc_highpass"}  # not declared
    findings = validate(circuit, profiles=_profiles_stub())
    s7 = [f for f in findings if f.check == "S7"]
    assert any("rc_highpass" in f.message for f in s7), findings


def test_undeclared_port_reference_rejected():
    """A top-level connections entry referencing `<instance>.<bad-port>` is S7."""
    circuit = _rc_pair_circuit()
    circuit["connections"].append(
        {"net": "BAD", "pins": ["FILT_A.no_such_port"]}
    )
    findings = validate(circuit, profiles=_profiles_stub())
    s7 = [f for f in findings if f.check == "S7"]
    assert any("no_such_port" in f.message for f in s7), findings


def test_flat_form_still_validates():
    """A circuit with no sub-blocks / instances must validate as today."""
    circuit = {
        "meta": {"title": "flat", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor", "value": 10000},
        },
        "connections": [
            {"net": "SIG", "pins": ["U1.D25", "R1.1"]},
            {"net": "GND", "pins": ["U1.GNDL", "R1.2"]},
        ],
    }
    assert validate(circuit, profiles=_profiles_stub()) == []


def test_mixed_flat_and_sub_block_validates():
    """Sub-block instance side-by-side with flat components works."""
    circuit = _rc_pair_circuit()
    # Add a flat resistor next to the sub-block instances.
    circuit["components"]["R_FLAT"] = {"type": "passives/resistor", "value": 220}
    circuit["connections"].append(
        {"net": "FLAT_NET", "pins": ["R_FLAT.1", "U1.D25"]}
    )
    findings = validate(circuit, profiles=_profiles_stub())
    assert findings == [], findings
