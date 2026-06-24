"""
Tests for scripts/check_doc_references.py (TASK-105).

Each test constructs a temp repo root with a few Markdown files and asserts
the gate's exit code and stderr. Covers the default class-1 link check (incl.
code-fence, external, and lifecycle-folder handling) and the opt-in
``--check-ids`` / ``--check-paths`` classes. The script is pure-stdlib, so
``sys.executable`` runs it without the project venv.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check_doc_references.py"


def _write(root: Path, relpath: str, content: str) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_clean_links_exit_zero(tmp_path: Path) -> None:
    _write(tmp_path, "docs/a.md", "# A\n\nSee [b](b.md).\n")
    _write(tmp_path, "docs/b.md", "# B\n")
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr


def test_broken_link_fails(tmp_path: Path) -> None:
    _write(tmp_path, "docs/a.md", "# A\n\nSee [gone](missing.md).\n")
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "broken link" in result.stderr
    assert "missing.md" in result.stderr


def test_external_link_ignored_by_default(tmp_path: Path) -> None:
    _write(tmp_path, "docs/a.md", "# A\n\n[site](https://example.com/x).\n")
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr


def test_links_inside_code_fence_ignored(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "docs/a.md",
        "# A\n\n```\nexample: [x](nope.md)\n```\n",
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr


def test_placeholder_target_ignored(tmp_path: Path) -> None:
    _write(tmp_path, "docs/a.md", "# A\n\nOutput at [svg](<doc>.circuits/<hash>.svg).\n")
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr


def test_lifecycle_folder_link_normalized(tmp_path: Path) -> None:
    """A link to tasks/open/task-001 resolves when the file is in closed/."""
    _write(tmp_path, "docs/developers/tasks/closed/task-001-foo.md", "# T1\n")
    _write(
        tmp_path,
        "a.md",
        "# A\n\nSee [T1](docs/developers/tasks/open/task-001-foo.md).\n",
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr


def test_phantom_task_link_fails(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "a.md",
        "# A\n\nSee [T999](docs/developers/tasks/open/task-999-foo.md).\n",
    )
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "task-999-foo.md" in result.stderr


def test_id_refs_checked_only_with_flag(tmp_path: Path) -> None:
    _write(tmp_path, "docs/a.md", "# A\n\nThis cites TASK-999 in prose.\n")
    assert _run(tmp_path).returncode == 0  # default: IDs not checked
    flagged = _run(tmp_path, "--check-ids")
    assert flagged.returncode == 1
    assert "TASK-999" in flagged.stderr


def test_id_ref_in_external_link_text_skipped(tmp_path: Path) -> None:
    _write(tmp_path, "docs/a.md", "# A\n\n[IDEA-999](https://example.com/idea).\n")
    result = _run(tmp_path, "--check-ids")
    assert result.returncode == 0, result.stderr


def test_code_path_checked_only_with_flag(tmp_path: Path) -> None:
    _write(tmp_path, "docs/a.md", "# A\n\nEdit `src/circuitsmith/nope.py`.\n")
    assert _run(tmp_path).returncode == 0  # default: paths not checked
    flagged = _run(tmp_path, "--check-paths")
    assert flagged.returncode == 1
    assert "broken code-path" in flagged.stderr
    assert "src/circuitsmith/nope.py" in flagged.stderr


def test_vendored_skills_skipped(tmp_path: Path) -> None:
    """Installed task-system skills (.claude/skills/ minus circuit/) are out of scope."""
    _write(tmp_path, ".claude/skills/ts-foo/SKILL.md", "# S\n\n[x](missing.md)\n")
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
