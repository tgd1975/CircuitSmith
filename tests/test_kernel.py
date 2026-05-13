"""
Layout-kernel tests for TASK-009.

Covers the four acceptance criteria:

1. Produces a deterministic layout.yml for circuits resembling the
   shipped esp32/nrf52840 targets (synthetic fixtures built inline,
   pending TASK-014's real .circuit.yml files).
2. Two runs of the kernel against the same NetGraph produce
   byte-identical layout.yml output.
3. Adding one component to a circuit changes exactly one line in
   layout.yml; all other slot assignments are byte-identical.
4. Unsupported topology produces a `no-canonical-rule` escalation
   naming the offending component.
"""
from __future__ import annotations

import pytest

from circuitsmith.layout import EscalationError, place, render_layout_yaml
from circuitsmith.netgraph import NetGraph


# ── Profile stubs (minimal, dict-shaped) ─────────────────────────────────


def _profiles_for_test() -> dict:
    """A registry the kernel can consult — keyed by `type:` string."""
    return {
        "mcu/esp32": {
            "category": "ic",
            "pins": {
                "D13": {"side": "left",  "type": "GPIO",   "direction": "bidir"},
                "D25": {"side": "left",  "type": "GPIO",   "direction": "bidir"},
                "D21": {"side": "right", "type": "GPIO",   "direction": "bidir"},
                "D22": {"side": "right", "type": "GPIO",   "direction": "bidir"},
                "VIN":  {"side": "left",  "type": "POWER",  "direction": "in"},
                "V33":  {"side": "right", "type": "POWER",  "direction": "in"},
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
        "passives/led": {
            "category": "led",
            "pins": {
                "A": {"side": "left",  "type": "TERMINAL", "direction": "in"},
                "K": {"side": "right", "type": "TERMINAL", "direction": "in"},
            },
        },
        "passives/capacitor": {
            "category": "capacitor",
            "pins": {
                "1": {"side": "left",  "type": "TERMINAL", "direction": "bidir"},
                "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
            },
        },
        "passives/pushbutton": {
            "category": "pushbutton",
            "pins": {
                "1": {"side": "left",  "type": "TERMINAL", "direction": "bidir"},
                "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
            },
        },
        "sensors/bme280": {
            "category": "sensor",
            "pins": {
                "SDA": {"side": "left",  "type": "GPIO",   "direction": "bidir"},
                "SCL": {"side": "left",  "type": "GPIO",   "direction": "bidir"},
                "VCC": {"side": "left",  "type": "POWER",  "direction": "in"},
                "GND": {"side": "right", "type": "GROUND", "direction": "in"},
            },
        },
        "connectors/usb_c": {
            "category": "usb_connector",
            "pins": {
                "VBUS": {"side": "bottom", "type": "POWER",  "direction": "in"},
                "GND":  {"side": "bottom", "type": "GROUND", "direction": "in"},
            },
        },
    }


# ── Fixtures ─────────────────────────────────────────────────────────────


def _esp32_led_button_circuit() -> dict:
    """ESP32 + LED with resistor on right + button on left."""
    return {
        "meta": {"title": "esp32 demo", "target": "esp32"},
        "components": {
            "U1":  {"type": "mcu/esp32"},
            "R1":  {"type": "passives/resistor", "value": 220},
            "D1":  {"type": "passives/led",      "color": "green"},
            "SW1": {"type": "passives/pushbutton"},
        },
        "connections": [
            {"net": "PWR_LED", "path": ["U1.D25", "R1.1", "R1.2", "D1.A", "D1.K", "GND"]},
            {"net": "BTN_A",   "path": ["U1.D13", "SW1.1", "SW1.2", "GND"], "pull": "firmware"},
            {"net": "GND",     "pins": ["U1.GNDL"]},
        ],
    }


def _esp32_led_button_circuit_plus_led() -> dict:
    """Same as _esp32_led_button_circuit, plus one extra LED+resistor pair."""
    c = _esp32_led_button_circuit()
    c["components"]["R2"] = {"type": "passives/resistor", "value": 220}
    c["components"]["D2"] = {"type": "passives/led", "color": "red"}
    c["connections"].append(
        {"net": "PWR_LED2", "path": ["U1.D21", "R2.1", "R2.2", "D2.A", "D2.K", "GND"]}
    )
    return c


def _build(circuit: dict) -> NetGraph:
    return NetGraph.from_yaml_dict(circuit)


# ── 1. Deterministic output for an esp32-like target ─────────────────────


def test_produces_layout_for_esp32_like_circuit():
    circuit = _esp32_led_button_circuit()
    result = place(
        circuit=circuit,
        graph=_build(circuit),
        profiles=_profiles_for_test(),
    )
    assert set(result.placements) == {"U1", "R1", "D1", "SW1"}
    # MCU is anchored at the centre.
    assert result.placements["U1"].region == "mcu-center"
    # LED on left column (D25 is on the left pin side).
    assert result.placements["D1"].region == "left-column"
    # Button on left column (D13 is on the left pin side).
    assert result.placements["SW1"].region == "left-column"
    # Resistor is attached to the LED; region is inherited from the anchor
    # so the layout-schema's `region: required` invariant holds.
    assert result.placements["R1"].attached_to == "D1"
    assert result.placements["R1"].region == result.placements["D1"].region


def test_produces_layout_for_nrf52840_like_circuit():
    """Use right-side pins to exercise right-column placement."""
    profiles = _profiles_for_test()
    profiles["mcu/nrf52840"] = {
        "category": "ic",
        "pins": {
            "P0_13": {"side": "right", "type": "GPIO",   "direction": "bidir"},
            "P0_14": {"side": "right", "type": "GPIO",   "direction": "bidir"},
            "GND":   {"side": "right", "type": "GROUND", "direction": "in"},
        },
    }
    circuit = {
        "meta": {"title": "nrf52840 demo", "target": "nrf52840"},
        "components": {
            "U1":  {"type": "mcu/nrf52840"},
            "R1":  {"type": "passives/resistor", "value": 220},
            "D1":  {"type": "passives/led", "color": "blue"},
        },
        "connections": [
            {"net": "PWR_LED", "path": ["U1.P0_13", "R1.1", "R1.2", "D1.A", "D1.K", "GND"]},
            {"net": "GND",     "pins": ["U1.GND"]},
        ],
    }
    result = place(circuit=circuit, graph=_build(circuit), profiles=profiles)
    assert result.placements["D1"].region == "right-column"
    assert result.placements["R1"].attached_to == "D1"


# ── 2. Byte-identical output for two runs ────────────────────────────────


def test_two_runs_produce_byte_identical_output():
    circuit = _esp32_led_button_circuit()
    a = render_layout_yaml(place(circuit=circuit, graph=_build(circuit), profiles=_profiles_for_test()))
    b = render_layout_yaml(place(circuit=circuit, graph=_build(circuit), profiles=_profiles_for_test()))
    assert a == b


def test_layout_yaml_includes_schema_header():
    circuit = _esp32_led_button_circuit()
    text = render_layout_yaml(
        place(circuit=circuit, graph=_build(circuit), profiles=_profiles_for_test())
    )
    assert text.startswith("schema: layout/v1\n")
    assert "placements:" in text


def test_topology_fingerprints_are_attached_to_every_placement():
    circuit = _esp32_led_button_circuit()
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles_for_test())
    for p in result.placements.values():
        assert p.topology_fingerprint.startswith("sha1:"), p


# ── 3. Single-line diff on incremental component addition ────────────────


def test_adding_one_led_pair_produces_minimal_diff():
    """
    Phase 6 acceptance test 5 (TASK-041) measures this. Adding a fifth LED
    must not move existing placements.
    """
    base_circuit = _esp32_led_button_circuit()
    base_result = place(
        circuit=base_circuit,
        graph=_build(base_circuit),
        profiles=_profiles_for_test(),
    )
    # Round-trip the result through layout.yml shape so the kernel re-reads it.
    prev_layout = _result_to_dict(base_result)

    updated = _esp32_led_button_circuit_plus_led()
    new_result = place(
        circuit=updated,
        graph=_build(updated),
        profiles=_profiles_for_test(),
        previous_layout=prev_layout,
    )

    # Every original component keeps its exact placement.
    for ref in ("U1", "R1", "D1", "SW1"):
        assert new_result.placements[ref] == base_result.placements[ref], (
            f"{ref} moved: {base_result.placements[ref]} → {new_result.placements[ref]}"
        )
    # The two new components placed.
    assert "D2" in new_result.placements
    assert "R2" in new_result.placements

    # layout.yml diff: exactly two new lines (D2, R2) added; no existing
    # lines changed.
    base_lines = render_layout_yaml(base_result).splitlines()
    new_lines = render_layout_yaml(new_result).splitlines()
    added = [line for line in new_lines if line not in base_lines]
    removed = [line for line in base_lines if line not in new_lines]
    assert removed == [], f"unexpected removed lines: {removed}"
    assert len(added) == 2, f"expected 2 new lines, got: {added}"


def test_topology_fingerprint_invalidates_a_drifted_placement():
    """If the LED's anchor pin changes, the placement re-runs."""
    base = _esp32_led_button_circuit()
    base_result = place(circuit=base, graph=_build(base), profiles=_profiles_for_test())
    prev_layout = _result_to_dict(base_result)

    # Same components, but the LED now driven from D21 (right side, not D25/left).
    drifted = _esp32_led_button_circuit()
    drifted["connections"][0]["path"] = ["U1.D21", "R1.1", "R1.2", "D1.A", "D1.K", "GND"]

    new_result = place(
        circuit=drifted,
        graph=_build(drifted),
        profiles=_profiles_for_test(),
        previous_layout=prev_layout,
    )
    # The LED's region should have switched sides (left → right).
    assert new_result.placements["D1"].region == "right-column", (
        f"expected re-placement after fingerprint mismatch; got {new_result.placements['D1']}"
    )
    assert new_result.placements["D1"] != base_result.placements["D1"]


# ── 4. Escalation when no canonical rule applies ────────────────────────


def test_unknown_category_raises_escalation():
    profiles = _profiles_for_test()
    profiles["passives/exotic"] = {"category": "transistor", "pins": {"1": {"side": "left"}}}
    circuit = {
        "meta": {"title": "exotic", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "Q1": {"type": "passives/exotic"},
        },
        "connections": [
            {"net": "GND", "pins": ["U1.GNDL", "Q1.1"]},
        ],
    }
    with pytest.raises(EscalationError) as exc_info:
        place(circuit=circuit, graph=_build(circuit), profiles=profiles)
    assert exc_info.value.ref == "Q1"
    assert exc_info.value.reason == "no-canonical-rule"
    assert "Q1" in str(exc_info.value)


def test_orphan_resistor_raises_escalation():
    """A resistor not paired with an LED and not on a power-class net escalates."""
    circuit = {
        "meta": {"title": "orphan resistor", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor", "value": 1000},
        },
        "connections": [
            {"net": "FOO", "pins": ["U1.D13", "R1.1"]},
            {"net": "BAR", "pins": ["R1.2", "U1.D25"]},
        ],
    }
    with pytest.raises(EscalationError) as exc_info:
        place(circuit=circuit, graph=_build(circuit), profiles=_profiles_for_test())
    assert exc_info.value.ref == "R1"
    assert exc_info.value.reason == "no-canonical-rule"


# ── Portability smoke test ──────────────────────────────────────────────


def test_layout_engine_has_no_host_project_imports():
    import re
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "src" / "circuitsmith" / "layout"
    forbidden = [
        r"\bimport\s+scripts\b",
        r"\bfrom\s+scripts\b",
        r"\bimport\s+data\b",
        r"\bfrom\s+data\b",
        r"\bCircuitSmith\b",
    ]
    for src in root.glob("*.py"):
        text = src.read_text()
        leaks = [pat for pat in forbidden if re.search(pat, text)]
        assert not leaks, f"{src} leaks host-project tokens: {leaks}"


# ── helpers ─────────────────────────────────────────────────────────────


def _result_to_dict(result) -> dict:
    """Serialise a LayoutResult into a parsed-layout.yml-shaped dict."""
    placements = {}
    for ref, p in result.placements.items():
        slot: dict = {}
        if p.region is not None:
            slot["region"] = p.region
        if p.row is not None:
            slot["row"] = p.row
        if p.col is not None:
            slot["col"] = p.col
        if p.position is not None:
            slot["position"] = p.position
        if p.step is not None:
            slot["step"] = p.step
        if p.attached_to is not None:
            slot["attached-to"] = p.attached_to
        if p.attach_step is not None:
            slot["attach-step"] = p.attach_step
        if p.label is not None:
            slot["label"] = p.label
        if p.topology_fingerprint:
            slot["topology-fingerprint"] = p.topology_fingerprint
        placements[ref] = slot
    out = {"placements": placements}
    if result.capacity_overrides:
        out["capacity-overrides"] = result.capacity_overrides
    return out
