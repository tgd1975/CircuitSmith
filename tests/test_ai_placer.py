"""
AI-placer tests for TASK-017.

Anthropic API is mocked via a `FakeLLM` implementing the `LLMClient`
Protocol. The real `AnthropicClient` adapter is never instantiated
in this suite — ADR-0002 keeps AI off the CI path.

Covers the four acceptance criteria:
  1. §7.1 input contract — prompts carry topology, frozen layout, the
     ambiguity queue, capacities, and the slot vocabulary.
  2. Convergence loop terminates within the iteration cap; over-cap
     runs return `ai-cap-exceeded`.
  3. Per-iteration reason codes + cost (input/output tokens) are
     recorded; the `IterationRecord` log surfaces what the caller
     writes to `meta.yml.provenance` (TASK-020).
  4. AI placer "falls through" cleanly — non-success
     `ConvergenceResult` reasons drive the caller to write a
     `state: incomplete` meta.yml (no silent success path).
"""
from __future__ import annotations

import json


from circuit.layout_engine import LayoutResult, Placement
from circuit.layout_engine.ai_placer import (
    AmbiguityEntry,
    ConvergenceResult,
    DEFAULT_ITERATION_CAP,
    LLMClient,
    _build_system_prompt,
    _build_user_prompt,
    converge,
)


# ── Fakes ────────────────────────────────────────────────────────────────


class _FakeLLM(LLMClient):
    """Records every call; returns scripted responses round-robin."""

    def __init__(self, responses: list[tuple[str, int, int]]):
        self._responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def call(self, *, system: str, user: str) -> tuple[str, int, int]:
        self.calls.append((system, user))
        if not self._responses:
            raise RuntimeError("FakeLLM ran out of scripted responses")
        return self._responses.pop(0)


def _json_resp(placements: dict, in_tok: int = 100, out_tok: int = 50) -> tuple[str, int, int]:
    body = json.dumps({"placements": placements})
    return body, in_tok, out_tok


def _basic_circuit() -> dict:
    return {
        "meta": {"title": "ambiguous demo", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "X1": {"type": "passives/exotic"},
        },
        "connections": [
            {"net": "FOO", "pins": ["U1.D13", "X1.1"]},
        ],
    }


def _basic_frozen_layout() -> LayoutResult:
    return LayoutResult(placements={
        "U1": Placement(
            ref="U1",
            region="mcu-center",
            topology_fingerprint="sha1:aaaa",
        ),
    })


# ── 1. §7.1 input contract ──────────────────────────────────────────────


def test_system_prompt_lists_slot_vocabulary_and_capacities():
    system = _build_system_prompt({"left-column": 12, "right-column": 12})
    assert "mcu-center" in system
    assert "left-column" in system
    assert "right-column" in system
    assert "bus-<name>" in system
    assert "free" in system
    assert "left-column: 12" in system
    assert "right-column: 12" in system


def test_user_prompt_carries_topology_frozen_and_ambiguity():
    user = _build_user_prompt(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[
            AmbiguityEntry(ref="X1", reason="no-canonical-rule", detail="exotic 2-pin"),
        ],
        previous_feedback=None,
    )
    assert "Circuit topology" in user
    assert "Frozen placements" in user
    assert "U1: { region: mcu-center" in user
    assert "X1" in user
    assert "no-canonical-rule" in user


def test_user_prompt_includes_previous_feedback_on_retry():
    user = _build_user_prompt(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[
            AmbiguityEntry(ref="X1", reason="no-canonical-rule", detail="exotic 2-pin"),
        ],
        previous_feedback="X1 overlaps with U1 at mcu-center",
    )
    assert "Rubric feedback" in user
    assert "X1 overlaps with U1" in user


# ── 2. Convergence loop ──────────────────────────────────────────────────


