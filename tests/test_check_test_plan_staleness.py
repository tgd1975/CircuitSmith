"""
Tests for scripts/check_test_plan_staleness.py (TASK-091).

Each test constructs a temp repo root with a `tests/` dir and a
`docs/developers/testing/` plan, then asserts the gate's exit code and
stderr for the clean, missing-from-plan, dangling-reference, and nested
cases. The script is pure-stdlib, so `sys.executable` runs it without the
project venv.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check_test_plan_staleness.py"


def _seed(root: Path, test_files: list[str], referenced: list[str]) -> None:
    """Create test files and a one-chapter plan referencing `referenced`."""
    (root / "tests").mkdir(parents=True)
    for name in test_files:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def test_x():\n    assert True\n", encoding="utf-8")
    plan_dir = root / "docs" / "developers" / "testing"
    plan_dir.mkdir(parents=True)
    block = "\n".join(referenced)
    (plan_dir / "chapter.md").write_text(
        f"# Plan\n\n```pytest\n{block}\n```\n", encoding="utf-8"
    )


def _run(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_clean_plan_exits_zero(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        test_files=["tests/test_a.py", "tests/test_b.py"],
        referenced=["tests/test_a.py", "tests/test_b.py"],
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr


def test_missing_from_plan_fails(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        test_files=["tests/test_a.py", "tests/test_b.py", "tests/test_c.py"],
        referenced=["tests/test_a.py", "tests/test_b.py"],
    )
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "missing from plan" in result.stderr
    assert "tests/test_c.py" in result.stderr


def test_dangling_reference_fails(tmp_path: Path) -> None:
    _seed(
        tmp_path,
        test_files=["tests/test_a.py", "tests/test_b.py"],
        referenced=[
            "tests/test_a.py",
            "tests/test_b.py",
            "tests/test_phantom.py",
        ],
    )
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "dangling reference" in result.stderr
    assert "tests/test_phantom.py" in result.stderr


def test_nested_test_files_are_walked(tmp_path: Path) -> None:
    """Subdir tests (e.g. tests/layout/test_*.py) count toward the plan."""
    _seed(
        tmp_path,
        test_files=["tests/test_a.py", "tests/layout/test_rule.py"],
        referenced=["tests/test_a.py"],
    )
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "tests/layout/test_rule.py" in result.stderr
