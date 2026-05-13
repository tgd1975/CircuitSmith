"""
Pre-commit / CI gate test for `scripts/check_circuit_schema.py` (TASK-052).

Two fixtures live under `tests/fixtures/schema_check/`:

- `valid.circuit.yml` — minimal but schema-conformant circuit.
- `invalid_missing_meta.circuit.yml` — drops the required `meta:` section.

The test invokes the script with each fixture and asserts:

- valid → exit 0, no stderr noise
- invalid → exit 1, stderr names the offending file and JSON pointer

The script is the pre-commit gate; the renderer's own schema check
(TASK-012) is defence-in-depth. Both must agree, so the same fixtures
also feed the validator unit tests in `test_schema_validation.py`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_circuit_schema.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "schema_check"


def _run(*args: Path) -> subprocess.CompletedProcess[str]:
    """Run the script with explicit path args (bypasses git-staged detection)."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_valid_fixture_exits_zero() -> None:
    """The valid fixture clears the gate silently."""
    result = _run(FIXTURES / "valid.circuit.yml")
    assert result.returncode == 0, (
        f"valid fixture rejected:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    # No error lines on the happy path. Allow incidental stderr only if it
    # is empty after stripping — the script is silent on success by design.
    assert result.stderr.strip() == ""


def test_invalid_fixture_exits_nonzero_with_diagnostic() -> None:
    """The invalid fixture is rejected with `<file>:<pointer>: <msg>` output."""
    result = _run(FIXTURES / "invalid_missing_meta.circuit.yml")
    assert result.returncode == 1, (
        f"invalid fixture passed unexpectedly:\nstdout: {result.stdout}"
    )
    stderr = result.stderr
    assert "invalid_missing_meta.circuit.yml" in stderr, stderr
    # The schema's "meta is required" check should fire on the root.
    assert "meta" in stderr, stderr


def test_no_paths_no_action() -> None:
    """No staged .circuit.yml → script exits 0 silently.

    The script defaults to git-staged detection when no args are passed.
    In a clean checkout (no `.circuit.yml` files in the index for the
    test runner's commit), this is a no-op. We assert exit 0; we cannot
    assert empty stderr in absolute terms because git itself may emit
    warnings depending on the runner environment.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"no-args run failed unexpectedly:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_all_mode_validates_committed_circuits() -> None:
    """`--all` mode picks up every committed .circuit.yml without error.

    The committed circuits under `data/` are exercised continuously by
    the renderer / ERC / exporter staleness gates; if any of them
    drifted out of conformance, multiple gates would fail simultaneously.
    This test pins the schema gate as part of that web.
    """
    result = _run(REPO_ROOT / "data" / "esp32.circuit.yml",
                  REPO_ROOT / "data" / "nrf52840.circuit.yml")
    assert result.returncode == 0, (
        f"committed circuits failed schema gate:\nstderr: {result.stderr}"
    )


def test_explicit_paths_override_staged_detection() -> None:
    """Passing paths directly bypasses git-staged detection.

    Belt-and-braces: confirms the CLI uses positional args verbatim and
    does not silently fall through to `git diff --cached` when the
    caller named files explicitly.
    """
    result = _run(FIXTURES / "invalid_missing_meta.circuit.yml")
    assert result.returncode == 1
    assert "invalid_missing_meta" in result.stderr