def test_converges_on_first_try():
    fake = _FakeLLM([
        _json_resp({"X1": {"region": "left-column", "row": 0}}),
    ])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={"left-column": 12},
        client=fake,
        rubric_check=lambda proposals: (True, ""),
    )
    assert result.converged
    assert result.iterations == 1
    assert result.placements["X1"].region == "left-column"
    assert result.placements["X1"].row == 0
    assert result.total_input_tokens == 100
    assert result.total_output_tokens == 50


def test_converges_after_one_retry():
    """First proposal fails rubric; second proposal converges."""
    fake = _FakeLLM([
        _json_resp({"X1": {"region": "left-column", "row": 0}}, in_tok=80),
        _json_resp({"X1": {"region": "right-column", "row": 0}}, in_tok=90, out_tok=40),
    ])
    calls_seen = []

    def rubric_check(proposals):
        calls_seen.append(proposals["X1"].region)
        return (proposals["X1"].region == "right-column", "left-column row 0 collides with U1")

    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={"left-column": 12, "right-column": 12},
        client=fake,
        rubric_check=rubric_check,
    )
    assert result.converged
    assert result.iterations == 2
    assert calls_seen == ["left-column", "right-column"]
    # The second turn's user prompt must have carried the feedback.
    assert "left-column row 0 collides with U1" in fake.calls[1][1]
    assert result.total_input_tokens == 170


def test_caps_at_iteration_limit_with_ai_cap_exceeded():
    """Never-converges scenario hits the cap."""
    cap = 3
    fake = _FakeLLM([
        _json_resp({"X1": {"region": "left-column", "row": 0}}) for _ in range(cap)
    ])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={"left-column": 12},
        client=fake,
        rubric_check=lambda proposals: (False, "still wrong"),
        iteration_cap=cap,
    )
    assert result.reason == "ai-cap-exceeded"
    assert result.iterations == cap
    assert len(result.log) == cap


def test_default_iteration_cap_is_five():
    """§7.3 provisional cap."""
    assert DEFAULT_ITERATION_CAP == 5


# ── Cost accounting + reason-code per iteration ─────────────────────────


def test_iteration_log_records_per_round_cost_and_reason():
    fake = _FakeLLM([
        _json_resp({"X1": {"region": "left-column", "row": 0}}, in_tok=120, out_tok=30),
        _json_resp({"X1": {"region": "right-column", "row": 0}}, in_tok=130, out_tok=35),
    ])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={"left-column": 12, "right-column": 12},
        client=fake,
        rubric_check=lambda proposals: (proposals["X1"].region == "right-column", "wrong side"),
    )
    assert len(result.log) == 2
    assert result.log[0].input_tokens == 120
    assert result.log[0].output_tokens == 30
    assert result.log[0].rubric_passed is False
    assert result.log[0].rejection_reason == "wrong side"
    assert result.log[1].rubric_passed is True
    assert result.log[1].rejection_reason is None


# ── Structural failures (one-shot exit per §7.3) ────────────────────────


def test_invalid_json_returns_ai_output_invalid():
    fake = _FakeLLM([("not json at all", 50, 20)])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={"left-column": 12},
        client=fake,
        rubric_check=lambda proposals: (True, ""),
    )
    assert result.reason == "ai-output-invalid"
    assert result.iterations == 1


def test_attempt_to_move_frozen_component_rejected():
    fake = _FakeLLM([
        _json_resp({"U1": {"region": "left-column", "row": 0}}),
    ])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={"left-column": 12},
        client=fake,
        rubric_check=lambda proposals: (True, ""),
    )
    assert result.reason == "ai-frozen-violation"


def test_unknown_region_rejected():
    fake = _FakeLLM([
        _json_resp({"X1": {"region": "not-a-known-region", "row": 0}}),
    ])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={"left-column": 12},
        client=fake,
        rubric_check=lambda proposals: (True, ""),
    )
    assert result.reason == "ai-unknown-region"


