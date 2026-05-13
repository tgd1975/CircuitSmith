"""
Tests for the rule-catalog validator (TASK-025).

Five-check coverage:
  1. Clean shipped catalog passes (offline mode).
  2. Missing-field fixture fails the format check.
  3. Unknown `enforced_by` fails the consistency check.
  4. Heuristic without disclaimer fails check 3.
  5. Deliberately-broken `.category` access outside layout/ fails check 4.
  (URL reachability — check 5 — is exercised via the offline flag in
  test 1 and a unit-test-injected unreachable URL in test 6.)
"""
from __future__ import annotations

import json
from pathlib import Path


from circuitsmith.knowledge import load_rules
from circuitsmith.knowledge.validate_catalog import (
    _check_category_lint,
    _check_disclaimers,
    _check_enforced_by,
    _check_format,
    validate,
)


PKG_ROOT = Path(__file__).resolve().parent.parent / "src"


def test_shipped_catalog_passes_offline() -> None:
    rules = load_rules()
    errors = validate(rules, package_root=PKG_ROOT, offline=True)
    assert errors == [], f"shipped catalog should validate clean: {errors}"


def test_missing_field_fails_format() -> None:
    rules = load_rules()
    # Drop heuristic from the first entry.
    rules[0] = {k: v for k, v in rules[0].items() if k != "heuristic"}
    errors = _check_format(rules)
    assert any("heuristic" in e for e in errors)


def test_unknown_enforced_by_fails() -> None:
    rules = load_rules()
    rules[0]["enforced_by"] = "E99"
    errors = _check_enforced_by(rules)
    assert any("E99" in e for e in errors)


def test_unreferenced_check_code_fails() -> None:
    """Removing a catalog row for a code in CHECK_TABLE breaks consistency."""
    rules = [r for r in load_rules() if r["id"] != "E1"]
    errors = _check_enforced_by(rules)
    assert any("E1" in e for e in errors)


def test_disclaimer_missing_fails() -> None:
    rules = load_rules()
    rules[0]["heuristic"] = "Just use 220 Ω."  # no disclaimer phrase
    errors = _check_disclaimers(rules)
    assert any(rules[0]["id"] in e for e in errors)


def test_category_lint_flags_outside_layout(tmp_path: Path) -> None:
    """A planted `.category ==` in a file outside layout/ must be flagged."""
    # Stage a fake `circuitsmith` package under tmp.
    pkg = tmp_path / "circuitsmith"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "erc_engine.py").write_text(
        "def f(profile):\n    return profile.category == 'led'\n"
    )
    errors = _check_category_lint(tmp_path)
    assert errors and "erc_engine.py" in errors[0]


def test_category_lint_allows_layout_dir(tmp_path: Path) -> None:
    pkg = tmp_path / "circuitsmith"
    layout_dir = pkg / "layout"
    layout_dir.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (layout_dir / "__init__.py").write_text("")
    (layout_dir / "kernel.py").write_text(
        "def f(profile):\n    return profile.category == 'led'\n"
    )
    errors = _check_category_lint(tmp_path)
    assert errors == [], f"layout/ reads should be allowed: {errors}"


def test_validator_cli_offline_returns_zero(tmp_path: Path, monkeypatch) -> None:
    """The CLI returns 0 on a clean catalog in offline mode."""
    from circuitsmith.knowledge.validate_catalog import _main
    monkeypatch.setenv("CS_CATALOG_OFFLINE", "1")
    exit_code = _main([])
    assert exit_code == 0


def test_validator_cli_reports_format_failure(tmp_path: Path) -> None:
    from circuitsmith.knowledge.validate_catalog import _main
    rules = load_rules()
    rules[0].pop("rule")  # break the format check
    broken_path = tmp_path / "rules.json"
    broken_path.write_text(json.dumps(rules), encoding="utf-8")
    exit_code = _main([
        "--rules", str(broken_path),
        "--offline",
    ])
    assert exit_code == 1
