"""EPIC-014 / TASK-124 — schema-level coverage for the `pages:` partition."""
from __future__ import annotations

from circuitsmith.schema import validate_layout


def _clean_layout() -> dict:
    return {
        "schema": "layout/v1",
        "placements": {
            "U1": {"region": "mcu-center", "topology-fingerprint": "sha1:0000aaaa"},
            "D1": {
                "region": "left-column",
                "row": 0,
                "label": "left",
                "topology-fingerprint": "sha1:1111bbbb",
            },
        },
    }


def test_layout_without_pages_validates_as_today():
    """Coexistence: a `.layout.yml` with no `pages:` block remains valid."""
    assert validate_layout(_clean_layout()) == []


def test_pages_with_named_pages_and_per_placement_assignment():
    layout = _clean_layout()
    layout["pages"] = [
        {"name": "p1", "title": "Front end"},
        {"name": "p2"},  # title is optional
    ]
    layout["placements"]["U1"]["page"] = "p1"
    layout["placements"]["D1"]["page"] = "p2"
    assert validate_layout(layout) == []


def test_pages_duplicate_name_rejected():
    layout = _clean_layout()
    layout["pages"] = [{"name": "p1"}, {"name": "p1"}]
    findings = validate_layout(layout)
    assert any(
        f.check == "layout-pages-duplicate-name" and "'p1'" in f.message
        for f in findings
    ), findings


def test_placement_with_undeclared_page_rejected():
    layout = _clean_layout()
    layout["pages"] = [{"name": "p1"}]
    layout["placements"]["U1"]["page"] = "p_typo"
    findings = validate_layout(layout)
    assert any(
        f.check == "layout-page-undeclared" and "p_typo" in f.message
        for f in findings
    ), findings


def test_pages_empty_list_rejected_by_schema():
    """`pages:` is opt-in; if present, it must declare at least one page."""
    layout = _clean_layout()
    layout["pages"] = []
    findings = validate_layout(layout)
    assert any(f.check == "layout-schema" for f in findings), findings


def test_page_name_invalid_pattern_rejected():
    layout = _clean_layout()
    layout["pages"] = [{"name": "1bad"}]  # must start with letter or underscore
    findings = validate_layout(layout)
    assert any(f.check == "layout-schema" for f in findings), findings


def test_placement_page_invalid_pattern_rejected():
    layout = _clean_layout()
    layout["pages"] = [{"name": "p1"}]
    layout["placements"]["U1"]["page"] = "9wrong"
    findings = validate_layout(layout)
    assert any(f.check == "layout-schema" for f in findings), findings
