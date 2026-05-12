"""
TASK-006 regression guard: the refactored generator must produce
content-equivalent SVG to the predecessor (the on-disk references at
`docs/builders/wiring/<target>/main-circuit.svg`).

Three matplotlib-injected fields vary across runs and installs:

1. `<dc:date>` — fresh per invocation
2. `<clipPath id="pXXXXXXXXXX">` / `url(#pXXXXXXXXXX)` — random per run
3. `<dc:title>Matplotlib vX.Y.Z...</dc:title>` — varies by mpl install

These three are normalised before comparison. Everything else must
match byte-for-byte. A failure here means the refactor changed
schematic content — either pin geometry, label, or symbol — which is
the regression we're guarding against. See ADR-0011 for why this is
content-identity rather than literal byte-identity.

The generator is invoked **in-process** by importing `main()` and
monkeypatching `sys.argv`. Earlier revisions used `subprocess.run` —
that worked, but coverage tools watching the pytest process never
saw the generator. In-process invocation closes that gap.

This test is **transient** per TASK-006's note: it is deleted by
EPIC-002 TASK-016 (cutover) when the new YAML-driven renderer takes
over and geometric identity intentionally changes per
`layout.md §16.2`.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "scripts" / "generate-schematic.py"
REFERENCES = {
    "esp32":    REPO_ROOT / "docs/builders/wiring/esp32/main-circuit.svg",
    "nrf52840": REPO_ROOT / "docs/builders/wiring/nrf52840/main-circuit.svg",
}


def _load_generator():
    """Import `scripts/generate-schematic.py` by path (hyphenated name)."""
    spec = importlib.util.spec_from_file_location("_cs_generator", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalise(svg: str) -> str:
    """Strip the three matplotlib-injected non-deterministic fields."""
    svg = re.sub(r"<dc:date>[^<]+</dc:date>", "<dc:date>N</dc:date>", svg)
    svg = re.sub(r"(#|id=\")p[0-9a-f]{10}", r"\1CLIP", svg)
    svg = re.sub(r"Matplotlib v[\d.]+", "Matplotlib vN", svg)
    return svg


@pytest.mark.parametrize("target", ["esp32", "nrf52840"])
def test_generator_matches_reference(target, tmp_path, monkeypatch):
    gen = _load_generator()
    out = tmp_path / f"{target}.svg"
    monkeypatch.setattr(
        sys, "argv",
        ["generate-schematic.py", "--target", target, "--output", str(out)],
    )
    gen.main()

    new = _normalise(out.read_text())
    ref = _normalise(REFERENCES[target].read_text())
    assert new == ref, (
        f"{target}: refactored generator output differs from reference "
        f"in schematic content (matplotlib non-determinism already stripped)."
    )