def test_missing_component_in_response_rejected():
    """LLM addressed only one of two ambiguities."""
    fake = _FakeLLM([
        _json_resp({"X1": {"region": "left-column", "row": 0}}),  # Y1 missing
    ])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[
            AmbiguityEntry("X1", "no-canonical-rule", "exotic"),
            AmbiguityEntry("Y1", "no-canonical-rule", "another exotic"),
        ],
        capacity_map={"left-column": 12},
        client=fake,
        rubric_check=lambda proposals: (True, ""),
    )
    assert result.reason == "ai-missing-component"


def test_free_slot_requires_gx_gy():
    fake = _FakeLLM([
        _json_resp({"X1": {"region": "free"}}),  # no gx/gy
    ])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={},
        client=fake,
        rubric_check=lambda proposals: (True, ""),
    )
    assert result.reason == "ai-output-invalid"


def test_markdown_fences_are_stripped():
    """LLMs sometimes wrap JSON in ```json despite the prompt."""
    wrapped = "```json\n" + json.dumps({"placements": {"X1": {"region": "left-column", "row": 0}}}) + "\n```"
    fake = _FakeLLM([(wrapped, 80, 40)])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={"left-column": 12},
        client=fake,
        rubric_check=lambda proposals: (True, ""),
    )
    assert result.converged


# ── Token cap (cost safety net) ─────────────────────────────────────────


def test_token_cap_exits_with_dedicated_reason():
    fake = _FakeLLM([
        _json_resp({"X1": {"region": "left-column", "row": 0}}, in_tok=10_000, out_tok=5_000),
    ])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={"left-column": 12},
        client=fake,
        rubric_check=lambda proposals: (True, ""),
        token_cap=10_000,
    )
    assert result.reason == "ai-token-cap-exceeded"


# ── Fall-through path ───────────────────────────────────────────────────


def test_empty_ambiguity_queue_short_circuits_to_converged():
    """No ambiguities → no LLM call, immediate converged result."""
    fake = _FakeLLM([])
    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[],
        capacity_map={"left-column": 12},
        client=fake,
        rubric_check=lambda proposals: (False, "should not be called"),
    )
    assert result.converged
    assert result.iterations == 0
    assert fake.calls == []


def test_transport_failure_returns_ai_output_invalid():
    """A raised exception from the client is treated as a parse failure."""

    class _BrokenLLM(LLMClient):
        def call(self, *, system: str, user: str) -> tuple[str, int, int]:
            raise RuntimeError("simulated network error")

    result = converge(
        circuit=_basic_circuit(),
        frozen_layout=_basic_frozen_layout(),
        ambiguity_queue=[AmbiguityEntry("X1", "no-canonical-rule", "exotic")],
        capacity_map={"left-column": 12},
        client=_BrokenLLM(),
        rubric_check=lambda proposals: (True, ""),
    )
    assert result.reason == "ai-output-invalid"
    assert "simulated network error" in result.log[0].response_excerpt


def test_non_success_result_is_distinguishable_for_caller():
    """Caller writes `state: incomplete` whenever .converged is False."""
    failure_cases: list[ConvergenceResult] = [
        ConvergenceResult(reason="ai-cap-exceeded"),
        ConvergenceResult(reason="ai-output-invalid"),
        ConvergenceResult(reason="ai-frozen-violation"),
        ConvergenceResult(reason="ai-unknown-region"),
        ConvergenceResult(reason="ai-missing-component"),
        ConvergenceResult(reason="ai-token-cap-exceeded"),
    ]
    for r in failure_cases:
        assert r.converged is False, r
    assert ConvergenceResult(reason="converged").converged is True


# ── Portability smoke test ──────────────────────────────────────────────


def test_module_has_no_host_project_imports():
    import re
    from pathlib import Path
    src = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "circuit" / "layout_engine" / "ai_placer.py"
    text = src.read_text()
    forbidden = [
        r"\bimport\s+scripts\b",
        r"\bfrom\s+scripts\b",
        r"\bimport\s+data\b",
        r"\bfrom\s+data\b",
        r"\bCircuitSmith\b",
    ]
    leaks = [pat for pat in forbidden if re.search(pat, text)]
    assert not leaks, f"ai_placer.py leaks host-project tokens: {leaks}"
