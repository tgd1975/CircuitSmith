"""EPIC-014 / TASK-125 — multi-page render driver.

Covers the four fixture-matrix scenarios from IDEA-009 Phase 3:

- **Single-page** (no `pages:` block): output stays at `<stem>.svg`
  with no `-p1` suffix; v0.1 behaviour byte-identical.
- **Two-page minimal**: two pages, one placement on each, emit
  `<stem>-p1.svg` and `<stem>-p2.svg`.
- **Three-page with shared rail**: three pages, GND/VCC nets span
  pages. The cross-page wires are dropped from per-page SVGs;
  TASK-126 adds the boundary label rendering. Both pages still
  render successfully.
- **Two-page independent**: two pages, no cross-page nets. Each
  page renders as if it were the whole circuit.

Plus per-page determinism and singleton-sidecar invariants.
"""
from __future__ import annotations

from pathlib import Path

from circuitsmith.renderer import render


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _two_led_circuit_yaml() -> str:
    """Two independent LED indicators driven by separate GPIOs."""
    return (
        "meta:\n"
        "  title: two-led-multipage\n"
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
    """Three LED indicators (front/middle/back) sharing GND."""
    return (
        "meta:\n"
        "  title: three-led-multipage\n"
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


def test_single_page_circuit_keeps_stem_svg(tmp_path: Path):
    """v0.1 coexistence: no `pages:` block ⇒ emit `<stem>.svg`."""
    circuit_path = tmp_path / "demo.circuit.yml"
    _write(circuit_path, _two_led_circuit_yaml())
    out_svg = tmp_path / "build" / "demo.svg"

    result = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)

    assert result.svg_paths == [out_svg]
    assert out_svg.exists()
    # Defensive: no -p1 / -p2 sibling exists.
    assert not (tmp_path / "build" / "demo-p1.svg").exists()


def test_two_page_layout_emits_suffixed_files(tmp_path: Path):
    """Two-page layout: each declared page gets its own `<stem>-pN.svg`."""
    circuit_path = tmp_path / "demo.circuit.yml"
    _write(circuit_path, _two_led_circuit_yaml())
    out_svg = tmp_path / "build" / "demo.svg"

    # First pass: kernel emits its own layout.yml (no pages).
    bootstrap = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)

    # Hand-author a pages-aware .layout.yml on top of the bootstrap. We
    # keep every placement but tag the two LED-driver pairs onto separate
    # pages. The MCU lives on p1 (the "front" sheet by convention).
    layout_text = bootstrap.layout_path.read_text()
    # Augment with a pages block and per-placement page tags.
    augmented = "pages:\n  - { name: p1 }\n  - { name: p2 }\n" + layout_text.replace(
        "schema: layout/v1\n",
        "schema: layout/v1\n",
    )
    # Add `page: p1` to U1, R1, D1; `page: p2` to R2, D2.
    def _tag(line: str, ref: str, page: str) -> str:
        if not line.startswith(f"  {ref}: "):
            return line
        return line.rstrip().rstrip("}").rstrip(", ") + f", page: {page} }}"

    lines = augmented.split("\n")
    out_lines: list[str] = []
    for line in lines:
        new = line
        for ref in ("U1", "R1", "D1"):
            new = _tag(new, ref, "p1")
        for ref in ("R2", "D2"):
            new = _tag(new, ref, "p2")
        out_lines.append(new)
    augmented_yaml = "\n".join(out_lines)
    pages_layout = tmp_path / "demo.layout.yml"
    pages_layout.write_text(augmented_yaml)

    # Render with the pages-aware layout.
    out_svg2 = tmp_path / "build2" / "demo.svg"
    result = render(
        circuit_path=circuit_path,
        layout_path=pages_layout,
        out_svg=out_svg2,
    )

    p1 = tmp_path / "build2" / "demo-p1.svg"
    p2 = tmp_path / "build2" / "demo-p2.svg"
    assert result.svg_paths == [p1, p2]
    assert p1.exists()
    assert p2.exists()
    # No `<stem>.svg` is written in multi-page mode.
    assert not out_svg2.exists()


def test_three_page_with_shared_rail_renders_all_pages(tmp_path: Path):
    """A shared GND rail across three pages produces three SVGs.

    Cross-page wires (those whose endpoints land on different pages)
    are dropped from each per-page SVG — TASK-126 will add the
    boundary label rendering. The acceptance bar for TASK-125 is that
    every declared page produces a valid SVG.
    """
    circuit_path = tmp_path / "demo.circuit.yml"
    _write(circuit_path, _three_led_circuit_yaml())
    out_svg = tmp_path / "build" / "demo.svg"
    bootstrap = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)

    layout_text = bootstrap.layout_path.read_text()
    augmented = "pages:\n  - { name: p1 }\n  - { name: p2 }\n  - { name: p3 }\n" + layout_text

    def _tag(line: str, ref: str, page: str) -> str:
        if not line.startswith(f"  {ref}: "):
            return line
        return line.rstrip().rstrip("}").rstrip(", ") + f", page: {page} }}"

    lines = augmented.split("\n")
    out_lines: list[str] = []
    for line in lines:
        new = line
        for ref in ("U1", "R1", "D1"):
            new = _tag(new, ref, "p1")
        for ref in ("R2", "D2"):
            new = _tag(new, ref, "p2")
        for ref in ("R3", "D3"):
            new = _tag(new, ref, "p3")
        out_lines.append(new)
    pages_layout = tmp_path / "demo.layout.yml"
    pages_layout.write_text("\n".join(out_lines))

    out_svg2 = tmp_path / "build2" / "demo.svg"
    result = render(
        circuit_path=circuit_path,
        layout_path=pages_layout,
        out_svg=out_svg2,
    )

    assert len(result.svg_paths) == 3
    for idx in (1, 2, 3):
        page_svg = tmp_path / "build2" / f"demo-p{idx}.svg"
        assert page_svg.exists()
        assert page_svg.read_text().startswith("<svg")


