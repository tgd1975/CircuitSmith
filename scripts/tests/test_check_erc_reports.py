"""
Tests for scripts/check_erc_reports.py (TASK-029).

The script enforces:
  - Each shipped target's committed `erc-report.md` matches a freshly
    rendered report (modulo the date-line stamp).
  - The ERC stage produces no ERROR-level findings on either target.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path



def _load_script():
    repo_root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "check_erc_reports",
        repo_root / "scripts" / "check_erc_reports.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_erc_reports"] = module
    spec.loader.exec_module(module)
    return module


def test_committed_reports_match_renderer() -> None:
    """The shipped reports must be fresh — re-rendering them produces no diff."""
    script = _load_script()
    errors_esp32 = script.check_target("esp32")
    errors_nrf = script.check_target("nrf52840")
    assert errors_esp32 == [], errors_esp32
    assert errors_nrf == [], errors_nrf


def test_stale_report_fails(tmp_path: Path, monkeypatch) -> None:
    """A deliberately-edited committed report must fail the gate."""
    script = _load_script()
    target_dir = tmp_path / "docs" / "builders" / "wiring" / "esp32"
    target_dir.mkdir(parents=True)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    repo_root = Path(__file__).resolve().parents[2]
    # Copy the shipped circuit; tamper with the report so it diverges.
    (data_dir / "esp32.circuit.yml").write_text(
        (repo_root / "data" / "esp32.circuit.yml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (target_dir / "erc-report.md").write_text("TAMPERED CONTENT\n", encoding="utf-8")
    monkeypatch.setattr(script, "DATA_DIR", data_dir)
    monkeypatch.setattr(script, "WIRING_DIR", tmp_path / "docs" / "builders" / "wiring")
    errors = script.check_target("esp32")
    assert errors and "stale" in errors[0]


def test_main_exit_zero_on_clean_repo() -> None:
    script = _load_script()
    exit_code = script.main([])
    assert exit_code == 0
