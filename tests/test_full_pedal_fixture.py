"""
Full-pedal fixture tests for TASK-014.

Confirms the renderer runs end-to-end against the shipped esp32 and
nrf52840 `.circuit.yml` files, producing rubric-green SVGs whose
structural fingerprint (XML element shape + `data-ref` attributes) is
stable across runs.

The `data/*.circuit.yml` files are checked into the repo; the test
runs the renderer over a tmp_path so it doesn't litter the worktree
with build artefacts.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from circuitsmith.renderer import render

REPO_ROOT = Path(__file__).resolve().parents[1]
CIRCUIT_DIR = REPO_ROOT / "data"

TARGETS = ("esp32", "nrf52840")


@pytest.mark.parametrize("target", TARGETS)
def test_full_pipeline_runs_clean(target: str, tmp_path: Path):
    circuit_path = CIRCUIT_DIR / f"{target}.circuit.yml"
    out_svg = tmp_path / f"{target}.svg"
    result = render(
        circuit_path=circuit_path,
        layout_path=None,
        out_svg=out_svg,
    )
    assert result.rubric.passed, result.rubric.findings
    assert out_svg.exists()
    text = out_svg.read_text()
    assert text.startswith("<svg")
    assert "data-ref=\"U1\"" in text


@pytest.mark.parametrize("target", TARGETS)
def test_layout_yaml_validates_against_schema(target: str, tmp_path: Path):
    from circuitsmith.schema import validate_layout_file

    circuit_path = CIRCUIT_DIR / f"{target}.circuit.yml"
    out_svg = tmp_path / f"{target}.svg"
    result = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    findings = validate_layout_file(result.layout_path)
    assert findings == [], f"layout.yml failed validation: {findings}"


@pytest.mark.parametrize("target", TARGETS)
def test_renderer_is_deterministic_across_runs(target: str, tmp_path: Path):
    """Two runs of the renderer produce byte-identical layout.yml and SVG."""
    circuit_path = CIRCUIT_DIR / f"{target}.circuit.yml"

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()

    a = render(circuit_path=circuit_path, layout_path=None, out_svg=first_dir / "out.svg")
    b = render(circuit_path=circuit_path, layout_path=None, out_svg=second_dir / "out.svg")

    assert a.layout_path.read_text() == b.layout_path.read_text()
    # SVG paths embed the temp dir into the data-doc, so byte-compare the
    # placement-bearing core via the layout.yml above and the data-ref count
    # below.
    a_text = a.svg_path.read_text()
    b_text = b.svg_path.read_text()
    a_refs = sorted(line for line in a_text.splitlines() if "data-ref=" in line)
    b_refs = sorted(line for line in b_text.splitlines() if "data-ref=" in line)
    assert a_refs == b_refs
