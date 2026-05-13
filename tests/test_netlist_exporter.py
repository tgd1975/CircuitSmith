"""
Netlist exporter — TASK-033.

Tests cover:

  - Named-net preservation (pins-form nets keep their declared names)
  - Path-form segment naming (first segment uses the declared net name,
    later segments use the content-addressed form from `NetGraph`)
  - Net-code assignment is deterministic across two runs
  - Component-block emits one (comp ...) per ref in declaration order
  - (datasheet ...) is omitted when the profile carries none, included
    when it does
  - (value ...) matches the BOM CSV `Value` column row-for-row
  - Round-trip: parsing the emitted .net reconstructs the same
    {net_name -> set(PinRef)} as `NetGraph.nets`

The S-expression parsing is hand-rolled (~30 lines) per the dossier
§"Round-trip test" — KiCad's .net grammar is a tiny subset of
S-expressions and does not justify a third-party dep.
"""
from __future__ import annotations

from pathlib import Path

from circuitsmith.export.bom_exporter import export as export_bom
from circuitsmith.export.netlist_exporter import (
    _component_value,
    _escape,
    export,
)
from circuitsmith.netgraph import NetGraph, PinRef
from circuitsmith.schema.registry import load_profiles


# ── Fixture builders ─────────────────────────────────────────────────────


def _circuit_with_path():
    """Path-form net feeding a power LED through a current-limit resistor."""
    return {
        "meta": {"title": "test build"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor", "value": 220},
            "D1": {"type": "passives/led", "color": "green"},
            "J1": {"type": "connectors/usb_c"},
        },
        "connections": [
            {"net": "VCC", "pins": ["J1.VBUS", "U1.VIN"]},
            {"net": "GND", "pins": ["J1.GND", "U1.GNDL", "D1.K"]},
            {"net": "LED_PWR", "path": ["U1.D2", "R1.1", "R1.2", "D1.A"]},
        ],
    }


# ── Surface-shape tests ──────────────────────────────────────────────────


def test_named_nets_preserve_declared_name():
    circuit = _circuit_with_path()
    profiles = load_profiles()
    graph = NetGraph.from_yaml_dict(circuit)
    text = export(circuit, graph, profiles, Path("data/esp32.circuit.yml"))
    assert '(net (code 1) (name "VCC")' in text
    assert '(net (code 2) (name "GND")' in text
    # First segment of LED_PWR takes the declared net name.
    assert '(name "LED_PWR")' in text


def test_path_segments_use_content_addressed_names():
    circuit = _circuit_with_path()
    profiles = load_profiles()
    graph = NetGraph.from_yaml_dict(circuit)
    text = export(circuit, graph, profiles, Path("data/esp32.circuit.yml"))
    # Second segment of LED_PWR: content-addressed by R1.2 / D1.A endpoints.
    assert '(name "LED_PWR__R1_2__D1_A")' in text


def test_components_block_one_entry_per_ref():
    circuit = _circuit_with_path()
    profiles = load_profiles()
    graph = NetGraph.from_yaml_dict(circuit)
    text = export(circuit, graph, profiles, Path("data/esp32.circuit.yml"))
    # In declaration order.
    pos_u1 = text.index("(comp (ref U1)")
    pos_r1 = text.index("(comp (ref R1)")
    pos_d1 = text.index("(comp (ref D1)")
    pos_j1 = text.index("(comp (ref J1)")
    assert pos_u1 < pos_r1 < pos_d1 < pos_j1


def test_value_matches_bom_csv():
    circuit = _circuit_with_path()
    profiles = load_profiles()
    graph = NetGraph.from_yaml_dict(circuit)
    net_text = export(circuit, graph, profiles, Path("data/esp32.circuit.yml"))
    _, bom_csv = export_bom(circuit, profiles)
    # R1 row in CSV: "R1,passives/resistor,220,..."
    assert ",220," in bom_csv
    assert '(comp (ref R1) (value "220")' in net_text
    # D1 row in CSV: "D1,passives/led,green,..."
    assert ",green," in bom_csv
    assert '(comp (ref D1) (value "green")' in net_text


def test_datasheet_omitted_when_profile_has_none():
    circuit = {
        "meta": {"title": "minimal"},
        "components": {
            "R1": {"type": "passives/resistor", "value": 220},
            "R2": {"type": "passives/resistor", "value": 220},
        },
        "connections": [
            {"net": "FOO", "pins": ["R1.1", "R2.1"]},
        ],
    }
    profiles = load_profiles()
    graph = NetGraph.from_yaml_dict(circuit)
    text = export(circuit, graph, profiles, Path("data/test.circuit.yml"))
    # Resistor profile has no datasheet metadata — the comp line must not
    # carry a (datasheet ...) trailer.
    r1_line = next(line for line in text.split("\n") if "(ref R1)" in line)
    assert "(datasheet" not in r1_line


