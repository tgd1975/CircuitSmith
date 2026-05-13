"""
Tests for the circuit-artefact regenerator that powers the pre-commit
hook trigger on `.circuit.yml` and component-profile changes (TASK-038).

The pytest layer here exercises the regenerator script's logic
(fingerprint-skip, render-and-stage, error handling) against a
freshly-copied data dir. The actual hook is a shell wrapper around
the same script; the script-level test covers the same behaviour
without the shell harness.

The acceptance criterion for "<5 s on shipped circuits" is enforced
by the fingerprint short-circuit, which makes the no-op case sub-
second; this test verifies the short-circuit fires when expected.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Importing the regenerator without polluting sys.path for the rest of
# the test suite: insert at the front for the import only, then remove.
sys.path.insert(0, str(SCRIPTS_DIR))
try:
    import regenerate_circuit_artefacts as regen
finally:
    sys.path.remove(str(SCRIPTS_DIR))


@pytest.fixture
def isolated_repo(tmp_path: Path, monkeypatch) -> Path:
    """Copy data/ + docs/builders/wiring/ into tmp_path and point the
    regenerator at it. The src/circuitsmith/components/ tree stays
    where it is (read-only for the test).

    The committed meta.yml carries the production fingerprint; we
    strip it so the first call in each test exercises the cold-start
    path."""
    data_dst = tmp_path / "data"
    wiring_dst = tmp_path / "docs" / "builders" / "wiring"
    shutil.copytree(REPO_ROOT / "data", data_dst)
    shutil.copytree(REPO_ROOT / "docs" / "builders" / "wiring", wiring_dst)
    for meta in wiring_dst.rglob("main-circuit.meta.yml"):
        out_lines = [
            line for line in meta.read_text().splitlines(keepends=True)
            if not line.lstrip().startswith(regen.FINGERPRINT_PREFIX)
        ]
        meta.write_text("".join(out_lines))
    monkeypatch.setattr(regen, "DATA_DIR", data_dst)
    monkeypatch.setattr(regen, "WIRING_DIR", wiring_dst)
    return tmp_path


def test_fingerprint_skip_on_unchanged_inputs(isolated_repo: Path, monkeypatch):
    # First run: fingerprint not yet written → must regenerate.
    skipped_first, written_first, err_first = regen.regenerate_target("esp32")
    assert err_first is None
    assert skipped_first is False
    assert written_first  # at least one artefact

    # Second run with no edits: fingerprint matches → skip render.
    skipped_second, written_second, err_second = regen.regenerate_target("esp32")
    assert err_second is None
    assert skipped_second is True
    assert written_second == []


def test_edit_to_circuit_yml_triggers_regen(isolated_repo: Path):
    # Prime the fingerprint.
    regen.regenerate_target("esp32")

    # Edit the circuit YAML — append a comment to flip the file bytes
    # without changing the rendered output materially.
    circuit_path = regen.DATA_DIR / "esp32.circuit.yml"
    circuit_path.write_text(circuit_path.read_text() + "\n# touched by test\n")

    skipped, written, err = regen.regenerate_target("esp32")
    assert err is None
    assert skipped is False
    assert written  # regen fired


def test_no_stage_flag_does_not_invoke_git(isolated_repo: Path, monkeypatch):
    # The --no-stage path should leave _git_add un-called even after
    # a regen happens. Patch _git_add to a sentinel that fails if hit.
    called = {"count": 0}

    def _fake_git_add(paths):
        called["count"] += 1

    monkeypatch.setattr(regen, "_git_add", _fake_git_add)
    # First run from cold: regen fires, but --no-stage suppresses git add.
    code = regen.main(["--targets", "esp32", "--no-stage"])
    assert code == 0
    assert called["count"] == 0


def test_main_returns_nonzero_on_unknown_target(isolated_repo: Path, capsys):
    code = regen.main(["--targets", "does-not-exist", "--no-stage"])
    assert code == 1
    err = capsys.readouterr().err
    assert "no circuit at" in err


def test_hook_script_recognises_circuit_yml_paths():
    """The pre-commit hook's `STAGED_RENDER_INPUTS` regex must match
    both `data/*.circuit.yml` and `src/circuitsmith/components/*.py`.
    Lightweight grep against the hook file rather than a shell run."""
    hook = (REPO_ROOT / "scripts" / "pre-commit").read_text()
    assert "regenerate_circuit_artefacts.py" in hook
    assert "data/.*\\.circuit\\.yml" in hook
    assert "src/circuitsmith/components/.*\\.py" in hook
    # Bypass-env handling still lives at the top of the hook.
    assert "CS_COMMIT_BYPASS" in hook
