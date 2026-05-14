"""EPIC-014 / TASK-127 — cross-page ERC rules (E19..E22)."""
from __future__ import annotations

from circuitsmith.erc_engine import run as run_erc
from circuitsmith.netgraph import NetGraph


def _profiles_stub() -> dict:
    from circuitsmith.schema.registry import Profile
    def mk(type_str: str, category: str, pin_names: list[str]) -> "Profile":
        return Profile(
            type=type_str,
            file="test",
            name=type_str.split("/")[-1],
            pins=frozenset(pin_names),
            category=category,
            pins_detail={p: {"type": "GPIO", "direction": "in"} for p in pin_names},
            metadata={"kind": category},
        )
    return {
        "mcu/esp32":         mk("mcu/esp32",         "mcu",       ["D25", "D13", "GNDL"]),
        "passives/resistor": mk("passives/resistor", "resistor",  ["1", "2"]),
        "passives/led":      mk("passives/led",      "led",       ["A", "K"]),
    }


def _two_led_circuit() -> dict:
    return {
        "meta": {"title": "two-led", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor"},
            "D1": {"type": "passives/led", "color": "green"},
            "R2": {"type": "passives/resistor"},
            "D2": {"type": "passives/led", "color": "red"},
        },
        "connections": [
            {"net": "PWR_LED1", "pins": ["U1.D25", "R1.1"]},
            {"net": "MID1",     "pins": ["R1.2", "D1.A"]},
            {"net": "GND1",     "pins": ["D1.K", "U1.GNDL"]},
            {"net": "PWR_LED2", "pins": ["U1.D13", "R2.1"]},
            {"net": "MID2",     "pins": ["R2.2", "D2.A"]},
            {"net": "GND2",     "pins": ["D2.K", "U1.GNDL"]},
        ],
    }


def _two_page_layout(extras: dict | None = None) -> dict:
    base = {
        "schema": "layout/v1",
        "pages": [{"name": "p1"}, {"name": "p2"}],
        "placements": {
            "U1": {"region": "mcu-center", "page": "p1",
                   "topology-fingerprint": "sha1:0000aaaa"},
            "R1": {"region": "left-column", "row": 0, "page": "p1",
                   "topology-fingerprint": "sha1:1111bbbb"},
            "D1": {"region": "left-column", "row": 1, "page": "p1",
                   "topology-fingerprint": "sha1:2222cccc"},
            "R2": {"region": "right-column", "row": 0, "page": "p2",
                   "topology-fingerprint": "sha1:3333dddd"},
            "D2": {"region": "right-column", "row": 1, "page": "p2",
                   "topology-fingerprint": "sha1:4444eeee"},
        },
    }
    if extras:
        base.update(extras)
    return base


def _run(circuit: dict, layout: dict) -> list:
    graph = NetGraph.from_yaml_dict(circuit)
    return run_erc(graph, circuit, profiles=_profiles_stub(), layout=layout)


def test_no_pages_block_skips_cross_page_rules():
    """Pre-layout / flat-form circuits: cross-page rules silent."""
    circuit = _two_led_circuit()
    findings = run_erc(
        NetGraph.from_yaml_dict(circuit),
        circuit,
        profiles=_profiles_stub(),
        layout=None,
    )
    for code in ("E19", "E20", "E21", "E22"):
        assert not any(f.check == code for f in findings), f"{code} fired without layout"


def test_E19_page_declared_but_empty():
    """Page with no placements tagged onto it fires E19."""
    circuit = _two_led_circuit()
    layout = _two_page_layout({"pages": [
        {"name": "p1"}, {"name": "p2"}, {"name": "p3"},  # p3 is empty
    ]})
    findings = _run(circuit, layout)
    e19 = [f for f in findings if f.check == "E19"]
    assert any("'p3'" in f.message for f in e19), [f.message for f in e19]
    # p1 and p2 are populated — no spurious E19 for them.
    assert not any("'p1'" in f.message for f in e19)


