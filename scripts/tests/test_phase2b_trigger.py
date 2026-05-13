"""
Tests for scripts/check_phase2b_trigger.py (TASK-058).

Three fixture corpora exercise the observer:
  - empty:     no meta.yml files → all-zeros report.
  - mixed:     several meta.yml files with various categories → counts.
  - malformed: a meta.yml with a structurally-broken escalations field
               → script exits non-zero with a clear stderr message.

`git ls-files` runs against a fresh `git init`-ed tmp repo so the
test is hermetic (does not depend on the host repo state).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_phase2b_trigger.py"


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "ci@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "ci"], cwd=root, check=True)


def _commit(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=root, check=True)


def _run_script(root: Path) -> tuple[int, dict, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(root)],
        capture_output=True,
        text=True,
    )
    stdout = proc.stdout
    report = json.loads(stdout) if proc.returncode == 0 else {}
    return proc.returncode, report, proc.stderr


def test_empty_corpus_returns_all_zeros(tmp_path: Path):
    _init_git_repo(tmp_path)
    _commit(tmp_path, {"README.md": "no meta files here\n"})
    exit_code, report, stderr = _run_script(tmp_path)
    assert exit_code == 0
    assert report == {
        "total_escalations": 0,
        "by_category": {},
        "non_addressable_count": 0,
        "no_rule_count": 0,
        "circuits_with_escalations": [],
    }
    assert "clean" in stderr.lower(), stderr


def test_mixed_corpus_categorises_counts(tmp_path: Path):
    _init_git_repo(tmp_path)
    files = {
        "build/esp32.meta.yml": (
            "schema: circuit-meta/v1\n"
            "provenance:\n"
            "  tool: circuit-renderer\n"
            "  skill: x@0.0.0\n"
            "  ai_invoked: false\n"
            "  iterations: 0\n"
            "  escalations:\n"
            "    - { category: no-canonical-rule, component: U1, detail: 'foo' }\n"
            "    - { category: no-canonical-rule, component: U2, detail: 'bar' }\n"
            "    - { category: router-stall, detail: 'baz' }\n"
        ),
        "build/nrf52840.meta.yml": (
            "schema: circuit-meta/v1\n"
            "provenance:\n"
            "  tool: circuit-renderer\n"
            "  skill: x@0.0.0\n"
            "  ai_invoked: false\n"
            "  iterations: 0\n"
            "  escalations: []\n"
        ),
    }
    _commit(tmp_path, files)
    exit_code, report, _ = _run_script(tmp_path)
    assert exit_code == 0, report
    assert report["total_escalations"] == 3
    assert report["by_category"] == {"no-canonical-rule": 2, "router-stall": 1}
    assert report["no_rule_count"] == 2
    assert report["non_addressable_count"] == 1
    assert report["circuits_with_escalations"] == ["esp32.meta.yml"]


def test_malformed_meta_yml_fails_loudly(tmp_path: Path):
    _init_git_repo(tmp_path)
    _commit(tmp_path, {
        "build/bad.meta.yml": (
            "schema: circuit-meta/v1\n"
            "provenance:\n"
            "  escalations:\n"
            "    - not_a_mapping\n"  # malformed entry — string instead of dict
        ),
    })
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "malformed escalation" in proc.stderr


def test_only_committed_files_count(tmp_path: Path):
    """Working-tree-only meta.yml files do not contribute to the report."""
    _init_git_repo(tmp_path)
    _commit(tmp_path, {"README.md": "init\n"})
    # Drop a meta.yml that's NOT committed.
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "rogue.meta.yml").write_text(
        "schema: circuit-meta/v1\n"
        "provenance:\n"
        "  escalations:\n"
        "    - { category: router-stall }\n"
    )
    exit_code, report, _ = _run_script(tmp_path)
    assert exit_code == 0
    assert report["total_escalations"] == 0
