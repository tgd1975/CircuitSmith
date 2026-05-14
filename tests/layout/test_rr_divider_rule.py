"""EPIC-014 / TASK-114 — kernel canonical rule: R + R voltage divider."""
from __future__ import annotations

from circuitsmith.layout import place
from circuitsmith.netgraph import NetGraph


def _profiles() -> dict:
    return {
        "mcu/esp32": {
            "category": "ic",
            "pins": {
                "ADC0": {"side": "right", "type": "GPIO", "direction": "bidir"},
                "V33": {"side": "right", "type": "POWER", "direction": "in"},
                "GNDL": {"side": "left", "type": "GROUND", "direction": "in"},
            },
        },
        "passives/resistor": {
            "category": "resistor",
            "pins": {
                "1": {"side": "left", "type": "TERMINAL", "direction": "bidir"},
                "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
            },
        },
    }


def _divider(tap_name: str = "VREF", role: bool = False) -> dict:
    components = {
        "U1": {"type": "mcu/esp32"},
        "R1": {"type": "passives/resistor", "value": 10000},
        "R2": {"type": "passives/resistor", "value": 10000},
    }
    if role:
        components["R1"]["role"] = "divider"
    return {
        "meta": {"title": "divider", "target": "esp32"},
        "components": components,
        "connections": [
            {"net": "V33", "pins": ["U1.V33", "R1.1"]},
            {"net": tap_name, "pins": ["R1.2", "R2.1", "U1.ADC0"]},
            {"net": "GND", "pins": ["R2.2", "U1.GNDL"]},
        ],
    }


def _build(circuit: dict) -> NetGraph:
    return NetGraph.from_yaml_dict(circuit)


def test_divider_matches_with_vref_tap():
    circuit = _divider(tap_name="VREF")
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    r1 = result.placements["R1"]
    r2 = result.placements["R2"]
    assert r1.region == r2.region == "divider-VREF"
    assert r1.label == "divider"
    assert r1.row == 0
    assert r2.row == 1


def test_divider_tap_regex_is_case_insensitive():
    for tap in ("VREF", "vref", "Vref", "vREF", "sense", "Sense", "ADC_X", "DIV0", "TAP1"):
        circuit = _divider(tap_name=tap)
        result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
        assert result.placements["R1"].region == f"divider-{tap}", tap


def test_divider_matches_with_role_annotation_when_tap_name_unconventional():
    circuit = _divider(tap_name="BIAS", role=True)
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    assert result.placements["R1"].region == "divider-BIAS"


def test_divider_collect_escalations_does_not_treat_unhinted_as_divider():
    """Unhinted R+R rail-to-GND topology must not silently produce a
    `divider-…` region — the rule only fires when the discriminator is
    satisfied."""
    circuit = _divider(tap_name="BIAS", role=False)
    result = place(
        circuit=circuit,
        graph=_build(circuit),
        profiles=_profiles(),
        collect_escalations=True,
    )
    for ref in ("R1", "R2"):
        if ref in result.placements:
            assert not result.placements[ref].region.startswith("divider-"), (
                f"{ref} got divider region without a discriminator hint"
            )


def test_divider_both_hints_present_no_duplicate_placement():
    """Tap-name hint AND role annotation: still one divider placement."""
    circuit = _divider(tap_name="VREF", role=True)
    result = place(circuit=circuit, graph=_build(circuit), profiles=_profiles())
    assert result.placements["R1"].region == "divider-VREF"
    assert result.placements["R2"].region == "divider-VREF"
