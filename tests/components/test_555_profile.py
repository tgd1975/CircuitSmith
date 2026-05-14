"""EPIC-014 / TASK-121 — `ic/555` profile: auto-discovery via the
`metadata.type:` override mechanism, silkscreen-pin keying, silicon-
name alias resolution, and generic-IC kernel placement."""
from __future__ import annotations

from circuitsmith.schema.registry import load_profiles
from circuitsmith.schema.validator import validate


def _555_minimal_circuit(use_silicon_aliases: bool = False) -> dict:
    """Minimal 555 monostable referencing the timer via either
    silkscreen pins (`U1.1`) or silicon-name aliases (`U1.GND`)."""
    if use_silicon_aliases:
        connections = [
            {"net": "VCC",     "pins": ["U1.VIN", "T1.VCC"]},
            {"net": "GND",     "pins": ["U1.GNDL", "T1.GND"]},
            {"net": "OUT_SIG", "pins": ["T1.OUT", "U1.D4"]},
        ]
    else:
        connections = [
            {"net": "VCC",     "pins": ["U1.VIN", "T1.8"]},
            {"net": "GND",     "pins": ["U1.GNDL", "T1.1"]},
            {"net": "OUT_SIG", "pins": ["T1.3", "U1.D4"]},
        ]
    return {
        "meta": {"title": "555-min", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "T1": {"type": "ic/555"},
        },
        "connections": connections,
    }


def test_555_profile_discovered_under_ic_slash_555():
    """Registry's `metadata.type:` override remaps the
    `ics.py:ic_555` attribute to the `ic/555` registry key per
    the EPIC-014 frozen-decisions table."""
    profiles = load_profiles()
    assert "ic/555" in profiles, sorted(profiles)
    # No leakage of the auto-derived name.
    assert "ics/ic_555" not in profiles


def test_555_pin_shape_silkscreen_keys():
    profiles = load_profiles()
    prof = profiles["ic/555"]
    assert prof.category == "ic_timer"
    assert prof.pins == frozenset({"1", "2", "3", "4", "5", "6", "7", "8"})
    # `metadata.symbol` drives schemdraw element selection.
    assert prof.metadata["symbol"] == "Ic"
    # ADR-0010 — silicon names live on `alt:`.
    assert prof.pins_detail["1"]["alt"] == ["GND"]
    assert prof.pins_detail["8"]["alt"] == ["VCC"]
    assert prof.pins_detail["3"]["alt"] == ["OUT"]


def test_555_silkscreen_pin_form_validates():
    findings = validate(_555_minimal_circuit(), profiles=load_profiles())
    assert findings == [], findings


def test_555_silicon_alias_form_validates():
    """A connection referencing `T1.GND` resolves the same as `T1.1`."""
    findings = validate(
        _555_minimal_circuit(use_silicon_aliases=True),
        profiles=load_profiles(),
    )
    assert findings == [], findings


def test_555_unknown_pin_still_fails_s5():
    """Sanity — adding the alt-resolution path didn't open S5 to
    arbitrary names."""
    circuit = _555_minimal_circuit()
    circuit["connections"].append(
        {"net": "BOGUS", "pins": ["T1.TOTALLY_NOT_A_PIN"]}
    )
    findings = validate(circuit, profiles=load_profiles())
    assert any(f.check == "S5" and "TOTALLY_NOT_A_PIN" in f.message for f in findings), findings


def test_555_kernel_placement_right_column():
    """The generic-IC rule (id 17) lands the 555 in a side column.
    With seven of eight pins on the left or right, the dominant-side
    heuristic picks whichever has the four pins — for the 555 that
    happens to be both left (1, 2, 3, 4) and right (5, 6, 7, 8) tied;
    the `_first_declared_pin_side` tiebreaker picks based on the
    first net connection."""
    from circuitsmith.layout.kernel import place
    from circuitsmith.netgraph import NetGraph

    circuit = _555_minimal_circuit()
    graph = NetGraph.from_yaml_dict(circuit)
    result = place(circuit=circuit, graph=graph, profiles=load_profiles())

    t1 = result.placements["T1"]
    assert t1.region in ("left-column", "right-column"), t1
    assert t1.row == 0
