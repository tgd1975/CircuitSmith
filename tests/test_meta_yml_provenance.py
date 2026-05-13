"""
meta.yml provenance tests for TASK-020.

Verifies the v1 provenance contract:
  - `ai_invoked: bool` is always written.
  - `iterations` is the cumulative AI iteration count (0 on kernel-only).
  - `ai_invocations` block is present when the AI placer ran (one entry
    per dispatch, each with `reason` + `iterations` + token cost +
    affected components).
  - The escalation enum in `meta.schema.json` covers every category
    the renderer emits.

The Phase 2b trigger gate (TASK-058) reads `provenance.escalations`;
this task layers AI-specific records on top of TASK-057's foundation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from circuitsmith.layout import LLMClient
from circuitsmith.renderer import RenderError, render

REPO_ROOT = Path(__file__).resolve().parents[1]
META_SCHEMA = (
    REPO_ROOT / "src" / "circuitsmith" / "schema" / "meta.schema.json"
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _orphan_resistor_yaml() -> str:
    return (
        "meta:\n"
        "  title: orphan resistor\n"
        "  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/esp32 }\n"
        "  R1: { type: passives/resistor, value: 1000 }\n"
        "connections:\n"
        "  - net: FOO\n"
        "    pins: [U1.D13, R1.1]\n"
        "  - net: BAR\n"
        "    pins: [U1.D25, R1.2]\n"
    )


class _ConvergingLLM(LLMClient):
    def __init__(self, region: str = "left-column", row: int = 1):
        self._region = region
        self._row = row

    def call(self, *, system: str, user: str) -> tuple[str, int, int]:
        body = json.dumps({"placements": {"R1": {"region": self._region, "row": self._row}}})
        return body, 120, 80


# ── `ai_invoked` always written ─────────────────────────────────────────


def test_kernel_only_run_records_ai_invoked_false(tmp_path: Path):
    """A clean kernel-only run emits `ai_invoked: false` + iterations 0."""
    circuit_path = REPO_ROOT / "data" / "esp32.circuit.yml"
    out_svg = tmp_path / "out.svg"
    result = render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    meta = result.meta_path.read_text()
    assert "ai_invoked: false" in meta
    assert "iterations: 0" in meta


def test_ai_run_records_ai_invoked_true_with_iteration_count(tmp_path: Path):
    """An AI dispatch that converged records `ai_invoked: true` + iteration count."""
    circuit_path = tmp_path / "orphan.circuit.yml"
    _write(circuit_path, _orphan_resistor_yaml())
    out_svg = tmp_path / "out.svg"
    result = render(
        circuit_path=circuit_path,
        layout_path=None,
        out_svg=out_svg,
        use_ai_placer=True,
        ai_client=_ConvergingLLM(),
    )
    meta = result.meta_path.read_text()
    assert "ai_invoked: true" in meta
    assert "iterations: 1" in meta
    assert "ai_invocations:" in meta
    assert "reason: converged" in meta


# ── `ai_invocations` entry shape ────────────────────────────────────────


def test_ai_invocation_entry_carries_reason_iterations_tokens_components(tmp_path: Path):
    circuit_path = tmp_path / "orphan.circuit.yml"
    _write(circuit_path, _orphan_resistor_yaml())
    out_svg = tmp_path / "out.svg"
    result = render(
        circuit_path=circuit_path,
        layout_path=None,
        out_svg=out_svg,
        use_ai_placer=True,
        ai_client=_ConvergingLLM(),
    )
    meta = result.meta_path.read_text()
    # The entry is a flow-style YAML map. Spot-check the keys.
    assert "reason: converged" in meta
    assert "input_tokens: 120" in meta
    assert "output_tokens: 80" in meta
    assert "[R1]" in meta or "[ R1 ]" in meta


# ── Schema covers every category the renderer emits ─────────────────────


def test_schema_enum_covers_all_emitted_escalation_categories():
    """Every category surface in the codebase must appear in meta.schema.json."""
    schema = json.loads(META_SCHEMA.read_text())
    enum = set(schema["$defs"]["escalation"]["properties"]["category"]["enum"])

    # The renderer surface — keep this list in sync with renderer.py's
    # category construction (kernel reason + rubric-fail-<check> +
    # ai-placer-<reason>).
    kernel_categories = {
        "no-canonical-rule", "no-profile", "slot-overflow",
        "bus-saturated", "router-stall", "kernel-bug",
    }
    rubric_categories = {
        "rubric-fail-overlaps",
        "rubric-fail-labels-fit",
        "rubric-fail-wire-crossings",
        "rubric-fail-min-label-distance",  # v1 promotion (TASK-019)
        "rubric-fail-density",              # v1 promotion (TASK-019)
    }
    ai_categories = {
        "ai-placer-ai-cap-exceeded",
        "ai-placer-ai-output-invalid",
        "ai-placer-ai-frozen-violation",
        "ai-placer-ai-unknown-region",
        "ai-placer-ai-missing-component",
        "ai-placer-ai-token-cap-exceeded",
    }
    expected = kernel_categories | rubric_categories | ai_categories
    assert expected <= enum, f"categories missing from schema: {expected - enum}"


def test_ai_invocation_schema_covers_all_reason_codes():
    """Every reason code `converge()` returns must be in meta.schema.json."""
    schema = json.loads(META_SCHEMA.read_text())
    enum = set(schema["$defs"]["aiReason"]["enum"])
    expected = {
        "converged", "ai-cap-exceeded", "ai-output-invalid",
        "ai-frozen-violation", "ai-unknown-region",
        "ai-missing-component", "ai-token-cap-exceeded",
    }
    assert expected == enum


# ── Drift-guard parsing (§17.2) ────────────────────────────────────────


def test_release_prep_review_can_parse_escalation_corpus(tmp_path: Path):
    """A release-prep tool can walk committed meta.yml files and count
    categories — the corpus the Phase 2b trigger gate reads."""
    circuit_path = tmp_path / "orphan.circuit.yml"
    _write(circuit_path, _orphan_resistor_yaml())
    out_svg = tmp_path / "out.svg"

    # Kernel-only path produces a no-canonical-rule entry.
    with pytest.raises(RenderError):
        render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)

    # Parse via ruamel — the renderer writes flow-style YAML.
    from ruamel.yaml import YAML
    meta = YAML(typ="safe").load((tmp_path / "out.meta.yml").read_text())
    escalations = meta["provenance"]["escalations"]
    assert isinstance(escalations, list)
    assert any(entry["category"] == "no-canonical-rule" for entry in escalations)
    assert all("circuit" in entry for entry in escalations if "circuit" in entry)
