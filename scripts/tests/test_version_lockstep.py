"""Assert circuitsmith.__version__ == pyproject.toml [project] version.

The package version is mirrored across two files
(`src/circuitsmith/__init__.py` and `pyproject.toml`). A drift between
them is a shipping bug — the wheel reports one version while
`import circuitsmith` reports another. RELEASING.md § Version lockstep
documents the contract; this test enforces it.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_INIT = REPO_ROOT / "src" / "circuitsmith" / "__init__.py"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _read_dunder_version() -> str:
    text = PACKAGE_INIT.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, f"__version__ not found in {PACKAGE_INIT}"
    return match.group(1)


def _read_pyproject_version() -> str:
    # Scoped read: only the `[project]` table's `version` field, not
    # any `version` field that may appear under `[tool.*]` tables.
    text = PYPROJECT.read_text(encoding="utf-8")
    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_project = stripped == "[project]"
            continue
        if in_project and stripped.startswith("version"):
            match = re.match(r'version\s*=\s*"([^"]+)"', stripped)
            assert match, f"unexpected version line in {PYPROJECT}: {line!r}"
            return match.group(1)
    raise AssertionError(f"[project] version not found in {PYPROJECT}")


def test_version_lockstep() -> None:
    dunder = _read_dunder_version()
    pyproj = _read_pyproject_version()
    assert dunder == pyproj, (
        f"Version drift between files:\n"
        f"  src/circuitsmith/__init__.py __version__ = {dunder!r}\n"
        f"  pyproject.toml [project] version = {pyproj!r}\n"
        f"Bump both files together — see RELEASING.md § Version lockstep."
    )
