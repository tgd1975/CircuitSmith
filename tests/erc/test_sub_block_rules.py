"""EPIC-014 / TASK-117 — sub-block ERC rules (E11..E14) + divider (E15)."""
from __future__ import annotations


from circuitsmith.erc_engine import run as erc_run
from circuitsmith.netgraph import NetGraph
from circuitsmith.schema.registry import Profile


def _profiles_stub() -> dict[str, Profile]:
    def mk(type_str: str, category: str, pin_spec: dict, kind: str | None = None) -> Profile:
        return Profile(
            type=type_str,
            file="test",
            name=type_str.split("/")[-1],
            pins=frozenset(pin_spec),
            category=category,
            pins_detail=pin_spec,
            metadata={"kind": kind or category},
        )
    return {
        "mcu/esp32": mk("mcu/esp32", "ic", {
            "D25": {"side": "left", "type": "GPIO", "direction": "bidir"},
            "V33": {"side": "right", "type": "POWER", "direction": "in"},
            "GNDL": {"side": "left", "type": "GROUND", "direction": "in"},
        }),
        "passives/resistor": mk("passives/resistor", "resistor", {
            "1": {"side": "left", "type": "TERMINAL", "direction": "bidir"},
            "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
        }),
        "passives/capacitor": mk("passives/capacitor", "capacitor", {
            "1": {"side": "left", "type": "TERMINAL", "direction": "bidir"},
            "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
        }),
    }


def _wired_sub_block_circuit() -> dict:
    """All three ports wired — should be ERC-clean for E11..E14."""
    return {
        "meta": {"title": "wired", "target": "esp32"},
        "components": {"U1": {"type": "mcu/esp32"}},
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
        },
        "connections": [
            {"net": "SIG", "pins": ["U1.D25", "FILT_A.signal_in"]},
            {"net": "OUT", "pins": ["FILT_A.signal_out", "U1.V33"]},
            {"net": "GND", "pins": ["U1.GNDL", "FILT_A.gnd"]},
        ],
    }


def _run(circuit: dict) -> list:
    g = NetGraph.from_yaml_dict(circuit)
    return erc_run(g, circuit, profiles=_profiles_stub())


# ── E11: port not wired ─────────────────────────────────────────────────────


def test_e11_fires_when_port_not_wired():
    c = _wired_sub_block_circuit()
    # Drop the OUT net so FILT_A.signal_out is left floating.
    c["connections"] = [e for e in c["connections"] if e["net"] != "OUT"]
    findings = _run(c)
    e11 = [f for f in findings if f.check == "E11"]
    assert len(e11) == 1
    assert "signal_out" in e11[0].pin


def test_e11_clean_when_all_ports_wired():
    findings = _run(_wired_sub_block_circuit())
    assert [f for f in findings if f.check == "E11"] == []


# ── E12: declared but never instantiated ────────────────────────────────────


def test_e12_warns_on_unused_sub_block():
    c = _wired_sub_block_circuit()
    c["sub-blocks"]["unused_sb"] = c["sub-blocks"]["rc_lowpass"]
    findings = _run(c)
    e12 = [f for f in findings if f.check == "E12"]
    assert len(e12) == 1
    assert e12[0].ref == "unused_sb"
    assert e12[0].severity == "warning"


def test_e12_clean_when_every_sub_block_instantiated():
    findings = _run(_wired_sub_block_circuit())
    assert [f for f in findings if f.check == "E12"] == []


# ── E13: refdes collision ───────────────────────────────────────────────────


def test_e13_fires_on_flat_refdes_collision():
    c = _wired_sub_block_circuit()
    # The flattener mints R_FILT_A — pre-populate that name with a flat
    # component to force collision.
    c["components"]["R_FILT_A"] = {"type": "passives/resistor", "value": 1}
    # We must run ERC on the original (un-flattened) circuit, but the
    # NetGraph flatten path will raise. Run ERC alone using a graph built
    # from a synthetic flat shadow that avoids the collision in the
    # netgraph layer (E13 is the cross-check the netgraph can't make).
    # In practice, callers pass the un-flattened dict to erc.run and a
    # flattened NetGraph from from_yaml_dict — but from_yaml_dict will
    # fail first. Verify the check itself directly against a synthesised
    # flat graph.
    from circuitsmith.erc_engine import _check_E13, _Context
    flat_graph = NetGraph.from_yaml_dict({
        "meta": c["meta"],
        "components": c["components"],
        "connections": [
            {"net": "GND", "pins": ["U1.GNDL", "R_FILT_A.1"]},
        ],
    })
    ctx = _Context.build(graph=flat_graph, circuit=c, profiles=_profiles_stub())
    findings = _check_E13(ctx)
    assert len(findings) == 1
    assert findings[0].ref == "R_FILT_A"


def test_e13_clean_when_no_collision():
    findings = _run(_wired_sub_block_circuit())
    assert [f for f in findings if f.check == "E13"] == []


# ── E14: instance port double-driven ────────────────────────────────────────


def test_e14_fires_when_port_appears_on_two_distinct_nets():
    c = _wired_sub_block_circuit()
    # Re-target the existing SIG net's signal_in reference onto a new net
    # AND keep the original SIG entry, producing two distinct nets that
    # both reference FILT_A.signal_in. Wire the new net to U1.D25 so the
    # circuit still passes structural checks.
    c["connections"].append(
        {"net": "OTHER", "pins": ["FILT_A.signal_in", "U1.GNDL"]}
    )
    findings = _run(c)
    e14 = [f for f in findings if f.check == "E14"]
    assert len(e14) == 1
    assert "signal_in" in e14[0].pin


def test_e14_clean_when_each_port_on_one_net():
    findings = _run(_wired_sub_block_circuit())
    assert [f for f in findings if f.check == "E14"] == []


# ── E15: voltage-divider ambiguous ──────────────────────────────────────────


def test_e15_fires_on_unhinted_rr_divider():
    c = {
        "meta": {"title": "amb-divider", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor", "value": 10000},
            "R2": {"type": "passives/resistor", "value": 10000},
        },
        "connections": [
            {"net": "V33", "pins": ["U1.V33", "R1.1"]},
            {"net": "BIAS", "pins": ["R1.2", "R2.1"]},
            {"net": "GND", "pins": ["U1.GNDL", "R2.2"]},
        ],
    }
    findings = _run(c)
    e15 = [f for f in findings if f.check == "E15"]
    assert len(e15) == 1
    assert e15[0].severity == "warning"
    assert "BIAS" in e15[0].net


def test_e15_silent_with_vref_tap():
    c = {
        "meta": {"title": "hinted-divider", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor", "value": 10000},
            "R2": {"type": "passives/resistor", "value": 10000},
        },
        "connections": [
            {"net": "V33", "pins": ["U1.V33", "R1.1"]},
            {"net": "VREF", "pins": ["R1.2", "R2.1"]},
            {"net": "GND", "pins": ["U1.GNDL", "R2.2"]},
        ],
    }
    findings = _run(c)
    assert [f for f in findings if f.check == "E15"] == []
