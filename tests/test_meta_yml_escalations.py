"""
meta.yml escalations tests for TASK-057.

The `provenance.escalations` block is the corpus the Phase 2b trigger
gate (TASK-058) reads. This test suite verifies one entry per category
is emitted on a deliberately-failing fixture, and the clean-run path
emits `escalations: []`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from circuit.renderer import RenderError, render


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_clean_run_emits_empty_escalations(tmp_path: Path):
    circuit_path = tmp_path / "clean.circuit.yml"
    _write(circuit_path, (
        "meta:\n"
        "  title: Clean run\n"
        "  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/esp32 }\n"
        "  R1: { type: passives/resistor, value: 220 }\n"
        "  D1: { type: passives/led, color: green }\n"
        "connections:\n"
        "  - net: PWR_LED\n"
        "    path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]\n"
        "  - net: GND\n"
        "    pins: [U1.GNDL]\n"
    ))
    result = render(circuit_path=circuit_path, layout_path=None, out_svg=tmp_path / "out.svg")
    meta = result.meta_path.read_text()
    assert "escalations: []" in meta, meta


def test_kernel_no_canonical_rule_escalation_recorded(tmp_path: Path):
    """A component with no slot-table rule emits a no-canonical-rule entry."""
    circuit_path = tmp_path / "exotic.circuit.yml"
    # passives/piezo has category=resistor in the shipped profile, but a
    # standalone resistor with no LED partner and no power-class terminal
    # is the classic no-canonical-rule case.
    _write(circuit_path, (
        "meta:\n"
        "  title: orphan resistor\n"
        "  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/esp32 }\n"
        "  R1: { type: passives/resistor, value: 1000 }\n"
        "connections:\n"
        "  - net: FOO\n"
        "    pins: [U1.D13, R1.1]\n"
        "  - net: BAR\n"
        "    pins: [U1.D25, R1.2]\n"
    ))
    with pytest.raises(RenderError):
        render(circuit_path=circuit_path, layout_path=None, out_svg=tmp_path / "out.svg")
    meta_path = tmp_path / "out.meta.yml"
    assert meta_path.exists(), "meta.yml must be written even on kernel escalation"
    meta = meta_path.read_text()
    assert "state: incomplete" in meta
    assert "category: no-canonical-rule" in meta
    assert "component: R1" in meta


def test_rubric_fail_escalation_recorded(tmp_path: Path):
    """A label that exceeds the budget triggers `rubric-fail-labels-fit`."""
    # Build a circuit with a very long ref name to exceed DEFAULT_LABEL_BUDGET.
    circuit_path = tmp_path / "longref.circuit.yml"
    _write(circuit_path, (
        "meta:\n"
        "  title: long ref test\n"
        "  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/esp32 }\n"
        "  RESISTOR_WITH_VERY_LONG_NAME: { type: passives/resistor, value: 220 }\n"
        "  LED_WITH_VERY_LONG_NAME:      { type: passives/led, color: green }\n"
        "connections:\n"
        "  - net: PWR_LED\n"
        "    path: [U1.D25, RESISTOR_WITH_VERY_LONG_NAME.1, RESISTOR_WITH_VERY_LONG_NAME.2, "
        "LED_WITH_VERY_LONG_NAME.A, LED_WITH_VERY_LONG_NAME.K, GND]\n"
        "  - net: GND\n"
        "    pins: [U1.GNDL]\n"
    ))
    with pytest.raises(RenderError):
        render(circuit_path=circuit_path, layout_path=None, out_svg=tmp_path / "out.svg")
    meta = (tmp_path / "out.meta.yml").read_text()
    assert "state: incomplete" in meta
    assert "category: rubric-fail-labels-fit" in meta


def test_escalations_use_known_category_enum(tmp_path: Path):
    """Every emitted category must be one of the enum values from meta.schema.json."""
    import json
    from pathlib import Path as _Path
    schema_path = (
        _Path(__file__).resolve().parents[1]
        / ".claude" / "skills" / "circuit" / "schema" / "meta.schema.json"
    )
    schema = json.loads(schema_path.read_text())
    known = set(schema["$defs"]["escalation"]["properties"]["category"]["enum"])

    # Trigger a no-canonical-rule escalation, parse meta, assert the category
    # name is in the schema's enum (forces us to keep code and schema in sync).
    circuit_path = tmp_path / "orphan.circuit.yml"
    _write(circuit_path, (
        "meta:\n  title: orphan\n  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/esp32 }\n"
        "  R1: { type: passives/resistor, value: 1000 }\n"
        "connections:\n"
        "  - net: FOO\n    pins: [U1.D13, R1.1]\n"
        "  - net: BAR\n    pins: [U1.D25, R1.2]\n"
    ))
    with pytest.raises(RenderError):
        render(circuit_path=circuit_path, layout_path=None, out_svg=tmp_path / "out.svg")
    meta = (tmp_path / "out.meta.yml").read_text()
    # Extract `category:` values from the escalations block — simple line scan.
    found = set()
    for line in meta.splitlines():
        if "category:" in line:
            cat = line.split("category:")[1].split(",")[0].strip().strip("}").strip()
            found.add(cat)
    assert found, f"no category lines found in meta: {meta}"
    assert found <= known, f"unknown categories emitted: {found - known}"
