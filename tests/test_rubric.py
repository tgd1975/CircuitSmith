"""
Rubric tests for TASK-011.

Covers the four acceptance criteria:
  1. Rubric runs after router; failure aborts emission (caller inspects `.passed`).
  2. All three blocking checks (`overlaps`, `labels_fit`, `wire_crossings`)
     are implemented and pass on a clean fixture.
  3. Advisory checks emit numeric values to the metrics dict.
  4. Diagnostic output names the failing check + components involved.
"""
from __future__ import annotations

from circuit.layout_engine import (
    LayoutResult,
    Placement,
    RouterResult,
    Segment,
    WireRoute,
    evaluate,
)
from circuit.netgraph import PinRef


def _clean_layout() -> LayoutResult:
    return LayoutResult(placements={
        "U1": Placement(ref="U1", region="mcu-center"),
        "D1": Placement(ref="D1", region="left-column",  row=0, label="left"),
        "D2": Placement(ref="D2", region="right-column", row=0, label="right"),
    })


def _empty_router_result() -> RouterResult:
    return RouterResult(routes=[], crossings=0, intra_component_intersections=0)


def test_clean_layout_passes_rubric():
    result = evaluate(layout=_clean_layout(), router_result=_empty_router_result())
    assert result.passed, result.findings
    assert result.failures == []


def test_advisory_metrics_emitted_to_metrics_dict():
    result = evaluate(layout=_clean_layout(), router_result=_empty_router_result())
    assert "min_label_distance" in result.metrics
    assert "density" in result.metrics
    assert "wire_crossings" in result.metrics


def test_overlaps_failure_names_components():
    """Two placements at the same cell trigger `overlaps`."""
    layout = LayoutResult(placements={
        "A": Placement(ref="A", region="left-column", row=0),
        "B": Placement(ref="B", region="left-column", row=0),
    })
    result = evaluate(layout=layout, router_result=_empty_router_result())
    assert not result.passed
    overlap_findings = [f for f in result.failures if f.check == "overlaps"]
    assert overlap_findings, result.failures
    assert "A" in overlap_findings[0].refs and "B" in overlap_findings[0].refs


def test_labels_fit_failure_names_refs():
    """A label whose ref name exceeds the per-region budget fails."""
    layout = LayoutResult(placements={
        "VERY_LONG_REF_NAME_EXCEEDING_BUDGET": Placement(
            ref="VERY_LONG_REF_NAME_EXCEEDING_BUDGET",
            region="left-column",
            row=0,
            label="left",
        ),
    })
    result = evaluate(layout=layout, router_result=_empty_router_result())
    label_findings = [f for f in result.failures if f.check == "labels_fit"]
    assert label_findings, result.failures
    assert "VERY_LONG_REF_NAME_EXCEEDING_BUDGET" in label_findings[0].refs


def test_wire_crossings_failure_at_threshold_zero():
    """Default threshold is 0; any non-zero crossing fails."""
    routes = [
        WireRoute(
            net="N1",
            a=PinRef("A", "1"),
            b=PinRef("B", "1"),
            segments=(Segment(0, 0, 10, 0),),
        ),
    ]
    router_result = RouterResult(routes=routes, crossings=2, intra_component_intersections=0)
    result = evaluate(layout=_clean_layout(), router_result=router_result)
    crossing_findings = [f for f in result.failures if f.check == "wire_crossings"]
    assert crossing_findings, result.failures
    assert "2" in crossing_findings[0].message and "0" in crossing_findings[0].message


def test_wire_crossings_threshold_can_be_relaxed():
    """A configured threshold gates the rubric — useful for waiver paths."""
    router_result = RouterResult(routes=[], crossings=3, intra_component_intersections=0)
    result = evaluate(
        layout=_clean_layout(),
        router_result=router_result,
        wire_crossing_threshold=5,
    )
    assert result.passed, result.findings


def test_failing_rubric_aborts_with_structured_diagnostic():
    """A failure carries the check name and ref list, not just a bool."""
    layout = LayoutResult(placements={
        "A": Placement(ref="A", region="left-column", row=0),
        "B": Placement(ref="B", region="left-column", row=0),
    })
    result = evaluate(layout=layout, router_result=_empty_router_result())
    assert not result.passed
    for f in result.failures:
        assert f.check, f
        assert f.severity == "error", f
        assert f.message, f
        assert f.refs, f


def test_metrics_record_advisory_and_blocking_alike():
    """Both numeric advisory checks and the blocking-check counts are recorded."""
    router_result = RouterResult(routes=[], crossings=4, intra_component_intersections=1)
    result = evaluate(
        layout=_clean_layout(),
        router_result=router_result,
        wire_crossing_threshold=10,
    )
    assert result.metrics["wire_crossings"] == 4
    assert result.metrics["intra_component_intersections"] == 1
    assert "min_label_distance" in result.metrics
    assert "density" in result.metrics
