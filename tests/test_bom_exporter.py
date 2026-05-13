"""
BOM exporter — TASK-031.

Tests cover:

  - Variant grouping by category (resistor on value, LED on color, etc.)
  - Reference-designator run-length encoding within a group
  - Run-length only spans consecutive numeric suffixes within one group
  - Markdown + CSV output shapes
  - Determinism across two runs
  - KiCad `Value` column carries the bare projection (no Ω, no unit)
"""
from __future__ import annotations

from circuitsmith.export.bom_exporter import (
    _condense_refs,
    _variant_csv_value,
    _variant_display,
    _variant_key,
    export,
)
from circuitsmith.schema.registry import load_profiles


def _circuit(**components):
    return {
        "meta": {"title": "test build"},
        "components": components,
        "connections": [],
    }


def test_resistor_grouping_by_value():
    profiles = load_profiles()
    circuit = _circuit(
        R1={"type": "passives/resistor", "value": 220},
        R2={"type": "passives/resistor", "value": 220},
        R3={"type": "passives/resistor", "value": 1000},
    )
    bom_md, _ = export(circuit, profiles)
    # Two 220 Ω resistors collapse to one row; 1 kΩ is its own row.
    assert "| R1, R2 | R | 220 Ω | 2 |" in bom_md
    assert "| R3 | R | 1000 Ω | 1 |" in bom_md


def test_led_grouping_by_color():
    profiles = load_profiles()
    circuit = _circuit(
        D1={"type": "passives/led", "color": "green"},
        D2={"type": "passives/led", "color": "red"},
        D3={"type": "passives/led", "color": "green"},
        D4={"type": "passives/led", "color": "red"},
        D5={"type": "passives/led", "color": "blue"},
    )
    bom_md, _ = export(circuit, profiles)
    # D1 and D3 are non-consecutive — must render as "D1, D3", not "D1–D3".
    assert "| D1, D3 | LED | green | 2 |" in bom_md
    assert "| D2, D4 | LED | red | 2 |" in bom_md
    assert "| D5 | LED | blue | 1 |" in bom_md


def test_run_length_encoding_within_consecutive():
    refs = _condense_refs(["R1", "R2", "R3", "R5"])
    # Run of three collapses to an en-dash range; R5 is appended verbatim.
    assert refs == "R1–R3, R5"


def test_run_length_no_subrange_across_prefix():
    refs = _condense_refs(["D1", "R1", "R2", "R3"])
    assert refs == "D1, R1–R3"


def test_csv_form_one_row_per_ref():
    profiles = load_profiles()
    circuit = _circuit(
        R1={"type": "passives/resistor", "value": 220},
        R2={"type": "passives/resistor", "value": 220},
    )
    _, bom_csv = export(circuit, profiles)
    rows = bom_csv.strip().split("\n")
    # Header + 2 data rows.
    assert len(rows) == 3
    assert rows[0].startswith("Reference,Type,Value,Footprint,Datasheet,Manufacturer")
    assert rows[1].startswith("R1,passives/resistor,220,")
    assert rows[2].startswith("R2,passives/resistor,220,")


def test_csv_value_column_bare_projection():
    profiles = load_profiles()
    circuit = _circuit(
        R1={"type": "passives/resistor", "value": 220},
        D1={"type": "passives/led", "color": "green"},
        U1={"type": "mcu/esp32"},
    )
    _, bom_csv = export(circuit, profiles)
    # KiCad's importer reads `Value`; the field must not carry units (no "Ω").
    assert ",220," in bom_csv
    assert ",green," in bom_csv
    # MCU has no variant axis — Value is blank.
    assert "U1,mcu/esp32,," in bom_csv


def test_determinism_across_two_runs():
    profiles = load_profiles()
    circuit = _circuit(
        R1={"type": "passives/resistor", "value": 220},
        R2={"type": "passives/resistor", "value": 220},
        D1={"type": "passives/led", "color": "blue"},
        U1={"type": "mcu/esp32"},
    )
    first = export(circuit, profiles)
    second = export(circuit, profiles)
    assert first == second


def test_variant_key_categories():
    profiles = load_profiles()
    led = profiles["passives/led"]
    resistor = profiles["passives/resistor"]
    mcu = profiles["mcu/esp32"]
    # LED — color axis.
    assert _variant_key(led, {"color": "green"}) == "green"
    # Resistor — value axis.
    assert _variant_key(resistor, {"value": 470}) == "470"
    # MCU — no variant axis; key is empty string for grouping.
    assert _variant_key(mcu, {}) == ""


def test_markdown_title_uses_meta_title():
    profiles = load_profiles()
    circuit = {
        "meta": {"title": "ESP32 default build"},
        "components": {"U1": {"type": "mcu/esp32"}},
        "connections": [],
    }
    bom_md, _ = export(circuit, profiles)
    assert bom_md.startswith("# Bill of Materials — ESP32 default build\n")


def test_omitted_meta_title_falls_back():
    profiles = load_profiles()
    circuit = {"components": {"U1": {"type": "mcu/esp32"}}, "connections": []}
    bom_md, _ = export(circuit, profiles)
    assert bom_md.startswith("# Bill of Materials — untitled\n")


def test_led_without_color_uses_default():
    profiles = load_profiles()
    led = profiles["passives/led"]
    assert _variant_key(led, {}) == "default"
    assert _variant_display(led, {}) == ""


def test_csv_carries_metadata_columns():
    profiles = load_profiles()
    circuit = _circuit(U1={"type": "mcu/esp32"})
    _, bom_csv = export(circuit, profiles)
    # `datasheet` and `manufacturer` come from metadata.
    assert "espressif" in bom_csv.lower()
    # `footprint` is blank until the profile field lands.
    rows = bom_csv.strip().split("\n")
    fields = rows[1].split(",")
    # Reference,Type,Value,Footprint,Datasheet,Manufacturer
    assert fields[3] == ""


def test_csv_value_helper_resistor_and_led():
    profiles = load_profiles()
    assert _variant_csv_value(profiles["passives/resistor"], {"value": 4700}) == "4700"
    assert _variant_csv_value(profiles["passives/led"], {"color": "red"}) == "red"
    assert _variant_csv_value(profiles["mcu/esp32"], {}) == ""
