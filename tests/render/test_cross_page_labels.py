"""EPIC-014 / TASK-126 — cross-page net label rendering.

Detection rather than declaration: the renderer walks every route
and, when the two endpoint placements live on different pages,
emits a paired arrow + text glyph on both sides (a `▶ p2` stub on
p1's SVG, a `◀ p1` stub on p2's SVG).

Covered scenarios:

- **Shared-rail two-page**: a single `SIGNAL`/`GND` net spans p1
  and p2 — both per-page SVGs gain the arrow glyph naming the
  *other* page.
- **Three-page shared rail**: `GND` touches three pages — each
  per-page SVG names both of the *other two* pages in its
  cross-page labels.
- **Internal nets** (entirely on one page) **do not** get
  cross-page labels — the detection pass must skip same-page
  wires.
- **Determinism**: two passes produce byte-identical SVGs (the
  label list is sorted, so de-duplication is stable).
"""
from __future__ import annotations

from pathlib import Path

from circuitsmith.renderer import render


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _two_led_circuit_yaml() -> str:
    return (
        "meta:\n"
        "  title: shared-gnd-multipage\n"
        "  target: esp32\n"
        "components:\n"
        "  U1:  { type: mcu/esp32 }\n"
        "  R1:  { type: passives/resistor, value: 330 }\n"
        "  D1:  { type: passives/led, color: green }\n"
        "  R2:  { type: passives/resistor, value: 330 }\n"
        "  D2:  { type: passives/led, color: red }\n"
        "connections:\n"
        "  - net: PWR_LED1\n"
        "    path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]\n"
        "  - net: PWR_LED2\n"
        "    path: [U1.D13, R2.1, R2.2, D2.A, D2.K, GND]\n"
        "  - net: GND\n"
        "    pins: [U1.GNDL]\n"
    )


def _three_led_circuit_yaml() -> str:
    return (
        "meta:\n"
        "  title: three-led-shared-rail\n"
        "  target: esp32\n"
        "components:\n"
        "  U1:  { type: mcu/esp32 }\n"
        "  R1:  { type: passives/resistor, value: 330 }\n"
        "  D1:  { type: passives/led, color: green }\n"
        "  R2:  { type: passives/resistor, value: 330 }\n"
        "  D2:  { type: passives/led, color: red }\n"
        "  R3:  { type: passives/resistor, value: 330 }\n"
        "  D3:  { type: passives/led, color: blue }\n"
        "connections:\n"
        "  - net: PWR_LED1\n"
        "    path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]\n"
        "  - net: PWR_LED2\n"
        "    path: [U1.D13, R2.1, R2.2, D2.A, D2.K, GND]\n"
        "  - net: PWR_LED3\n"
        "    path: [U1.D14, R3.1, R3.2, D3.A, D3.K, GND]\n"
        "  - net: GND\n"
        "    pins: [U1.GNDL]\n"
    )


def _augment_with_pages(
    layout_text: str, page_assignments: dict[str, str], page_names: list[str]
) -> str:
    """Inject a `pages:` block and per-placement `page:` tags."""
    pages_block = "pages:\n" + "".join(f"  - {{ name: {n} }}\n" for n in page_names)

    def _tag(line: str, ref: str, page: str) -> str:
        if not line.startswith(f"  {ref}: "):
            return line
        return line.rstrip().rstrip("}").rstrip(", ") + f", page: {page} }}"

    lines = (pages_block + layout_text).split("\n")
    out_lines: list[str] = []
    for line in lines:
        new = line
        for ref, page in page_assignments.items():
            new = _tag(new, ref, page)
        out_lines.append(new)
    return "\n".join(out_lines)


def _bootstrap(tmp_path: Path, circuit_yaml: str) -> tuple[Path, Path]:
    circuit_path = tmp_path / "demo.circuit.yml"
    _write(circuit_path, circuit_yaml)
    bootstrap = render(
        circuit_path=circuit_path,
        layout_path=None,
        out_svg=tmp_path / "build" / "demo.svg",
    )
    return circuit_path, bootstrap.layout_path


def test_two_page_shared_rail_emits_paired_arrows(tmp_path: Path):
    circuit_path, bootstrap_layout = _bootstrap(tmp_path, _two_led_circuit_yaml())
    augmented = _augment_with_pages(
        bootstrap_layout.read_text(),
        {"U1": "p1", "R1": "p1", "D1": "p1", "R2": "p2", "D2": "p2"},
        ["p1", "p2"],
    )
    pages_layout = tmp_path / "demo.layout.yml"
    pages_layout.write_text(augmented)

    result = render(
        circuit_path=circuit_path,
        layout_path=pages_layout,
        out_svg=tmp_path / "build2" / "demo.svg",
    )
    p1_text = result.svg_paths[0].read_text()
    p2_text = result.svg_paths[1].read_text()

    # The PWR_LED2 / GND nets cross. Each page has at least one
    # cross-page label naming the *other* page.
    assert 'class="cross-page-labels"' in p1_text
    assert 'class="cross-page-labels"' in p2_text
    assert 'data-other-page="p2"' in p1_text
    assert 'data-other-page="p1"' in p2_text
    # Arrow glyph direction.
    assert "▶" in p1_text  # outbound from p1
    assert "◀" in p2_text  # inbound to p2


