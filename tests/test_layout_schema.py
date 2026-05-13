"""
Layout-schema validation tests for TASK-013.

Covers:
  - A clean v0.1 layout validates.
  - Missing topology-fingerprint fails validation (the required field
    catches stale layout.yml from a pre-fingerprint kernel run).
  - Region-anchor overrides validate per their distinct sub-schema.
  - `attached-to` referencing a non-existent placement surfaces a clear error.
"""
from __future__ import annotations

from circuit.schema import validate_layout


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
            "R1": {
                "region": "right-column",
                "attached-to": "D1",
                "topology-fingerprint": "sha1:2222cccc",
            },
        },
    }


def test_clean_layout_validates():
    assert validate_layout(_clean_layout()) == []


def test_missing_topology_fingerprint_fails():
    layout = _clean_layout()
    del layout["placements"]["U1"]["topology-fingerprint"]
    findings = validate_layout(layout)
    assert any(f.check == "layout-schema" for f in findings), findings
    assert any("topology-fingerprint" in f.message for f in findings), findings


def test_attached_to_unknown_placement_surfaces_error():
    layout = _clean_layout()
    layout["placements"]["R1"]["attached-to"] = "DOES_NOT_EXIST"
    findings = validate_layout(layout)
    assert any(f.check == "layout-attached-to-unknown" for f in findings), findings


def test_attached_to_with_anchor_index_fields_rejected():
    layout = _clean_layout()
    # Per §4.2 attach-index-redundant: attached must not carry row/col/etc.
    layout["placements"]["R1"]["row"] = 0
    findings = validate_layout(layout)
    assert any(f.check == "layout-schema" for f in findings), findings


def test_free_slot_requires_gx_gy():
    layout = _clean_layout()
    layout["placements"]["FREE_THING"] = {
        "region": "free",
        "topology-fingerprint": "sha1:3333dddd",
    }
    findings = validate_layout(layout)
    assert any(f.check == "layout-schema" for f in findings), findings


def test_free_slot_with_gx_gy_validates():
    layout = _clean_layout()
    layout["placements"]["FREE_THING"] = {
        "region": "free",
        "gx": 3,
        "gy": -2,
        "topology-fingerprint": "sha1:3333dddd",
    }
    assert validate_layout(layout) == []


def test_region_anchor_overrides_validate():
    layout = _clean_layout()
    layout["region-anchor-overrides"] = {
        "right-column": {"dx": 1, "dy": 0},
    }
    assert validate_layout(layout) == []


def test_region_anchor_overrides_missing_dx_fails():
    layout = _clean_layout()
    layout["region-anchor-overrides"] = {
        "right-column": {"dy": 0},
    }
    findings = validate_layout(layout)
    assert any(f.check == "layout-schema" for f in findings), findings


def test_capacity_overrides_validate():
    layout = _clean_layout()
    layout["capacity-overrides"] = {"right-column": {"rows": 18}}
    assert validate_layout(layout) == []


def test_path_of_region_pattern_validates():
    layout = _clean_layout()
    layout["placements"]["C1"] = {
        "region": "path-of-U1.V33",
        "step": 0,
        "topology-fingerprint": "sha1:4444eeee",
    }
    assert validate_layout(layout) == []


def test_bus_region_pattern_validates():
    layout = _clean_layout()
    layout["placements"]["C1"] = {
        "region": "bus-V33",
        "position": 0.5,
        "topology-fingerprint": "sha1:5555ffff",
    }
    assert validate_layout(layout) == []


def test_unknown_schema_version_rejected():
    layout = _clean_layout()
    layout["schema"] = "layout/v999"
    findings = validate_layout(layout)
    assert any(f.check == "layout-schema" for f in findings), findings
