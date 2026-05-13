"""
CI staleness guard (TASK-015 cutover).

Re-runs the renderer over each shipped `.circuit.yml` and compares the
output against the committed expected fixtures. The comparison is
structural (XML element shape + `data-ref` attributes), not pixel-
diff — schemdraw / matplotlib float-geometry stability is OS-dependent
per `idea-001.layout-engine-concept.md §12 Cross-platform caveat`.

Failure means the committed `tests/fixtures/full-pedal/<target>/
expected.svg` is out of date with the renderer's current output. The
fix is to re-run the renderer and re-commit, not to patch the SVG by
hand.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from circuit.renderer import render

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "full-pedal"
TARGETS = ("esp32", "nrf52840")


def _structural_fingerprint(svg_text: str) -> dict:
    """Element type + data-ref attributes — robust to coordinate drift."""
    element_re = re.compile(r"<([a-zA-Z][a-zA-Z0-9]*)\b")
    data_ref_re = re.compile(r'data-ref="([^"]+)"')
    data_net_re = re.compile(r'data-net="([^"]+)"')
    return {
        "elements": sorted(element_re.findall(svg_text)),
        "data_refs": sorted(data_ref_re.findall(svg_text)),
        "data_nets": sorted(data_net_re.findall(svg_text)),
    }


@pytest.mark.parametrize("target", TARGETS)
def test_renderer_output_matches_fixture(target: str, tmp_path: Path):
    """The renderer's current SVG must structurally match the committed fixture."""
    circuit_path = DATA_DIR / f"{target}.circuit.yml"
    out_svg = tmp_path / f"{target}.svg"
    render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)

    rendered = _structural_fingerprint(out_svg.read_text())
    expected = _structural_fingerprint(
        (FIXTURE_DIR / target / "expected.svg").read_text()
    )

    assert rendered == expected, (
        f"renderer output for {target} drifted from committed fixture. "
        f"Re-run the renderer and commit the refreshed "
        f"tests/fixtures/full-pedal/{target}/expected.{{svg,meta.yml}}."
    )


@pytest.mark.parametrize("target", TARGETS)
def test_meta_yml_fixture_is_present_and_clean(target: str):
    """The committed fixture meta.yml exists and records a clean run."""
    meta_path = FIXTURE_DIR / target / "expected.meta.yml"
    assert meta_path.exists(), f"missing fixture: {meta_path}"
    meta = meta_path.read_text()
    assert "state: complete" in meta
    assert "escalations: []" in meta
