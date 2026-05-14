"""EPIC-014 / TASK-116 — sub-block flattener."""
from __future__ import annotations

import pytest

from circuitsmith.netgraph import NetGraph, SubBlockFlattenError, flatten_sub_blocks


def _rc_lowpass_subblock() -> dict:
    return {
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
    }


def _single_instance_circuit() -> dict:
    return {
        "meta": {"title": "single", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
        },
        "sub-blocks": {
            "rc_lowpass": _rc_lowpass_subblock(),
        },
        "instances": {
            "FILT_A": {"sub-block": "rc_lowpass"},
        },
        "connections": [
            {"net": "SIG", "pins": ["U1.D25", "FILT_A.signal_in"]},
            {"net": "GND", "pins": ["U1.GNDL", "FILT_A.gnd"]},
        ],
    }


def _multi_instance_circuit() -> dict:
    c = _single_instance_circuit()
    c["instances"]["FILT_B"] = {"sub-block": "rc_lowpass"}
    c["connections"][0]["pins"].append("FILT_B.signal_in")
    c["connections"][1]["pins"].append("FILT_B.gnd")
    return c


def test_flatten_no_sub_blocks_is_identity_modulo_top_level():
    flat = {
        "meta": {"title": "flat", "target": "esp32"},
        "components": {"U1": {"type": "mcu/esp32"}},
        "connections": [{"net": "GND", "pins": ["U1.GNDL"]}],
    }
    out = flatten_sub_blocks(flat)
    assert out is flat  # no expansion needed → original returned


def test_single_instance_expansion():
    out = flatten_sub_blocks(_single_instance_circuit())
    assert "sub-blocks" not in out
    assert "instances" not in out
    # Refdes minted as <local>_<instance>: R_FILT_A, C_FILT_A.
    assert "R_FILT_A" in out["components"]
    assert "C_FILT_A" in out["components"]
    assert out["components"]["R_FILT_A"]["type"] == "passives/resistor"
    # Top-level connections rewritten — FILT_A.signal_in → R_FILT_A.1
    sig = next(c for c in out["connections"] if c["net"] == "SIG")
    assert "R_FILT_A.1" in sig["pins"]
    gnd = next(c for c in out["connections"] if c["net"] == "GND")
    assert "C_FILT_A.2" in gnd["pins"]
    # Sub-block-internal connection prefixed with instance name.
    internal = next(c for c in out["connections"] if c["net"].startswith("FILT_A__"))
    assert internal["net"] == "FILT_A__filtered"
    assert "R_FILT_A.2" in internal["pins"]
    assert "C_FILT_A.1" in internal["pins"]


def test_multi_instance_yields_distinct_refdes():
    out = flatten_sub_blocks(_multi_instance_circuit())
    assert {"R_FILT_A", "C_FILT_A", "R_FILT_B", "C_FILT_B"}.issubset(out["components"])
    # Two distinct prefixed internal nets.
    internal_nets = {c["net"] for c in out["connections"] if "__" in c["net"]}
    assert "FILT_A__filtered" in internal_nets
    assert "FILT_B__filtered" in internal_nets


def test_bom_ordering_groups_by_component_class():
    """`<local>_<instance>` minting keeps R_FILT_A and R_FILT_B adjacent."""
    out = flatten_sub_blocks(_multi_instance_circuit())
    sorted_refs = sorted(out["components"])
    # All R_* refs should be contiguous after sort.
    r_indices = [i for i, r in enumerate(sorted_refs) if r.startswith("R_")]
    assert r_indices == list(range(r_indices[0], r_indices[-1] + 1))
    c_indices = [i for i, r in enumerate(sorted_refs) if r.startswith("C_")]
    assert c_indices == list(range(c_indices[0], c_indices[-1] + 1))


def test_empty_sub_block_rejected():
    c = _single_instance_circuit()
    c["sub-blocks"]["rc_lowpass"]["components"] = {}
    with pytest.raises(SubBlockFlattenError, match="empty"):
        flatten_sub_blocks(c)


def test_undeclared_port_rejected():
    c = _single_instance_circuit()
    c["connections"].append({"net": "BAD", "pins": ["FILT_A.no_such_port"]})
    with pytest.raises(SubBlockFlattenError, match="no_such_port"):
        flatten_sub_blocks(c)


def test_undeclared_sub_block_rejected():
    c = _single_instance_circuit()
    c["instances"]["FILT_X"] = {"sub-block": "rc_highpass"}
    with pytest.raises(SubBlockFlattenError, match="rc_highpass"):
        flatten_sub_blocks(c)


def test_netgraph_round_trips_through_flattener():
    """NetGraph.from_yaml_dict transparently flattens sub-block circuits."""
    g = NetGraph.from_yaml_dict(_multi_instance_circuit())
    # All four constituent refs visible as pin owners.
    refs = {p.ref for net in g.nets.values() for p in net}
    assert {"R_FILT_A", "C_FILT_A", "R_FILT_B", "C_FILT_B"}.issubset(refs)
    # Internal nets present.
    assert "FILT_A__filtered" in g.nets
    assert "FILT_B__filtered" in g.nets


def test_flattener_is_deterministic():
    a = flatten_sub_blocks(_multi_instance_circuit())
    b = flatten_sub_blocks(_multi_instance_circuit())
    assert a == b
    # And NetGraph hashes match.
    ha = NetGraph.from_yaml_dict(_multi_instance_circuit()).canonical_hash()
    hb = NetGraph.from_yaml_dict(_multi_instance_circuit()).canonical_hash()
    assert ha == hb
