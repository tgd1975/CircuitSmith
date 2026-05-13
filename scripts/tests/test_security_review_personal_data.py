"""
Tests for the personal-data leak detection in
``scripts/security_review_changes.py`` (TASK-074 / EPIC-008).

Strategy: build a throwaway git repository in a ``tmp_path``, plant a
``personal_data_patterns.yml`` config at the project's expected location
(by monkeypatching ``PERSONAL_DATA_PATTERNS_PATH`` to a temp file),
stage a diff, and run the hook entry point against the two refs.

Three paths exercised:

- **clean** — added line contains no leak; exit 0, no findings.
- **leak** — added line contains the maintainer email pattern; exit
  non-zero, finding emitted with the rule name.
- **allowlisted** — same leak on a file that the config's allowlist
  exempts; exit 0, no finding.

The tests run as an ordinary pytest suite. The hook entry point is
called as a Python function — no subprocess shell, no second git
repo on disk beyond the throwaway one.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

# Import scripts/security_review_changes.py by file path so we don't depend
# on `scripts` being a Python package.
SCRIPT_PATH = Path(__file__).resolve().parent.parent / "security_review_changes.py"
_SPEC = importlib.util.spec_from_file_location("sr_changes", SCRIPT_PATH)
assert _SPEC and _SPEC.loader
sr_changes = importlib.util.module_from_spec(_SPEC)
sys.modules["sr_changes"] = sr_changes
_SPEC.loader.exec_module(sr_changes)


PATTERN_CONFIG = """
patterns:
  - rule: maintainer-email
    regex: "(?i)\\\\bmaintainer\\\\.test\\\\.NN@example\\\\.com\\\\b"
    severity: HIGH
    description: literal maintainer email
allowlist:
  - file: docs/allowed.md
    contains: maintainer.test.NN@example.com
    rule: maintainer-email
"""

LEAK_LINE = "Contact: maintainer.test.NN@example.com for questions.\n"
CLEAN_LINE = "Contact the maintainer via GitHub for questions.\n"


def _git(*args: str, cwd: Path) -> str:
    """Run a git subcommand in `cwd`, return stdout, raise on non-zero."""
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return result.stdout


def _init_repo(repo: Path) -> None:
    """Initialise a throwaway repo with one baseline commit."""
    repo.mkdir(parents=True, exist_ok=True)
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "test@example.invalid", cwd=repo)
    _git("config", "user.name", "test", cwd=repo)
    (repo / "README.md").write_text("# baseline\n")
    _git("add", "README.md", cwd=repo)
    _git("commit", "-q", "-m", "baseline", cwd=repo)


@pytest.fixture
def patched_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Set up a throwaway repo, plant the patterns config, patch globals.

    Yields a dict with ``repo`` (Path) and ``config`` (Path of the patterns
    file). The fixture monkeypatches the script's REPO_ROOT and
    PERSONAL_DATA_PATTERNS_PATH so the hook reads the temp file and
    diffs the temp repo.
    """
    repo = tmp_path / "repo"
    _init_repo(repo)

    config = tmp_path / "personal_data_patterns.yml"
    config.write_text(PATTERN_CONFIG)

    report_path = repo / ".claude" / "security-review-latest.md"

    monkeypatch.setattr(sr_changes, "REPO_ROOT", repo)
    monkeypatch.setattr(sr_changes, "PERSONAL_DATA_PATTERNS_PATH", config)
    monkeypatch.setattr(sr_changes, "REPORT_PATH", report_path)
    # The semantic-review pass would try to shell out to `claude`;
    # short-circuit it so the tests don't depend on the CLI being on PATH.
    monkeypatch.setenv("CS_SKIP_CLAUDE_REVIEW", "1")
    monkeypatch.chdir(repo)

    return {"repo": repo, "config": config, "report": report_path}


def _commit_line(repo: Path, file: str, line: str, msg: str) -> str:
    """Add (or replace) `file` with `line`, commit, return the new SHA."""
    path = repo / file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(line)
    _git("add", file, cwd=repo)
    _git("commit", "-q", "-m", msg, cwd=repo)
    return _git("rev-parse", "HEAD", cwd=repo).strip()


def _run_hook(old_ref: str, new_ref: str) -> tuple[int, list]:
    """Invoke main() with two refs; return (exit_code, findings)."""
    # main() reads sys.argv; build it manually.
    argv = [old_ref, new_ref, "--label", "test"]
    old_argv = sys.argv
    sys.argv = ["security_review_changes.py", *argv]
    try:
        rc = sr_changes.main()
    finally:
        sys.argv = old_argv
    # Drain the report's findings by re-parsing the report file — main()
    # writes them to disk, which is the contract the rest of the hook
    # chain expects. For the test, we read them off the in-memory
    # Report object indirectly via the file.
    findings = []
    if sr_changes.REPORT_PATH.exists():
        findings = [
            line for line in sr_changes.REPORT_PATH.read_text().splitlines()
            if "personal-data:" in line
        ]
    return rc, findings


def test_clean_diff_passes(patched_paths: dict) -> None:
    """A diff with no PII matches passes silently."""
    repo = patched_paths["repo"]
    old = _git("rev-parse", "HEAD", cwd=repo).strip()
    new = _commit_line(repo, "docs/note.md", CLEAN_LINE, "clean addition")
    rc, findings = _run_hook(old, new)
    assert rc == 0, f"clean diff failed unexpectedly; findings: {findings}"
    assert not findings, f"clean diff produced personal-data findings: {findings}"


def test_leaked_email_is_blocked(patched_paths: dict) -> None:
    """An added line containing the email pattern blocks the hook."""
    repo = patched_paths["repo"]
    old = _git("rev-parse", "HEAD", cwd=repo).strip()
    new = _commit_line(repo, "docs/leak.md", LEAK_LINE, "add email")
    rc, findings = _run_hook(old, new)
    assert rc != 0, "leak should have blocked the hook"
    assert findings, "expected at least one personal-data finding"
    assert any("maintainer-email" in line for line in findings), findings


def test_allowlisted_path_passes(patched_paths: dict) -> None:
    """The email on an allowlisted path is exempted; the hook passes."""
    repo = patched_paths["repo"]
    old = _git("rev-parse", "HEAD", cwd=repo).strip()
    new = _commit_line(repo, "docs/allowed.md", LEAK_LINE, "allowlisted")
    rc, findings = _run_hook(old, new)
    assert rc == 0, (
        f"allowlisted leak was blocked; findings: {findings}"
    )


def test_missing_config_silently_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the patterns file is absent, the scan is a no-op.

    The check is opt-in: contributors who don't maintain a local
    patterns file should not see noise. This test guards against a
    future refactor that accidentally inverts the default.
    """
    repo = tmp_path / "repo"
    _init_repo(repo)
    report_path = repo / ".claude" / "security-review-latest.md"

    monkeypatch.setattr(sr_changes, "REPO_ROOT", repo)
    monkeypatch.setattr(
        sr_changes,
        "PERSONAL_DATA_PATTERNS_PATH",
        tmp_path / "missing-on-purpose.yml",
    )
    monkeypatch.setattr(sr_changes, "REPORT_PATH", report_path)
    monkeypatch.setenv("CS_SKIP_CLAUDE_REVIEW", "1")
    monkeypatch.chdir(repo)

    old = _git("rev-parse", "HEAD", cwd=repo).strip()
    new = _commit_line(repo, "docs/leak.md", LEAK_LINE, "leak with no config")
    rc, findings = _run_hook(old, new)
    assert rc == 0, "leak should not block when config is absent"
    assert not findings, "no findings expected when config is absent"