def test_E20_page_referenced_but_undeclared():
    """Placement carrying `page: pX` where pX is not in pages: fires E20."""
    circuit = _two_led_circuit()
    layout = _two_page_layout()
    # Re-tag U1 to a page that doesn't exist.
    layout["placements"]["U1"]["page"] = "p_typo"
    findings = _run(circuit, layout)
    e20 = [f for f in findings if f.check == "E20"]
    assert any(f.ref == "U1" and "p_typo" in f.message for f in e20), [f.message for f in e20]


def test_E21_cross_page_net_invisible_on_one_side():
    """A placement with `page:` but no `region:` causes label-resolution
    to fail, which the renderer would silently skip. E21 fires."""
    circuit = _two_led_circuit()
    layout = _two_page_layout()
    # Break U1's region: it carries a `page:` but no region/attached-to.
    del layout["placements"]["U1"]["region"]
    findings = _run(circuit, layout)
    e21 = [f for f in findings if f.check == "E21"]
    # PWR_LED2 (U1.D13 ↔ R2.1) crosses p1↔p2 with U1 on p1 unresolvable.
    assert any("PWR_LED2" in f.net or "PWR_LED1" in f.net for f in e21), [f.message for f in e21]


def test_E22_excessive_cross_page_net_count_default_threshold():
    """Six+ cross-page nets between one pair fires E22 at threshold 6."""
    # Build a synthetic circuit with 7 nets crossing p1↔p2.
    components = {
        "U1": {"type": "mcu/esp32"},
    }
    connections = []
    placements = {
        "U1": {"region": "mcu-center", "page": "p1",
               "topology-fingerprint": "sha1:0000aaaa"},
    }
    for i in range(7):
        rname = f"R{i}"
        components[rname] = {"type": "passives/resistor"}
        # First terminal on U1 (p1), second terminal on the resistor (p2).
        connections.append({"net": f"X{i}", "pins": ["U1.D25", f"{rname}.1"]})
        connections.append({"net": f"Y{i}", "pins": [f"{rname}.2", "U1.GNDL"]})
        placements[rname] = {
            "region": "right-column", "row": i, "page": "p2",
            "topology-fingerprint": f"sha1:{i:04d}cccc",
        }
    circuit = {
        "meta": {"title": "many-crossings", "target": "esp32"},
        "components": components,
        "connections": connections,
    }
    layout = {
        "schema": "layout/v1",
        "pages": [{"name": "p1"}, {"name": "p2"}],
        "placements": placements,
    }
    findings = _run(circuit, layout)
    e22 = [f for f in findings if f.check == "E22"]
    assert any("p1 ↔ p2" in f.message for f in e22), [f.message for f in e22]


def test_E22_threshold_tuneable_via_meta_erc():
    """Default threshold 6 lets 6 crossings through; lowering to 3 fires."""
    components = {"U1": {"type": "mcu/esp32"}}
    connections = []
    placements = {
        "U1": {"region": "mcu-center", "page": "p1",
               "topology-fingerprint": "sha1:0000aaaa"},
    }
    for i in range(4):  # 4 crossing nets — between 3 and 6
        rname = f"R{i}"
        components[rname] = {"type": "passives/resistor"}
        connections.append({"net": f"X{i}", "pins": ["U1.D25", f"{rname}.1"]})
        placements[rname] = {
            "region": "right-column", "row": i, "page": "p2",
            "topology-fingerprint": f"sha1:{i:04d}cccc",
        }
    circuit = {
        "meta": {"title": "threshold-test", "target": "esp32",
                 "erc": {"cross-page-threshold": 3}},
        "components": components,
        "connections": connections,
    }
    layout = {
        "schema": "layout/v1",
        "pages": [{"name": "p1"}, {"name": "p2"}],
        "placements": placements,
    }
    findings = _run(circuit, layout)
    e22 = [f for f in findings if f.check == "E22"]
    assert any("threshold 3" in f.message for f in e22), [f.message for f in e22]


def test_clean_two_page_layout_no_cross_page_findings():
    """A well-formed two-page layout fires no E19..E22."""
    circuit = _two_led_circuit()
    layout = _two_page_layout()
    findings = _run(circuit, layout)
    for code in ("E19", "E20", "E21"):
        assert not any(f.check == code for f in findings), \
            [f.message for f in findings if f.check == code]
    # E22 fires only with > 6 cross-page nets; this fixture has ~2.
    assert not any(f.check == "E22" for f in findings)
