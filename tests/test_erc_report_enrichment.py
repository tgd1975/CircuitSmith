"""
ERC report-writer tests for TASK-027.

Covers:
  - Every non-OK finding carries the three-paragraph enrichment block.
  - Lookup is by check code (no fuzzy matching).
  - Missing-catalog-row produces CatalogLookupError, not silent skip.
  - Snapshot-style structural assertion on the rendered Markdown.
"""
from __future__ import annotations

from datetime import date

import pytest

from circuitsmith.erc_engine import EMPTY, Finding
from circuitsmith.erc_report import CatalogLookupError, render_report


_FIXED_DATE = date(2026, 5, 13)


def _warning_finding() -> Finding:
    return Finding(
        check="E9", severity="warning",
        ref="J1", pin="VBUS", net="VCC",
        message="power input pin J1.VBUS on net 'VCC' has no diode or P-MOSFET protection element.",
    )


def _error_finding() -> Finding:
    return Finding(
        check="E2", severity="error",
        ref="D1", pin="A", net="LED",
        message="LED D1.A on path net 'LED' has no current-limit resistor.",
    )


def test_warning_finding_includes_enrichment_block() -> None:
    md = render_report(
        [_warning_finding()],
        title="ESP32 default build",
        target="esp32",
        today=_FIXED_DATE,
    )
    assert "## ⚠️ J1.VBUS — E9" in md
    assert "**Why.**" in md
    assert "**Senior's tip.**" in md
    assert "**Source.**" in md


def test_error_finding_includes_enrichment_block() -> None:
    md = render_report(
        [_error_finding()],
        title="bad LED",
        target="esp32",
        today=_FIXED_DATE,
    )
    assert "## ❌ D1.A — E2" in md
    assert "**Why.**" in md
    assert "elektronik-kompendium.de" in md or "allaboutcircuits.com" in md


def test_missing_catalog_row_raises() -> None:
    """A check code without a catalog row must surface fail-loud."""
    finding = Finding(
        check="EX99", severity="warning",
        ref="X", pin="P", net="N",
        message="custom finding from a non-shipped check",
    )
    with pytest.raises(CatalogLookupError) as exc:
        render_report(
            [finding],
            title="t",
            target="t",
            today=_FIXED_DATE,
            catalog=[],  # explicitly empty
        )
    assert "EX99" in str(exc.value)


def test_header_carries_title_and_date() -> None:
    md = render_report(
        [_warning_finding()],
        title="My Circuit",
        target="esp32",
        today=_FIXED_DATE,
    )
    assert "# ERC Report — My Circuit — 2026-05-13" in md


def test_table_emits_em_dash_for_empty_fields() -> None:
    """Circuit-wide findings (E8) use em-dash in both Ref and Pin per spec."""
    e8 = Finding(
        check="E8", severity="warning",
        ref=EMPTY, pin=EMPTY, net=EMPTY,
        message="LED total current 250 mA exceeds budget 200 mA.",
    )
    md = render_report(
        [e8],
        title="t",
        target="esp32",
        today=_FIXED_DATE,
    )
    # The table row must show the em-dash literal in the empty columns.
    table_lines = [line for line in md.splitlines() if line.startswith("| ")]
    # Header + finding row.
    assert any("—" in line for line in table_lines), table_lines


def test_lookup_is_strict_by_check_code() -> None:
    """A custom catalog must be respected; lookup goes only via `id`."""
    custom = [
        {
            "id": "E2",
            "category": "test",
            "keywords": [],
            "rule": "custom rule",
            "explanation": "CUSTOM_EXPLAIN",
            "heuristic": "starting point — custom",
            "source_of_truth": "https://example.test/",
            "enforced_by": "E2",
        }
    ]
    md = render_report(
        [_error_finding()],
        title="t",
        target="t",
        today=_FIXED_DATE,
        catalog=custom,
    )
    assert "CUSTOM_EXPLAIN" in md
