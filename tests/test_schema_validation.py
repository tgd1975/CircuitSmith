"""
Schema-validation tests for TASK-005.

Four fixture cases per the task body:
  - valid esp32 minimal circuit
  - S4: unknown-component-type reference
  - S5: unknown-pin reference on a known component
  - one well-formed instance per connection form (pins, path, bus)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from circuit.schema import validate, validate_file


def _minimal_circuit() -> dict:
    """A structurally valid esp32 + button circuit."""
    return {
        "meta": {"title": "Minimal", "target": "esp32"},
        "components": {
            "U1":  {"type": "mcu/esp32"},
            "SW1": {"type": "passives/pushbutton", "label": "BTN_A"},
        },
        "connections": [
            {"net": "BTN_A", "pins": ["U1.D13", "SW1.1"]},
            {"net": "GND",   "pins": ["U1.GNDL", "SW1.2"]},
        ],
    }


def test_valid_esp32_minimal_circuit_passes():
    assert validate(_minimal_circuit()) == []


def test_s4_unknown_component_type():
    circuit = _minimal_circuit()
    circuit["components"]["U1"]["type"] = "mcu/does_not_exist"
    findings = validate(circuit)
    assert any(f.check == "S4" for f in findings), (
        f"expected an S4 finding, got: {findings}"
    )


def test_s5_unknown_pin_reference():
    circuit = _minimal_circuit()
    circuit["connections"][0]["pins"] = ["U1.NOT_A_PIN", "SW1.1"]
    findings = validate(circuit)
    assert any(f.check == "S5" for f in findings), (
        f"expected an S5 finding, got: {findings}"
    )


def test_pins_form_validates():
    circuit = _minimal_circuit()
    assert validate(circuit) == []


def test_path_form_validates():
    circuit = {
        "meta": {"title": "Path form", "target": "esp32"},
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
        ],
    }
    findings = validate(circuit)
    assert findings == [], f"unexpected findings: {findings}"


def test_bus_form_validates():
    circuit = {
        "meta": {"title": "Bus form", "target": "esp32"},
        "components": {
            "U1":  {"type": "mcu/esp32"},
            "IC1": {"type": "sensors/bme280"},
        },
        "connections": [
            {
                "net":      "I2C_SDA",
                "bus":      True,
                "backbone": ["U1.D21", "IC1.SDA"],
                "taps":     ["IC1.SDA"],
            },
        ],
    }
    findings = validate(circuit)
    assert findings == [], f"unexpected findings: {findings}"


def test_oneof_rejects_mixed_connection_forms():
    """A net cannot declare both `pins` and `path` — the schema oneOf rejects."""
    circuit = _minimal_circuit()
    circuit["connections"] = [
        {
            "net":  "BAD",
            "pins": ["U1.D13"],
            "path": ["U1.D13", "SW1.1"],
        },
    ]
    findings = validate(circuit)
    assert any(f.check == "schema" for f in findings), (
        f"expected a schema finding for mixed connection forms: {findings}"
    )


@pytest.mark.parametrize("missing_key", ["meta", "components", "connections"])
def test_schema_requires_three_top_level_sections(missing_key):
    circuit = _minimal_circuit()
    del circuit[missing_key]
    findings = validate(circuit)
    assert any(f.check == "schema" for f in findings), (
        f"expected a schema finding when {missing_key} is missing: {findings}"
    )


def test_validate_file_loads_yaml_and_validates(tmp_path: Path):
    """`validate_file()` round-trips a real YAML fixture via ruamel.yaml."""
    yml = tmp_path / "minimal.circuit.yml"
    yml.write_text(
        "meta:\n"
        "  title: Minimal\n"
        "  target: esp32\n"
        "components:\n"
        "  U1:  { type: mcu/esp32 }\n"
        "  SW1: { type: passives/pushbutton }\n"
        "connections:\n"
        "  - net: BTN_A\n"
        "    pins: [U1.D13, SW1.1]\n"
        "  - net: GND\n"
        "    pins: [U1.GNDL, SW1.2]\n"
    )
    assert validate_file(yml) == []


def test_validate_file_surfaces_s5_for_unknown_pin(tmp_path: Path):
    yml = tmp_path / "broken.circuit.yml"
    yml.write_text(
        "meta:\n"
        "  title: Broken\n"
        "  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/esp32 }\n"
        "connections:\n"
        "  - net: GND\n"
        "    pins: [U1.NOT_A_PIN]\n"
    )
    findings = validate_file(yml)
    assert any(f.check == "S5" for f in findings), findings
