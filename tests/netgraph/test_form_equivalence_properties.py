"""Property-based NetGraph form-equivalence tests (TASK-135).

The NetGraph chapter ([`docs/developers/testing/netgraph.md`]) flags the
gap: the three connection forms (`pins` / `path` / `bus`) are asserted
equivalent on *fixed fixtures* (see `tests/test_netgraph.py` around the
form-equivalence tests), not over generated topologies. This module
closes the headline part of that gap — pins-vs-path equivalence — over a
Hypothesis-generated chain, and adds a clean bus-vs-pins equivalence over
a generated single multi-drop net.

What "equivalent" means here
----------------------------
Two circuits are connectivity-equivalent iff they induce the same
**canonical net membership**: the same set of pin-sets, independent of
the net *names* the author chose. That is the invariant downstream
consumers (ERC, layout, exporters) actually depend on — none of them
branch on which form the human wrote (ADR-0003).

Why membership, not ``canonical_hash()``, across forms
------------------------------------------------------
``canonical_hash()`` folds in the ``PATH_SEGMENTS`` table, which the
``path`` form populates and the ``pins`` form does not, so the hash is
deliberately **not** equal across forms even for identical connectivity.
The hash's contract is *stability within a form across parses* (the
golden-drift guard, TASK-053) — that is asserted here per form. The
cross-form invariant is membership equivalence.

Chain construction (pins vs path)
---------------------------------
A chain of ``n`` series 2-pin resistors between an MCU GPIO and the MCU
ground pin:

    U1.D13 → R1.1 R1.2 → R2.1 R2.2 → … → Rn.2 → U1.GNDL

The ``path`` form lists the whole ordered chain in one ``path:`` entry,
**terminating at a real pin** (``U1.GNDL``), not a bare net-name node.
Terminating at a real pin matters: a bare net-name terminator would make
the path emit an extra single-pin tail segment plus a merge into the
named net, which the plain ``pins`` form has no counterpart for — the two
forms would then *not* be membership-equivalent by construction. With a
real-pin terminator the path's segments are exactly the chain's
junctions, one per ``pins``-form net.
"""
from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from circuitsmith.netgraph import NetGraph

# Fast PR-time budget; large-iteration runs deferred to nightly (IDEA-014).
_SETTINGS = settings(max_examples=40, deadline=None)


def _canonical_membership(g: NetGraph) -> list[tuple[str, ...]]:
    """Name-independent connectivity: sorted set of sorted pin-tuples.

    Two graphs with this list equal induce the same connectivity
    regardless of the net names their authors chose.
    """
    return sorted(
        tuple(sorted(str(p) for p in g.pins_on_net(name)))
        for name in g.nets
    )


# ── pins vs path over a generated chain ─────────────────────────────────────


def _chain_components(n: int) -> dict:
    comps: dict[str, dict] = {"U1": {"type": "mcu/esp32"}}
    for i in range(n):
        comps[f"R{i + 1}"] = {"type": "passives/resistor", "value": 220}
    return comps


def _chain_path_circuit(n: int) -> dict:
    """The chain as a single ``path:`` terminating at a real pin."""
    tokens = ["U1.D13"]
    for i in range(n):
        tokens.append(f"R{i + 1}.1")
        tokens.append(f"R{i + 1}.2")
    tokens.append("U1.GNDL")
    return {
        "meta": {"title": "chain-path", "target": "esp32"},
        "components": _chain_components(n),
        "connections": [{"net": "CHAIN", "path": tokens}],
    }


def _chain_pins_circuit(n: int) -> dict:
    """The same chain as one ``pins:`` net per junction.

    Junctions, left to right:
      J0 = {U1.D13, R1.1}
      Ji = {Ri.2, R(i+1).1}   for 1 <= i < n
      Jn = {Rn.2, U1.GNDL}
    """
    connections: list[dict] = [{"net": "J0", "pins": ["U1.D13", "R1.1"]}]
    for i in range(1, n):
        connections.append(
            {"net": f"J{i}", "pins": [f"R{i}.2", f"R{i + 1}.1"]}
        )
    connections.append({"net": f"J{n}", "pins": [f"R{n}.2", "U1.GNDL"]})
    return {
        "meta": {"title": "chain-pins", "target": "esp32"},
        "components": _chain_components(n),
        "connections": connections,
    }


