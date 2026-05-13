"""
Tests for the Phase 2b gate in scripts/release_snapshot.py (TASK-059).

Four scenarios exercise the gate's decision tree:
  1. Trigger reports clean → release proceeds.
  2. Trigger fires + Phase 2b tasks all open → release refuses.
  3. Trigger fires + at least one Phase 2b task active/closed → proceeds.
  4. CS_PHASE2B_BYPASS set → release proceeds and bypass is logged.

The trigger script itself is mocked via stub paths so the test stays
hermetic.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_SCRIPT = REPO_ROOT / "scripts" / "release_snapshot.py"


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "ci@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "ci"], cwd=root, check=True)
    # Bare commit so HEAD exists; release_snapshot expects a real git tree.
    (root / ".gitkeep").write_text("")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)


def _write_meta_with_escalations(root: Path, *, non_addressable: int = 0, no_rule: int = 0) -> None:
    (root / "build").mkdir(exist_ok=True)
    entries: list[str] = []
    for _ in range(no_rule):
        entries.append("    - { category: no-canonical-rule, component: X, detail: x }")
    for _ in range(non_addressable):
        entries.append("    - { category: router-stall, detail: y }")
    if entries:
        block = "\n".join(entries)
    else:
        block = ""
    content = (
        "schema: circuit-meta/v1\n"
        "provenance:\n"
        "  tool: circuit-renderer\n"
        "  skill: x@0.0.0\n"
        "  ai_invoked: false\n"
        "  iterations: 0\n"
        f"  escalations:{'' if not entries else chr(10) + block}\n"
    )
    if not entries:
        content = content.replace("escalations:\n", "escalations: []\n")
    (root / "build" / "fixture.meta.yml").write_text(content)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "meta fixture"], cwd=root, check=True)


def _link_scripts(root: Path) -> Path:
    """Materialise a copy of `scripts/` inside the tmp repo so the gate's
    inner subprocess call (which uses `--repo-root` to locate the trigger
    script) finds `scripts/check_phase2b_trigger.py`."""
    target = root / "scripts"
    target.mkdir(exist_ok=True)
    for name in ("check_phase2b_trigger.py", "release_snapshot.py"):
        (target / name).write_text((REPO_ROOT / "scripts" / name).read_text())
    return target


def _write_tasks(root: Path, statuses: dict[str, str]) -> None:
    """Create stub task files in `docs/developers/tasks/<state>/`."""
    base = root / "docs" / "developers" / "tasks"
    for state in ("open", "active", "paused", "closed"):
        (base / state).mkdir(parents=True, exist_ok=True)
    for tid, state in statuses.items():
        num = tid.split("-")[1]
        path = base / state / f"task-{num}-stub.md"
        path.write_text(f"---\nid: {tid}\nstatus: {state}\n---\nstub\n")


def _run_release(root: Path, *, version="v0.1.0", env_extra: dict | None = None) -> tuple[int, str, str]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [
            sys.executable, str(RELEASE_SCRIPT), version,
            "--tasks-dir", str(root / "docs" / "developers" / "tasks"),
            "--repo-root", str(root),
            "--dry-run",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _phase2b_all_open() -> dict[str, str]:
    return {tid: "open" for tid in ("TASK-017", "TASK-018", "TASK-019", "TASK-020", "TASK-021")}


def test_gate_passes_when_no_escalations(tmp_path: Path):
    _init_repo(tmp_path)
    _link_scripts(tmp_path)
    _write_tasks(tmp_path, _phase2b_all_open())
    _write_meta_with_escalations(tmp_path)

    code, _stdout, stderr = _run_release(tmp_path)
    assert code == 0, stderr
    assert "phase2b gate: clean" in stderr


def test_gate_refuses_when_non_addressable_and_all_phase2b_open(tmp_path: Path):
    _init_repo(tmp_path)
    _link_scripts(tmp_path)
    _write_tasks(tmp_path, _phase2b_all_open())
    _write_meta_with_escalations(tmp_path, non_addressable=2)

    code, _stdout, stderr = _run_release(tmp_path)
    assert code == 3, stderr
    assert "REFUSING RELEASE" in stderr
    assert "router-stall" in stderr
    assert "Next action" in stderr


def test_gate_passes_when_phase2b_task_active(tmp_path: Path):
    _init_repo(tmp_path)
    _link_scripts(tmp_path)
    states = _phase2b_all_open()
    states["TASK-017"] = "active"
    _write_tasks(tmp_path, states)
    _write_meta_with_escalations(tmp_path, non_addressable=2)

    code, _stdout, stderr = _run_release(tmp_path)
    assert code == 0, stderr
    assert "response is underway" in stderr


def test_gate_bypass_logs_and_proceeds(tmp_path: Path):
    _init_repo(tmp_path)
    _link_scripts(tmp_path)
    _write_tasks(tmp_path, _phase2b_all_open())
    _write_meta_with_escalations(tmp_path, non_addressable=1)

    code, _stdout, stderr = _run_release(
        tmp_path,
        env_extra={"CS_PHASE2B_BYPASS": "shipping anyway, follow-up open"},
    )
    assert code == 0, stderr
    assert "BYPASS" in stderr
    log = (tmp_path / ".git" / "cs-phase2b-bypass.log").read_text()
    assert "shipping anyway" in log
    assert "router-stall" in log
