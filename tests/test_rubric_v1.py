"""
v1 (Phase 2b) rubric tests for TASK-019.

The v0.1 rubric recorded `min_label_distance` and `density` as
advisory metrics only. Under v1 both are promoted to blocking, with
thresholds derived from the Phase 2a green-corpus (75th-percentile
floor per `idea-001.layout-engine-concept.md §10`).

The v0.1 corpus is two shipped circuits — both produce
`min_label_distance = 1` and `density = 0.1453`. The thresholds
below accept that corpus and flag layouts that are pathologically
crowded or have overlapping labels.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from circuit.layout_engine import LayoutResult, Placement, RouterResult, evaluate
from circuit.layout_engine.rubric import (
    DEFAULT_DENSITY_THRESHOLD,
    DEFAULT_MIN_LABEL_DISTANCE_THRESHOLD,
)
from circuit.renderer import render

REPO_ROOT = Path(__file__).resolve().parents[1]


def _empty_router() -> RouterResult:
    return RouterResult(routes=[], crossings=0, intra_component_intersections=0)


# ── Threshold defaults are derived from the Phase 2a green corpus ───────


def test_default_thresholds_are_documented():
    """Both thresholds carry the 75th-percentile rationale from the dossier."""
    assert DEFAULT_MIN_LABEL_DISTANCE_THRESHOLD == 1
    assert DEFAULT_DENSITY_THRESHOLD == 0.5


# ── min_label_distance promoted to blocking ──────────────────────────────


def test_min_label_distance_below_threshold_fails():
    """Two labelled placements at the same cell trip the check."""
    layout = LayoutResult(placements={
        "A": Placement(ref="A", region="left-column", row=0, label="left"),
        "B": Placement(ref="B", region="left-column", row=0, label="left"),
    })
    result = evaluate(
        layout=layout,
        router_result=_empty_router(),
        min_label_distance_threshold=2,
    )
    findings = [f for f in result.failures if f.check == "min_label_distance"]
    assert findings, result.failures
    assert "min_label_distance" in findings[0].message
    assert "A" in findings[0].refs and "B" in findings[0].refs


def test_min_label_distance_at_threshold_passes():
    layout = LayoutResult(placements={
        "A": Placement(ref="A", region="left-column", row=0, label="left"),
        "B": Placement(ref="B", region="left-column", row=1, label="left"),
    })
    result = evaluate(
        layout=layout,
        router_result=_empty_router(),
        min_label_distance_threshold=1,  # B is 2 rows = 2 grid units away
    )
    assert not any(f.check == "min_label_distance" for f in result.failures)


# ── density promoted to blocking ────────────────────────────────────────


def test_density_above_threshold_fails():
    """A pathologically dense layout (every cell occupied) trips the check."""
    # Pack the left-column with placements at rows 0..3 — density ≈ 1.0 if
    # bbox is exactly those rows. Set a strict threshold to trip.
    layout = LayoutResult(placements={
        f"D{i}": Placement(ref=f"D{i}", region="left-column", row=i, label="left")
        for i in range(4)
    })
    result = evaluate(
        layout=layout,
        router_result=_empty_router(),
        density_threshold=0.1,  # impossibly tight for testing
    )
    findings = [f for f in result.failures if f.check == "density"]
    assert findings, result.failures
    assert "density" in findings[0].message


def test_density_at_threshold_passes():
    layout = LayoutResult(placements={
        "U1": Placement(ref="U1", region="mcu-center"),
    })
    result = evaluate(
        layout=layout,
        router_result=_empty_router(),
        density_threshold=1.0,
    )
    assert not any(f.check == "density" for f in result.failures)


# ── Suppression for pre-Phase-2b fixtures ───────────────────────────────


def test_none_threshold_suppresses_check():
    """Passing None for either threshold preserves v0.1 advisory-only behaviour."""
    layout = LayoutResult(placements={
        "A": Placement(ref="A", region="left-column", row=0, label="left"),
        "B": Placement(ref="B", region="left-column", row=0, label="left"),
    })
    result = evaluate(
        layout=layout,
        router_result=_empty_router(),
        min_label_distance_threshold=None,  # advisory only
        density_threshold=None,
    )
    # No min_label_distance/density failures even though we co-located labels.
    assert not any(f.check == "min_label_distance" for f in result.failures)
    assert not any(f.check == "density" for f in result.failures)
    # Metrics are still recorded.
    assert "min_label_distance" in result.metrics
    assert "density" in result.metrics


# ── Both shipped circuits pass at the empirical thresholds ─────────────


@pytest.mark.parametrize("target", ["esp32", "nrf52840"])
def test_shipped_circuit_passes_promoted_thresholds(target: str, tmp_path: Path):
    circuit_path = REPO_ROOT / "data" / f"{target}.circuit.yml"
    out_svg = tmp_path / f"{target}.svg"
    result = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    assert result.rubric.passed, result.rubric.findings
    # Specifically: the two promoted checks pass at the defaults.
    assert result.rubric.metrics["min_label_distance"] >= DEFAULT_MIN_LABEL_DISTANCE_THRESHOLD
    assert result.rubric.metrics["density"] <= DEFAULT_DENSITY_THRESHOLD