def test_datasheet_included_when_profile_declares_one():
    circuit = _circuit_with_path()
    profiles = load_profiles()
    graph = NetGraph.from_yaml_dict(circuit)
    text = export(circuit, graph, profiles, Path("data/esp32.circuit.yml"))
    u1_line = next(line for line in text.split("\n") if "(ref U1)" in line)
    assert "(datasheet" in u1_line
    assert "espressif" in u1_line.lower()


def test_determinism_across_two_runs():
    circuit = _circuit_with_path()
    profiles = load_profiles()
    g1 = NetGraph.from_yaml_dict(circuit)
    g2 = NetGraph.from_yaml_dict(circuit)
    src = Path("data/esp32.circuit.yml")
    a = export(circuit, g1, profiles, src)
    b = export(circuit, g2, profiles, src)
    assert a == b


def test_helpers_value_and_escape():
    profiles = load_profiles()
    assert _component_value(profiles["passives/resistor"], {"value": 470}) == "470"
    assert _component_value(profiles["passives/led"], {"color": "red"}) == "red"
    assert _component_value(profiles["mcu/esp32"], {}) == ""
    assert _escape('hello "world"') == 'hello \\"world\\"'


# ── Round-trip parse ─────────────────────────────────────────────────────


def _tokenise(text: str) -> list:
    """Tiny S-expression tokeniser — paren/whitespace/quoted-string only."""
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in "()":
            tokens.append(ch)
            i += 1
        elif ch.isspace():
            i += 1
        elif ch == '"':
            j = i + 1
            chunk = []
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    chunk.append(text[j + 1])
                    j += 2
                else:
                    chunk.append(text[j])
                    j += 1
            tokens.append('"' + "".join(chunk) + '"')
            i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in "()":
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def _parse(tokens):
    """Recursive-descent S-expression parser. Returns list-of-lists."""
    pos = [0]

    def walk():
        token = tokens[pos[0]]
        pos[0] += 1
        if token == "(":
            items = []
            while tokens[pos[0]] != ")":
                items.append(walk())
            pos[0] += 1  # consume ")"
            return items
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]
        return token

    return walk()


def _extract_nets(parsed) -> dict[str, set[PinRef]]:
    """From a parsed (export ...) tree, return {net_name -> set(PinRef)}."""
    out: dict[str, set[PinRef]] = {}
    # parsed[0] = "export"; remaining = blocks
    for block in parsed[1:]:
        if not isinstance(block, list) or not block or block[0] != "nets":
            continue
        for net in block[1:]:
            # net = ["net", ["code", "1"], ["name", "VCC"], ["node", ...], ...]
            name = ""
            members: set[PinRef] = set()
            for child in net[1:]:
                if not isinstance(child, list):
                    continue
                if child[0] == "name":
                    name = child[1]
                elif child[0] == "node":
                    # ["node", ["ref", "U1"], ["pin", "VIN"]]
                    ref = next(c[1] for c in child[1:] if isinstance(c, list) and c[0] == "ref")
                    pin = next(c[1] for c in child[1:] if isinstance(c, list) and c[0] == "pin")
                    members.add(PinRef(ref=ref, pin=pin))
            if name:
                out[name] = members
    return out


def test_round_trip_preserves_pin_memberships():
    circuit = _circuit_with_path()
    profiles = load_profiles()
    graph = NetGraph.from_yaml_dict(circuit)
    text = export(circuit, graph, profiles, Path("data/esp32.circuit.yml"))

    parsed = _parse(_tokenise(text))
    reconstructed = _extract_nets(parsed)
    graph_view = {name: set(members) for name, members in graph.nets.items()}

    # Same net names, same membership sets.
    assert set(reconstructed) == set(graph_view)
    for name, members in graph_view.items():
        assert reconstructed[name] == members, (
            f"net {name!r} mismatch: graph={members} parsed={reconstructed[name]}"
        )


def test_round_trip_on_bus_form_collapses_to_one_net():
    """Bus-form nets must collapse to one (net ...) block — the
    bus-collapse invariant from dossier §"Critical: bus collapses to one
    electrical net". A renderer drawing stubs is visual; KiCad sees one
    electrical net for the whole bus.
    """
    circuit = {
        "meta": {"title": "bus"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor", "value": 4700},
        },
        "connections": [
            {
                "net": "I2C_SDA",
                "bus": True,
                "backbone": ["U1.IO21"],
                "taps": ["R1.2"],
            },
        ],
    }
    profiles = load_profiles()
    graph = NetGraph.from_yaml_dict(circuit)
    text = export(circuit, graph, profiles, Path("data/test.circuit.yml"))
    # Exactly one (net ...) block for the bus.
    assert text.count('(name "I2C_SDA")') == 1
    parsed = _parse(_tokenise(text))
    reconstructed = _extract_nets(parsed)
    assert reconstructed["I2C_SDA"] == {
        PinRef("U1", "IO21"),
        PinRef("R1", "2"),
    }
