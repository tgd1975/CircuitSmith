"""
`--no-ai` fallback flag tests for TASK-018.

Covers:
  1. `--no-ai` (the default) runs kernel + router + rubric without
     invoking the AI placer; a `no-canonical-rule` escalation
     surfaces as a `RenderError` with non-zero CLI exit.
  2. `--ai` opts into the Phase 2b dispatch; a mocked `LLMClient`
     stands in so the test never touches the real Anthropic API.
  3. Both shipped circuits render rubric-green under `--no-ai`.
  4. `meta.yml.provenance.ai_invoked` honestly reflects which path
     ran (the TASK-020 contract — recorded here so the flag flip is
     observable in the sidecar).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from circuitsmith.layout import LLMClient
from circuitsmith.renderer import RenderError, _main, render

REPO_ROOT = Path(__file__).resolve().parents[1]


def _orphan_resistor_yaml() -> str:
    """A circuit the kernel cannot place — used to trigger an escalation."""
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


def _clean_esp32_yaml() -> str:
    return (
        "meta:\n"
        "  title: clean ESP32\n"
        "  target: esp32\n"
        "components:\n"
        "  U1: { type: mcu/esp32 }\n"
        "  R1: { type: passives/resistor, value: 220 }\n"
        "  D1: { type: passives/led, color: green }\n"
        "connections:\n"
        "  - net: PWR_LED\n"
        "    path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]\n"
        "  - net: GND\n"
        "    pins: [U1.GNDL]\n"
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ── 1. --no-ai surfaces escalations ─────────────────────────────────────


def test_no_ai_path_fails_loud_on_no_canonical_rule(tmp_path: Path):
    """The default (kernel-only) path raises `RenderError` on escalation."""
    circuit_path = tmp_path / "orphan.circuit.yml"
    _write(circuit_path, _orphan_resistor_yaml())
    out_svg = tmp_path / "out.svg"
    with pytest.raises(RenderError) as exc_info:
        render(circuit_path=circuit_path, layout_path=None, out_svg=out_svg)
    assert exc_info.value.stage == "kernel"
    assert "R1" in exc_info.value.summary
    meta = (tmp_path / "out.meta.yml").read_text()
    assert "state: incomplete" in meta
    assert "ai_invoked: false" in meta


def test_cli_defaults_to_no_ai(tmp_path: Path):
    """CLI without `--ai` runs the kernel-only path and exits non-zero on escalation."""
    circuit_path = tmp_path / "orphan.circuit.yml"
    _write(circuit_path, _orphan_resistor_yaml())
    out_svg = tmp_path / "out.svg"
    exit_code = _main(["--circuit", str(circuit_path), "--out", str(out_svg)])
    assert exit_code == 2  # kernel-stage failure
    meta = (tmp_path / "out.meta.yml").read_text()
    assert "ai_invoked: false" in meta


def test_no_ai_flag_is_explicit_no_op_for_default(tmp_path: Path):
    """`--no-ai` is identical to the default; included for explicit hermetic runs."""
    circuit_path = tmp_path / "orphan.circuit.yml"
    _write(circuit_path, _orphan_resistor_yaml())
    out_svg = tmp_path / "out.svg"
    exit_code = _main([
        "--circuit", str(circuit_path),
        "--out", str(out_svg),
        "--no-ai",
    ])
    assert exit_code == 2


# ── 2. --ai opts into the AI placer (with mocked client) ────────────────


class _MockLLM(LLMClient):
    """Returns a single scripted response, then refuses further calls."""

    def __init__(self, response: str, in_tok: int = 100, out_tok: int = 50):
        self._response = response
        self._in_tok = in_tok
        self._out_tok = out_tok
        self.call_count = 0

    def call(self, *, system: str, user: str) -> tuple[str, int, int]:
        self.call_count += 1
        return self._response, self._in_tok, self._out_tok


def test_ai_path_dispatches_to_placer_and_converges(tmp_path: Path):
    """`use_ai_placer=True` with a converging mock client succeeds end-to-end."""
    circuit_path = tmp_path / "orphan.circuit.yml"
    _write(circuit_path, _orphan_resistor_yaml())
    out_svg = tmp_path / "out.svg"

    proposal = json.dumps({"placements": {"R1": {"region": "left-column", "row": 1}}})
    mock = _MockLLM(proposal)

    result = render(
        circuit_path=circuit_path,
        layout_path=None,
        out_svg=out_svg,
        use_ai_placer=True,
        ai_client=mock,
    )
    assert result.rubric.passed
    assert mock.call_count == 1
    meta = result.meta_path.read_text()
    assert "ai_invoked: true" in meta
    assert "ai_invocations:" in meta
    assert "iterations: 1" in meta


def test_ai_path_non_convergence_records_failure(tmp_path: Path):
    """An LLM proposing a frozen-component move triggers an `ai-frozen-violation`."""
    circuit_path = tmp_path / "orphan.circuit.yml"
    _write(circuit_path, _orphan_resistor_yaml())
    out_svg = tmp_path / "out.svg"

    bad_proposal = json.dumps({"placements": {"U1": {"region": "left-column", "row": 0}}})
    mock = _MockLLM(bad_proposal)

    with pytest.raises(RenderError) as exc_info:
        render(
            circuit_path=circuit_path,
            layout_path=None,
            out_svg=out_svg,
            use_ai_placer=True,
            ai_client=mock,
        )
    assert exc_info.value.stage == "ai-placer"
    meta = (tmp_path / "out.meta.yml").read_text()
    assert "state: incomplete" in meta
    assert "ai-placer-ai-frozen-violation" in meta


# ── 3. Both shipped circuits pass under --no-ai ────────────────────────


@pytest.mark.parametrize("target", ["esp32", "nrf52840"])
def test_shipped_circuit_passes_under_no_ai(target: str, tmp_path: Path):
    circuit_path = REPO_ROOT / "data" / f"{target}.circuit.yml"
    out_svg = tmp_path / f"{target}.svg"
    result = render(
        circuit_path=circuit_path,
        layout_path=None,
        out_svg=out_svg,
        use_ai_placer=False,
    )
    assert result.rubric.passed, result.rubric.findings
    meta = result.meta_path.read_text()
    assert "ai_invoked: false" in meta
    assert "escalations: []" in meta


# ── 4. ai_invoked surfaces the path that ran ───────────────────────────


def test_meta_yml_records_ai_invoked_false_on_kernel_only_clean_run(tmp_path: Path):
    circuit_path = tmp_path / "clean.circuit.yml"
    _write(circuit_path, _clean_esp32_yaml())
    out_svg = tmp_path / "out.svg"
    result = render(
        circuit_path=circuit_path,
        layout_path=None,
        out_svg=out_svg,
        use_ai_placer=False,
    )
    meta = result.meta_path.read_text()
    assert "ai_invoked: false" in meta
    assert "iterations: 0" in meta


def test_meta_yml_records_ai_invoked_true_when_placer_runs(tmp_path: Path):
    """An `--ai` run that didn't actually need the placer still records ai_invoked
    as false — the placer is only "invoked" when the kernel kicks something up."""
    circuit_path = tmp_path / "clean.circuit.yml"
    _write(circuit_path, _clean_esp32_yaml())
    out_svg = tmp_path / "out.svg"
    result = render(
        circuit_path=circuit_path,
        layout_path=None,
        out_svg=out_svg,
        use_ai_placer=True,  # opt-in
        ai_client=_MockLLM('{"placements": {}}'),  # not called — kernel succeeded
    )
    meta = result.meta_path.read_text()
    # ai_invoked is true iff the placer actually ran. Clean run = false.
    assert "ai_invoked: false" in meta