def test_three_page_shared_rail_each_page_names_others(tmp_path: Path):
    circuit_path, bootstrap_layout = _bootstrap(tmp_path, _three_led_circuit_yaml())
    augmented = _augment_with_pages(
        bootstrap_layout.read_text(),
        {
            "U1": "p1", "R1": "p1", "D1": "p1",
            "R2": "p2", "D2": "p2",
            "R3": "p3", "D3": "p3",
        },
        ["p1", "p2", "p3"],
    )
    pages_layout = tmp_path / "demo.layout.yml"
    pages_layout.write_text(augmented)

    result = render(
        circuit_path=circuit_path,
        layout_path=pages_layout,
        out_svg=tmp_path / "build2" / "demo.svg",
    )
    p1_text = result.svg_paths[0].read_text()
    p2_text = result.svg_paths[1].read_text()
    p3_text = result.svg_paths[2].read_text()

    # p1 carries the MCU + LED1 chain; PWR_LED2 and PWR_LED3 each cross
    # from U1 to a different page, plus GND spans every page —
    # so p1 must name both p2 and p3.
    assert 'data-other-page="p2"' in p1_text
    assert 'data-other-page="p3"' in p1_text
    # p2 reaches p1 via PWR_LED2 (U1.D13↔R2.1), and p3 via GND
    # (D2.K↔D3.K through the shared rail). So p2 names both p1 and p3.
    assert 'data-other-page="p1"' in p2_text
    assert 'data-other-page="p3"' in p2_text
    # Same for p3.
    assert 'data-other-page="p1"' in p3_text
    assert 'data-other-page="p2"' in p3_text


def test_single_page_circuit_emits_no_cross_page_labels(tmp_path: Path):
    """v0.1 coexistence: no pages block ⇒ no cross-page label group."""
    circuit_path, _ = _bootstrap(tmp_path, _two_led_circuit_yaml())
    out_svg = tmp_path / "build" / "demo.svg"
    svg_text = out_svg.read_text()
    assert 'class="cross-page-labels"' not in svg_text


def test_internal_net_does_not_get_cross_page_label(tmp_path: Path):
    """A net entirely within one page must not appear in cross-page labels."""
    circuit_path, bootstrap_layout = _bootstrap(tmp_path, _two_led_circuit_yaml())
    augmented = _augment_with_pages(
        bootstrap_layout.read_text(),
        {"U1": "p1", "R1": "p1", "D1": "p1", "R2": "p2", "D2": "p2"},
        ["p1", "p2"],
    )
    pages_layout = tmp_path / "demo.layout.yml"
    pages_layout.write_text(augmented)
    result = render(
        circuit_path=circuit_path,
        layout_path=pages_layout,
        out_svg=tmp_path / "build2" / "demo.svg",
    )
    p1_text = result.svg_paths[0].read_text()
    # PWR_LED1 is U1↔R1↔D1, all on p1; it must not appear as a
    # cross-page label.
    assert 'data-net="PWR_LED1"' not in p1_text.split('cross-page-labels')[1] if 'cross-page-labels' in p1_text else True


def test_cross_page_label_rendering_is_deterministic(tmp_path: Path):
    """Two passes produce byte-identical SVGs (labels sorted)."""
    circuit_path, bootstrap_layout = _bootstrap(tmp_path, _two_led_circuit_yaml())
    augmented = _augment_with_pages(
        bootstrap_layout.read_text(),
        {"U1": "p1", "R1": "p1", "D1": "p1", "R2": "p2", "D2": "p2"},
        ["p1", "p2"],
    )
    pages_layout = tmp_path / "demo.layout.yml"
    pages_layout.write_text(augmented)
    first = render(
        circuit_path=circuit_path,
        layout_path=pages_layout,
        out_svg=tmp_path / "build2" / "demo.svg",
    )
    second = render(
        circuit_path=circuit_path,
        layout_path=first.layout_path,
        out_svg=tmp_path / "build3" / "demo.svg",
    )
    for a, b in zip(first.svg_paths, second.svg_paths):
        assert a.read_bytes() == b.read_bytes()
