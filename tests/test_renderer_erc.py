"""
ERC-integration tests for the renderer (TASK-023).

Covers the four acceptance criteria of TASK-023:
  - ERC runs after schema validation, before kernel invocation.
  - ERROR-level findings abort the renderer with a distinct exit code (1).
  - WARNING-level findings (notably E9 on shipped circuits) do not abort.
  - The pipeline order matches `idea-001-circuit-skill.md §Pipeline`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from circuitsmith.renderer import RenderError, _main, render


def _write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# A circuit with a missing LED resistor — triggers E2 (ERROR).
_LED_NO_RESISTOR_YAML = (
    "meta:\n"
    "  title: bad LED\n"
    "  target: esp32\n"
    "components:\n"
    "  U1: { type: mcu/esp32 }\n"
    "  D1: { type: passives/led, color: red }\n"
    "connections:\n"
    "  - net: LED\n"
    "    path: [U1.D13, D1.A, D1.K, GND]\n"
    "  - net: GND\n"
    "    pins: [U1.GNDL]\n"
    "  - net: VCC\n"
    "    pins: [U1.VIN, U1.V33]\n"
)


def test_erc_error_aborts_pipeline(tmp_path: Path):
    """E2 (LED without resistor) is ERROR; renderer aborts at the erc stage."""
    circuit_path = tmp_path / "bad.circuit.yml"
    _write_yaml(circuit_path, _LED_NO_RESISTOR_YAML)
    out_svg = tmp_path / "build" / "bad.svg"
    with pytest.raises(RenderError) as exc_info:
        render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    assert exc_info.value.stage == "erc"
    assert any(f.check == "E2" for f in exc_info.value.findings)
    assert not out_svg.exists()


def test_erc_error_cli_exit_code_distinct_from_schema(tmp_path: Path):
    """ERC errors exit 1; schema/kernel errors exit 2."""
    circuit_path = tmp_path / "bad.circuit.yml"
    _write_yaml(circuit_path, _LED_NO_RESISTOR_YAML)
    out_svg = tmp_path / "bad.svg"
    exit_code = _main([
        "--circuit", str(circuit_path),
        "--out",     str(out_svg),
    ])
    assert exit_code == 1


def test_erc_warning_does_not_abort(tmp_path: Path):
    """A circuit with only WARNING-level findings (e.g. E9) still renders."""
    yaml = (
        "meta:\n"
        "  title: ESP32 with E9 warning\n"
        "  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/esp32 }\n"
        "  J1: { type: connectors/usb_c }\n"
        "  R1: { type: passives/resistor, value: 220 }\n"
        "  D1: { type: passives/led, color: green }\n"
        "connections:\n"
        "  - net: VCC\n"
        "    pins: [J1.VBUS, U1.VIN]\n"
        "  - net: GND\n"
        "    pins: [J1.GND, U1.GNDL]\n"
        "  - net: LED\n"
        "    path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]\n"
    )
    circuit_path = tmp_path / "warn.circuit.yml"
    _write_yaml(circuit_path, yaml)
    out_svg = tmp_path / "warn.svg"
    result = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    assert out_svg.exists()
    # E9 (USB-C VBUS no diode) is WARNING on v0.1; it should surface in
    # the result but not abort.
    assert any(f.check == "E9" and f.severity == "warning" for f in result.erc_findings)


def test_erc_runs_after_schema_validation(tmp_path: Path):
    """Schema failure precedes ERC. A circuit that would fail BOTH must
    surface the schema diagnostic, not the ERC diagnostic."""
    yaml = (
        "meta:\n"
        "  title: bad\n"
        "  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/does_not_exist }\n"
        "connections:\n"
        "  - net: GND\n"
        "    pins: [U1.D13]\n"
    )
    circuit_path = tmp_path / "bad.circuit.yml"
    _write_yaml(circuit_path, yaml)
    out_svg = tmp_path / "bad.svg"
    with pytest.raises(RenderError) as exc_info:
        render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    # The schema stage is the abort site, not the ERC stage.
    assert exc_info.value.stage != "erc"


def test_render_result_carries_erc_findings(tmp_path: Path):
    """Even on a green render, the RenderResult exposes the ERC findings list."""
    yaml = (
        "meta:\n"
        "  title: green\n"
        "  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/esp32 }\n"
        "  R1: { type: passives/resistor, value: 220 }\n"
        "  D1: { type: passives/led, color: green }\n"
        "connections:\n"
        "  - net: LED\n"
        "    path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]\n"
        "  - net: GND\n"
        "    pins: [U1.GNDL]\n"
    )
    circuit_path = tmp_path / "green.circuit.yml"
    _write_yaml(circuit_path, yaml)
    out_svg = tmp_path / "green.svg"
    result = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    assert isinstance(result.erc_findings, list)