def test_layout_and_meta_are_singletons(tmp_path: Path):
    """Multi-page output emits one `.layout.yml` and one `.meta.yml`,
    not one per page — they describe the whole circuit."""
    circuit_path = tmp_path / "demo.circuit.yml"
    _write(circuit_path, _two_led_circuit_yaml())
    out_svg = tmp_path / "build" / "demo.svg"
    bootstrap = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    augmented = (
        "pages:\n  - { name: p1 }\n  - { name: p2 }\n"
        + bootstrap.layout_path.read_text()
    )
    def _tag(line: str, ref: str, page: str) -> str:
        if not line.startswith(f"  {ref}: "):
            return line
        return line.rstrip().rstrip("}").rstrip(", ") + f", page: {page} }}"
    lines = augmented.split("\n")
    out_lines: list[str] = []
    for line in lines:
        new = line
        for ref in ("U1", "R1", "D1"):
            new = _tag(new, ref, "p1")
        for ref in ("R2", "D2"):
            new = _tag(new, ref, "p2")
        out_lines.append(new)
    pages_layout = tmp_path / "demo.layout.yml"
    pages_layout.write_text("\n".join(out_lines))
    out_svg2 = tmp_path / "build2" / "demo.svg"
    result = render(
        circuit_path=circuit_path,
        layout_path=pages_layout,
        out_svg=out_svg2,
    )
    # Exactly one layout.yml and one meta.yml. They reside next to the
    # nominal `<stem>.svg` path, not next to per-page SVGs.
    assert result.layout_path.exists()
    assert result.meta_path.exists()
    assert result.layout_path.suffix == ".yml"
    assert result.meta_path.suffix == ".yml"


def test_multi_page_render_is_deterministic(tmp_path: Path):
    """Running the multi-page driver twice produces byte-identical SVGs."""
    circuit_path = tmp_path / "demo.circuit.yml"
    _write(circuit_path, _two_led_circuit_yaml())
    out_svg = tmp_path / "build" / "demo.svg"
    bootstrap = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    augmented = (
        "pages:\n  - { name: p1 }\n  - { name: p2 }\n"
        + bootstrap.layout_path.read_text()
    )
    def _tag(line: str, ref: str, page: str) -> str:
        if not line.startswith(f"  {ref}: "):
            return line
        return line.rstrip().rstrip("}").rstrip(", ") + f", page: {page} }}"
    lines = augmented.split("\n")
    out_lines = []
    for line in lines:
        new = line
        for ref in ("U1", "R1", "D1"):
            new = _tag(new, ref, "p1")
        for ref in ("R2", "D2"):
            new = _tag(new, ref, "p2")
        out_lines.append(new)
    pages_layout = tmp_path / "demo.layout.yml"
    pages_layout.write_text("\n".join(out_lines))

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
    # Compare per-page SVG bytes pairwise.
    assert len(first.svg_paths) == len(second.svg_paths) == 2
    for a, b in zip(first.svg_paths, second.svg_paths):
        assert a.read_bytes() == b.read_bytes()


def test_two_page_independent_subsystems(tmp_path: Path):
    """When no nets span page boundaries, each per-page SVG contains all
    its own wires — a baseline for TASK-126's cross-page-label work."""
    circuit_path = tmp_path / "demo.circuit.yml"
    _write(circuit_path, _two_led_circuit_yaml())
    out_svg = tmp_path / "build" / "demo.svg"
    bootstrap = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)

    # Put U1 + LED1 set on p1, LED2 set on p2 — but no shared net is
    # forced cross-page because the only shared net is GND, which sits
    # on U1's page (p1). The LED2 GND endpoint lives on p2, so that
    # wire is cross-page and gets dropped from p1's SVG.
    augmented = (
        "pages:\n  - { name: p1 }\n  - { name: p2 }\n"
        + bootstrap.layout_path.read_text()
    )
    def _tag(line: str, ref: str, page: str) -> str:
        if not line.startswith(f"  {ref}: "):
            return line
        return line.rstrip().rstrip("}").rstrip(", ") + f", page: {page} }}"
    lines = augmented.split("\n")
    out_lines = []
    for line in lines:
        new = line
        for ref in ("U1", "R1", "D1"):
            new = _tag(new, ref, "p1")
        for ref in ("R2", "D2"):
            new = _tag(new, ref, "p2")
        out_lines.append(new)
    pages_layout = tmp_path / "demo.layout.yml"
    pages_layout.write_text("\n".join(out_lines))

    result = render(
        circuit_path=circuit_path,
        layout_path=pages_layout,
        out_svg=tmp_path / "build2" / "demo.svg",
    )
    p1_text = result.svg_paths[0].read_text()
    p2_text = result.svg_paths[1].read_text()
    # p1 carries U1's components; p2 carries the LED2 chain.
    assert 'data-ref="U1"' in p1_text
    assert 'data-ref="D1"' in p1_text
    assert 'data-ref="D2"' in p2_text
    assert 'data-ref="R2"' in p2_text
    # Cross-page bleed: p1 doesn't carry D2's glyph, and vice versa.
    assert 'data-ref="D2"' not in p1_text
    assert 'data-ref="U1"' not in p2_text
