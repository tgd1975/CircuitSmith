"""
Tests for scripts/check_gallery_regression.py (TASK-101).

The script walks `docs/users/tutorial/` and `docs/users/examples/`
for `*.circuit.yml`, re-runs the renderer, and diffs the output
against the committed artefacts. These tests construct a temp
gallery with one example whose committed SVG matches / drifts /
needs rebaseline, and assert the script's exit code + stderr.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check_gallery_regression.py"
SAMPLE_CIRCUIT = REPO_ROOT / "docs" / "users" / "tutorial" / "01-minimal-circuit.circuit.yml"
SAMPLE_DIR = SAMPLE_CIRCUIT.parent


def _venv_python() -> str:
    """Use the project venv interpreter if it exists; otherwise sys.executable."""
    venv = REPO_ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def _seed_gallery(dst: Path) -> Path:
    """Copy the step-1 tutorial artefacts into a temp gallery at <dst>.

    Returns the temp REPO_ROOT path the script should walk. Mirrors
    the production layout: docs/users/tutorial/<base>.<ext>.
    """
    tutorial = dst / "docs" / "users" / "tutorial"
    tutorial.mkdir(parents=True)
    base = SAMPLE_CIRCUIT.name.replace(".circuit.yml", "")
    for suffix in (
        ".circuit.yml",
        ".svg",
        ".layout.yml",
        ".meta.yml",
        ".erc-report.md",
    ):
        src = SAMPLE_DIR / f"{base}{suffix}"
        if src.exists():
            shutil.copy2(src, tutorial / src.name)
    # Empty examples dir so the walker doesn't fail on missing tree.
    (dst / "docs" / "users" / "examples").mkdir(parents=True)
    return dst


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Run the script with PYTHONPATH=src/ inside the temp repo."""
    env = {
        "PYTHONPATH": str(REPO_ROOT / "src"),
        "PATH": "/usr/bin:/bin",
    }
    return subprocess.run(
        [_venv_python(), str(SCRIPT), *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_clean_gallery_exits_zero(tmp_path: Path) -> None:
    repo = _seed_gallery(tmp_path)
    result = _run(repo)
    assert result.returncode == 0, (
        f"unexpected exit: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "ok docs/users/tutorial/01-minimal-circuit.circuit.yml" in result.stdout


def test_drifted_svg_fails(tmp_path: Path) -> None:
    repo = _seed_gallery(tmp_path)
    committed_svg = repo / "docs" / "users" / "tutorial" / "01-minimal-circuit.svg"
    # Mutate the committed SVG so the script sees drift on next run.
    committed_svg.write_bytes(committed_svg.read_bytes() + b"<!-- intentional drift -->")
    result = _run(repo)
    assert result.returncode == 1
    assert "FAIL docs/users/tutorial/01-minimal-circuit.circuit.yml" in result.stderr


def test_rebaseline_writes_and_then_passes(tmp_path: Path) -> None:
    repo = _seed_gallery(tmp_path)
    committed_svg = repo / "docs" / "users" / "tutorial" / "01-minimal-circuit.svg"
    committed_svg.write_bytes(committed_svg.read_bytes() + b"<!-- drift -->")
    # First pass — drift exists. Confirm it would fail without --rebaseline.
    drift_check = _run(repo)
    assert drift_check.returncode == 1
    # Rebaseline overwrites the committed artefacts with regenerated ones.
    rebase = _run(repo, "--rebaseline")
    assert rebase.returncode == 0, (
        f"rebaseline returncode={rebase.returncode} "
        f"stderr={rebase.stderr!r}"
    )
    # Subsequent check should pass.
    follow_up = _run(repo)
    assert follow_up.returncode == 0
    assert "ok docs/users/tutorial/01-minimal-circuit.circuit.yml" in follow_up.stdout


def test_circuit_without_committed_svg_is_skipped(tmp_path: Path) -> None:
    repo = _seed_gallery(tmp_path)
    # Drop the SVG so the entry has only a circuit + (stale) sidecars.
    (repo / "docs" / "users" / "tutorial" / "01-minimal-circuit.svg").unlink()
    result = _run(repo)
    assert result.returncode == 0
    assert "skip docs/users/tutorial/01-minimal-circuit.circuit.yml" in result.stdout


def test_empty_gallery_exits_zero(tmp_path: Path) -> None:
    # Just empty dirs.
    (tmp_path / "docs" / "users" / "tutorial").mkdir(parents=True)
    (tmp_path / "docs" / "users" / "examples").mkdir(parents=True)
    result = _run(tmp_path)
    assert result.returncode == 0
    assert "no circuits found" in result.stdout
