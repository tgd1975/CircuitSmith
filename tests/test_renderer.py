"""
Renderer tests for TASK-012.

Covers the four acceptance criteria:
  1. Path-agnostic CLI args (no hard-coded paths).
  2. Pipeline halts on schema/kernel/rubric error with structured diagnostics.
  3. A representative shipped-circuit-like fixture renders rubric-green.
  4. meta.yml sidecar carries rubric scores + advisory metrics.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from circuit.renderer import RenderError, _main, render


def _write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _esp32_circuit_yaml() -> str:
    return (
        "meta:\n"
        "  title: ESP32 LED demo\n"
        "  target: esp32\n"
        "components:\n"
        "  U1:  { type: mcu/esp32 }\n"
        "  R1:  { type: passives/resistor, value: 220 }\n"
        "  D1:  { type: passives/led, color: green }\n"
        "  SW1: { type: passives/pushbutton }\n"
        "connections:\n"
        "  - net: PWR_LED\n"
        "    path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]\n"
        "  - net: BTN_A\n"
        "    path: [U1.D13, SW1.1, SW1.2, GND]\n"
        "    pull: firmware\n"
        "  - net: GND\n"
        "    pins: [U1.GNDL]\n"
    )


def test_renders_clean_esp32_circuit(tmp_path: Path):
    circuit_path = tmp_path / "esp32.circuit.yml"
    _write_yaml(circuit_path, _esp32_circuit_yaml())
    out_svg = tmp_path / "build" / "esp32.svg"

    result = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    assert result.rubric.passed, result.rubric.findings
    assert out_svg.exists()
    svg_text = out_svg.read_text()
    assert svg_text.startswith("<svg")
    # Every component carries a data-ref attribute (the structural-equality
    # check from idea-001 §12 step 6).
    for ref in ("U1", "R1", "D1", "SW1"):
        assert f'data-ref="{ref}"' in svg_text


def test_layout_yaml_is_written_alongside_svg(tmp_path: Path):
    circuit_path = tmp_path / "esp32.circuit.yml"
    _write_yaml(circuit_path, _esp32_circuit_yaml())
    out_svg = tmp_path / "esp32.svg"
    result = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    layout_text = result.layout_path.read_text()
    assert layout_text.startswith("schema: layout/v1\n")
    assert "  U1: { region: mcu-center" in layout_text


def test_meta_yml_records_rubric_metrics(tmp_path: Path):
    circuit_path = tmp_path / "esp32.circuit.yml"
    _write_yaml(circuit_path, _esp32_circuit_yaml())
    out_svg = tmp_path / "esp32.svg"
    result = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    meta_text = result.meta_path.read_text()
    assert "schema: circuit-meta/v1" in meta_text
    assert "rubric:" in meta_text
    assert "overlaps:" in meta_text
    assert "wire_crossings:" in meta_text
    assert "min_label_distance:" in meta_text
    assert "density:" in meta_text
    assert "provenance:" in meta_text
    assert "ai_invoked: false" in meta_text


def test_renderer_round_trips_layout_yaml(tmp_path: Path):
    """Run the renderer twice; the second run reads the first's layout.yml."""
    circuit_path = tmp_path / "esp32.circuit.yml"
    _write_yaml(circuit_path, _esp32_circuit_yaml())
    out_svg = tmp_path / "esp32.svg"
    first = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    second = render(
        circuit_path=circuit_path,
        layout_path=first.layout_path,
        out_svg=out_svg,
    )
    assert first.layout_path.read_text() == second.layout_path.read_text()


def test_invalid_circuit_yaml_halts_with_diagnostic(tmp_path: Path):
    circuit_path = tmp_path / "bad.circuit.yml"
    _write_yaml(circuit_path, (
        "meta:\n"
        "  title: broken\n"
        "  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/does_not_exist }\n"
        "connections:\n"
        "  - net: GND\n"
        "    pins: [U1.D13]\n"
    ))
    out_svg = tmp_path / "bad.svg"
    with pytest.raises(RenderError) as exc_info:
        render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    assert exc_info.value.stage in ("circuit-schema", "kernel")
    assert "S4" in str(exc_info.value.findings[0]) or "no-profile" in str(exc_info.value)


def test_cli_path_agnostic(tmp_path: Path, capsys):
    """The CLI accepts any input/output path; no project-specific defaults."""
    circuit_path = tmp_path / "esp32.circuit.yml"
    _write_yaml(circuit_path, _esp32_circuit_yaml())
    out_svg = tmp_path / "out" / "esp32.svg"
    exit_code = _main([
        "--circuit", str(circuit_path),
        "--out",     str(out_svg),
    ])
    assert exit_code == 0
    assert out_svg.exists()


def test_cli_returns_non_zero_on_error(tmp_path: Path):
    """A schema failure surfaces as a non-zero exit code."""
    circuit_path = tmp_path / "bad.circuit.yml"
    _write_yaml(circuit_path, (
        "meta:\n"
        "  title: missing target\n"
        # `target:` missing → schema fail
        "components:\n"
        "  U1: { type: mcu/esp32 }\n"
        "connections:\n"
        "  - net: GND\n"
        "    pins: [U1.GNDL]\n"
    ))
    out_svg = tmp_path / "bad.svg"
    exit_code = _main([
        "--circuit", str(circuit_path),
        "--out",     str(out_svg),
    ])
    assert exit_code != 0


def test_module_has_no_host_project_imports():
    import re
    src = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "circuit" / "renderer.py"
    text = src.read_text()
    forbidden = [
        r"\bimport\s+scripts\b",
        r"\bfrom\s+scripts\b",
        r"\bimport\s+data\b",
        r"\bfrom\s+data\b",
        r"\bCircuitSmith\b",
    ]
    leaks = [pat for pat in forbidden if re.search(pat, text)]
    assert not leaks, f"renderer.py leaks host-project tokens: {leaks}"