@_SETTINGS
@given(n=st.integers(min_value=1, max_value=5))
def test_pins_and_path_have_equal_membership(n):
    """A series chain written as ``pins:`` joins vs one ``path:`` induce the
    same canonical net membership."""
    g_path = NetGraph.from_yaml_dict(_chain_path_circuit(n))
    g_pins = NetGraph.from_yaml_dict(_chain_pins_circuit(n))
    assert _canonical_membership(g_path) == _canonical_membership(g_pins)


@_SETTINGS
@given(n=st.integers(min_value=1, max_value=5))
def test_each_form_hash_is_stable_across_parses(n):
    """``canonical_hash()`` is stable across two parses of each form.

    (The hash is *not* asserted equal across forms — see module docstring;
    the ``path`` form carries a PATH_SEGMENTS section the ``pins`` form
    lacks. This pins the within-form determinism contract instead.)
    """
    path = _chain_path_circuit(n)
    pins = _chain_pins_circuit(n)
    assert (
        NetGraph.from_yaml_dict(path).canonical_hash()
        == NetGraph.from_yaml_dict(path).canonical_hash()
    )
    assert (
        NetGraph.from_yaml_dict(pins).canonical_hash()
        == NetGraph.from_yaml_dict(pins).canonical_hash()
    )


# ── bus vs pins over a generated single multi-drop net ──────────────────────
#
# A `bus:` net collapses backbone + taps into one entry, so it is
# connectivity-equivalent to a single `pins:` net listing the same
# devices. This is a star/multi-drop topology (one net, many pins) — a
# different shape from the chain above, included because it composes
# cleanly. The split between backbone and taps is Hypothesis-varied; it is
# purely a rendering hint (`bus_backbone_count`) and must not change the
# net's membership.


def _bus_devices(n: int) -> list[str]:
    """`n` sensor pins plus the MCU master, as REF.PIN tokens."""
    pins = ["U1.D21"]
    for i in range(n):
        pins.append(f"IC{i + 1}.SDA")
    return pins


def _bus_components(n: int) -> dict:
    comps: dict[str, dict] = {"U1": {"type": "mcu/esp32"}}
    for i in range(n):
        comps[f"IC{i + 1}"] = {"type": "sensors/bme280"}
    return comps


@_SETTINGS
@given(data=st.data())
def test_bus_and_pins_have_equal_membership(data):
    """A multi-drop net as ``bus:`` (backbone + taps) vs one ``pins:`` net
    induce the same canonical net membership, for any backbone/tap split."""
    n = data.draw(st.integers(min_value=1, max_value=4))
    devices = _bus_devices(n)
    # Split point: how many of the device pins live on the backbone (the
    # rest are taps). At least the master stays on the backbone.
    split = data.draw(st.integers(min_value=1, max_value=len(devices)))
    backbone = devices[:split]
    taps = devices[split:]

    bus_circuit = {
        "meta": {"title": "bus", "target": "esp32"},
        "components": _bus_components(n),
        "connections": [
            {"net": "I2C", "bus": True, "backbone": backbone, "taps": taps}
        ],
    }
    pins_circuit = {
        "meta": {"title": "bus-as-pins", "target": "esp32"},
        "components": _bus_components(n),
        "connections": [{"net": "I2C", "pins": devices}],
    }
    g_bus = NetGraph.from_yaml_dict(bus_circuit)
    g_pins = NetGraph.from_yaml_dict(pins_circuit)
    assert _canonical_membership(g_bus) == _canonical_membership(g_pins)
