"""
AI placer — invoked only when the kernel raises `EscalationError`.

Phase 2b feature per idea-001.layout-engine-concept.md §7 and
ADR-0008 (Phase 2b on evidence). Never on the happy path; the
default v0.1 pipeline never reaches this module.

Architecture:

  - The kernel runs its deterministic placement first. If a component
    has no §5.3 canonical-slot rule (or any other ambiguity from the
    §7.1 reason-code set), it raises `EscalationError`.
  - The renderer catches the escalation, builds an `AmbiguityEntry`
    list, and invokes `converge()` from this module.
  - `converge()` runs a bounded loop (≤ 5 iterations per §7.3) where
    each iteration:
      1. Prompts the LLM with topology + frozen layout + ambiguity
         queue + capacities + slot vocabulary (§7.1 input contract).
      2. Parses the LLM's slot proposals (§7.2 output contract).
      3. Validates that no frozen component was reassigned.
      4. Hands the proposals to the caller's rubric-check callback.
      5. Returns on success; loops with the rubric's feedback otherwise.
  - On `ai-cap-exceeded` (iteration 6) or any structural failure the
    placer returns a non-success `ConvergenceResult` and the renderer
    writes `meta.yml.layout.state: incomplete` per §7.3.

`LLMClient` is the seam tests use to inject mock responses without
calling the real Anthropic API. Production code wires the
`AnthropicClient` adapter (a thin wrapper around the official SDK)
behind it.

Reason codes (TASK-020 extends `meta.yml.provenance` with these):
  - `converged` — rubric green, AI proposals accepted.
  - `ai-cap-exceeded` — hit iteration cap without converging.
  - `ai-output-invalid` — LLM returned unparseable JSON.
  - `ai-frozen-violation` — LLM proposed to move a frozen component.
  - `ai-unknown-region` — LLM proposed a region not in the vocabulary.
  - `ai-missing-component` — LLM did not address every ambiguity.
  - `ai-token-cap-exceeded` — cumulative token cost overshot the cap.

References:
  - idea-001.layout-engine-concept.md §7 — input/output, iteration cap
  - ADR-0008 — Phase 2b on evidence
  - ADR-0002 — AI only at authoring time, never in CI
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from circuit.layout_engine.kernel import LayoutResult

# Iteration cap from §7.3 (provisional pending v1 calibration). The cap's
# job is to bound cost and guarantee termination, not to hit a measured
# sweet spot — the v1 PR re-calibrates against the v0.1 failure corpus.
DEFAULT_ITERATION_CAP = 5

# Per-run token cap. The figure is conservative for "five Sonnet rounds
# with a moderately verbose topology"; the convergence-budget contract
# is iteration-cap-bounded, this is the safety net against a runaway
# prompt or output.
DEFAULT_TOKEN_CAP = 50_000

# Slot vocabulary the AI may emit. Mirrors `layout.schema.json` /
# `kernel.py` — kept duplicated here so a stray AI suggestion of a
# region we don't recognise is caught at parse time, not at schema
# validation time. The dynamic patterns (`path-of-…`, `bus-…`,
# `pin-symbol-…`) are matched separately by `_is_known_region()`.
STATIC_REGIONS = frozenset({
    "mcu-center",
    "left-column",
    "right-column",
    "top-row",
    "bottom-row",
    "free",
})

DYNAMIC_REGION_PREFIXES = ("path-of-", "bus-", "pin-symbol-")


# ── Data classes ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AmbiguityEntry:
    """One unplaceable component the kernel kicks up to the AI placer."""

    ref: str
    reason: str         # one of the §7.1 reason codes; e.g. "no-canonical-rule"
    detail: str         # human-readable detail (component / shape / hint)


@dataclass(frozen=True)
class AIPlacement:
    """One slot assignment the AI proposed.

    Grid-discrete per §7.2 — no raw coordinates except via `region: free`.
    """

    ref: str
    region: str
    row: int | None = None
    col: int | None = None
    position: float | None = None
    step: int | None = None
    attached_to: str | None = None
    attach_step: int | None = None
    label: str | None = None
    gx: int | None = None
    gy: int | None = None


@dataclass
class IterationRecord:
    """One round of the convergence loop, recorded for meta.yml provenance."""

    iteration: int
    input_tokens: int
    output_tokens: int
    response_excerpt: str       # first 200 chars of the LLM response
    rubric_passed: bool
    rejection_reason: str | None  # set when this iteration's output didn't converge


@dataclass
class ConvergenceResult:
    """Outcome of a `converge()` call."""

    reason: str                              # "converged" | "ai-cap-exceeded" | "ai-output-invalid" | …
    placements: dict[str, AIPlacement] = field(default_factory=dict)
    iterations: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    log: list[IterationRecord] = field(default_factory=list)

    @property
    def converged(self) -> bool:
        return self.reason == "converged"


class LLMClient(Protocol):
    """Pluggable LLM-call seam. Production = Anthropic SDK; tests = mock."""

    def call(self, *, system: str, user: str) -> tuple[str, int, int]:
        """Return `(response_text, input_tokens, output_tokens)`.

        Implementations should raise on transport failure; `converge()`
        treats raised exceptions as `ai-output-invalid`.
        """
        ...


RubricCheck = Callable[[dict[str, AIPlacement]], tuple[bool, str]]
"""Callback the caller wires up.

Takes the AI's proposed placements; returns `(passed, feedback)`. On
`False`, `feedback` is the rubric-side message the AI sees on the next
turn ("PWR_LED overlaps with BTN_A at slot left-column row=0"). On
`True`, `feedback` is ignored.
"""


# ── Convergence loop ─────────────────────────────────────────────────────


def converge(
    *,
    circuit: dict[str, Any],
    frozen_layout: LayoutResult,
    ambiguity_queue: list[AmbiguityEntry],
    capacity_map: dict[str, int],
    client: LLMClient,
    rubric_check: RubricCheck,
    iteration_cap: int = DEFAULT_ITERATION_CAP,
    token_cap: int = DEFAULT_TOKEN_CAP,
) -> ConvergenceResult:
    """
    Run the §7.3 convergence loop. Returns a `ConvergenceResult` whose
    `reason` field tells the caller what happened.

    Termination guarantees (§7.3):
      - Caps at `iteration_cap` (default 5). Iteration 6 is the
        `ai-cap-exceeded` exit.
      - Caps at cumulative `token_cap`. Exceeding it mid-loop returns
        `ai-token-cap-exceeded` even if iterations remain.
      - On any single-round structural failure (`ai-output-invalid`,
        `ai-frozen-violation`, …) the loop returns immediately — the
        AI doesn't get to keep emitting junk under the iteration cap.

    The caller is responsible for plumbing the resulting placements
    back through the kernel + router + rubric to validate them against
    the full pipeline. The `rubric_check` callback the caller injects
    is what the AI sees as feedback on the next turn.
    """
    if not ambiguity_queue:
        return ConvergenceResult(reason="converged")

    log: list[IterationRecord] = []
    total_input = 0
    total_output = 0
    last_feedback: str | None = None
    frozen_refs = frozenset(frozen_layout.placements)

    for iteration in range(1, iteration_cap + 1):
        system_prompt = _build_system_prompt(capacity_map)
        user_prompt = _build_user_prompt(
            circuit=circuit,
            frozen_layout=frozen_layout,
            ambiguity_queue=ambiguity_queue,
            previous_feedback=last_feedback,
        )

        try:
            response_text, in_tokens, out_tokens = client.call(
                system=system_prompt, user=user_prompt
            )
        except Exception as exc:
            return ConvergenceResult(
                reason="ai-output-invalid",
                iterations=iteration,
                total_input_tokens=total_input,
                total_output_tokens=total_output,
                log=log + [IterationRecord(
                    iteration=iteration,
                    input_tokens=0,
                    output_tokens=0,
                    response_excerpt=f"<transport error: {exc!r}>"[:200],
                    rubric_passed=False,
                    rejection_reason="ai-output-invalid",
                )],
            )

        total_input += in_tokens
        total_output += out_tokens

        if total_input + total_output > token_cap:
            return ConvergenceResult(
                reason="ai-token-cap-exceeded",
                iterations=iteration,
                total_input_tokens=total_input,
                total_output_tokens=total_output,
                log=log + [IterationRecord(
                    iteration=iteration,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    response_excerpt=response_text[:200],
                    rubric_passed=False,
                    rejection_reason="ai-token-cap-exceeded",
                )],
            )

        parse_result = _parse_response(
            response_text=response_text,
            expected_refs={entry.ref for entry in ambiguity_queue},
            frozen_refs=frozen_refs,
        )
        if isinstance(parse_result, str):
            # Parse failure surfaces as the reason; one-shot exit (§7.3).
            return ConvergenceResult(
                reason=parse_result,
                iterations=iteration,
                total_input_tokens=total_input,
                total_output_tokens=total_output,
                log=log + [IterationRecord(
                    iteration=iteration,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    response_excerpt=response_text[:200],
                    rubric_passed=False,
                    rejection_reason=parse_result,
                )],
            )

        proposals: dict[str, AIPlacement] = parse_result

        passed, feedback = rubric_check(proposals)
        log.append(IterationRecord(
            iteration=iteration,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            response_excerpt=response_text[:200],
            rubric_passed=passed,
            rejection_reason=None if passed else feedback,
        ))

        if passed:
            return ConvergenceResult(
                reason="converged",
                placements=proposals,
                iterations=iteration,
                total_input_tokens=total_input,
                total_output_tokens=total_output,
                log=log,
            )
        last_feedback = feedback

    return ConvergenceResult(
        reason="ai-cap-exceeded",
        iterations=iteration_cap,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        log=log,
    )


# ── Prompt construction ──────────────────────────────────────────────────


def _build_system_prompt(capacity_map: dict[str, int]) -> str:
    """The §7.1 system contract — slot vocabulary + invariants + capacities."""
    lines = [
        "You are the AI placer for the circuit-skill layout engine.",
        "Your job is to assign slot positions to components the deterministic",
        "kernel could not place.",
        "",
        "Rules (NON-NEGOTIABLE):",
        "  1. Output is JSON only. Top-level shape:",
        '       { "placements": { "<ref>": { "region": "...", ... } } }',
        "     Any other text in your response invalidates the run.",
        "  2. Use only the slot vocabulary below.",
        "  3. Never reassign a frozen component. If you reference one,",
        "     the run is rejected and you do not get another turn.",
        "  4. Grid-discrete only. The `free` region is the only place",
        "     raw coordinates (`gx`, `gy`) are allowed.",
        "  5. Attached components MUST omit row/col/position/step;",
        "     they inherit from their anchor via `attached-to`.",
        "",
        "Slot vocabulary:",
        '  - "mcu-center"           — at most one occupant.',
        '  - "left-column"          — index by `row` (0, 1, …).',
        '  - "right-column"         — index by `row`.',
        '  - "top-row"              — index by `col`.',
        '  - "bottom-row"           — index by `col`.',
        '  - "path-of-<REF.PIN>"    — index by `step` (0-based).',
        '  - "bus-<name>"           — index by `position` (0.0–1.0).',
        '  - "pin-symbol-<pin>"     — no index.',
        '  - "free"                 — requires `gx`, `gy` integers.',
        "",
        "Region capacities (rows/cols this run can accept):",
    ]
    for region in sorted(capacity_map):
        lines.append(f"  - {region}: {capacity_map[region]}")
    lines.append("")
    lines.append(
        "If you cannot place a component without violating these rules, "
        "emit it under `region: free` with explicit `gx`/`gy`."
    )
    return "\n".join(lines)


def _build_user_prompt(
    *,
    circuit: dict[str, Any],
    frozen_layout: LayoutResult,
    ambiguity_queue: list[AmbiguityEntry],
    previous_feedback: str | None,
) -> str:
    """Per-iteration user prompt: topology + frozen state + asks + feedback."""
    lines = ["## Circuit topology", "", "```yaml", _yaml_lite(circuit), "```", ""]
    lines.append("## Frozen placements (DO NOT CHANGE)")
    lines.append("")
    if frozen_layout.placements:
        lines.append("```yaml")
        lines.append("placements:")
        for ref in sorted(frozen_layout.placements):
            p = frozen_layout.placements[ref]
            lines.append(f"  {ref}: " + _placement_to_inline_yaml(p))
        lines.append("```")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Components needing slot assignment")
    lines.append("")
    for entry in ambiguity_queue:
        lines.append(f"- **{entry.ref}** — reason: `{entry.reason}` — {entry.detail}")
    if previous_feedback:
        lines.append("")
        lines.append("## Rubric feedback on your previous attempt")
        lines.append("")
        lines.append(previous_feedback)
    lines.append("")
    lines.append("Respond with the JSON object only — no prose, no markdown fences.")
    return "\n".join(lines)


def _yaml_lite(obj: Any, indent: int = 0) -> str:
    """Tiny inline-YAML formatter. We do not import ruamel here to keep
    the prompt format stable across ruamel versions."""
    pad = "  " * indent
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        out: list[str] = []
        for k in sorted(obj):
            v = obj[k]
            if isinstance(v, (dict, list)) and v:
                out.append(f"{pad}{k}:")
                out.append(_yaml_lite(v, indent + 1))
            else:
                out.append(f"{pad}{k}: {_yaml_scalar(v)}")
        return "\n".join(out)
    if isinstance(obj, list):
        if not obj:
            return "[]"
        return "\n".join(
            f"{pad}- {_yaml_scalar(item)}" if not isinstance(item, (dict, list))
            else f"{pad}-\n{_yaml_lite(item, indent + 1)}"
            for item in obj
        )
    return f"{pad}{_yaml_scalar(obj)}"


def _yaml_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, str) and any(ch in v for ch in (":", "{", "}", "[", "]", "#", ",")):
        return json.dumps(v)
    return str(v)


def _placement_to_inline_yaml(p: Any) -> str:
    parts: list[str] = []
    if p.region is not None:
        parts.append(f"region: {p.region}")
    if p.attached_to is not None:
        parts.append(f"attached-to: {p.attached_to}")
    if p.row is not None:
        parts.append(f"row: {p.row}")
    if p.col is not None:
        parts.append(f"col: {p.col}")
    if p.position is not None:
        parts.append(f"position: {p.position}")
    if p.step is not None:
        parts.append(f"step: {p.step}")
    return "{ " + ", ".join(parts) + " }"


# ── Response parsing ─────────────────────────────────────────────────────


def _parse_response(
    *,
    response_text: str,
    expected_refs: set[str],
    frozen_refs: set[str],
) -> dict[str, AIPlacement] | str:
    """Parse the LLM JSON output. Returns AIPlacement map on success, or a
    reason-code string on failure (e.g. `"ai-output-invalid"`)."""
    try:
        doc = json.loads(_strip_markdown_fences(response_text))
    except json.JSONDecodeError:
        return "ai-output-invalid"
    if not isinstance(doc, dict) or "placements" not in doc:
        return "ai-output-invalid"
    raw = doc["placements"]
    if not isinstance(raw, dict):
        return "ai-output-invalid"

    result: dict[str, AIPlacement] = {}
    for ref, slot in raw.items():
        if not isinstance(slot, dict):
            return "ai-output-invalid"
        if ref in frozen_refs:
            return "ai-frozen-violation"
        region = slot.get("region")
        if not isinstance(region, str) or not _is_known_region(region):
            return "ai-unknown-region"
        if region == "free" and ("gx" not in slot or "gy" not in slot):
            return "ai-output-invalid"
        result[ref] = AIPlacement(
            ref=ref,
            region=region,
            row=_safe_int(slot.get("row")),
            col=_safe_int(slot.get("col")),
            position=_safe_float(slot.get("position")),
            step=_safe_int(slot.get("step")),
            attached_to=slot.get("attached-to") if isinstance(slot.get("attached-to"), str) else None,
            attach_step=_safe_int(slot.get("attach-step")),
            label=slot.get("label") if isinstance(slot.get("label"), str) else None,
            gx=_safe_int(slot.get("gx")),
            gy=_safe_int(slot.get("gy")),
        )

    missing = expected_refs - set(result)
    if missing:
        return "ai-missing-component"

    return result


def _is_known_region(region: str) -> bool:
    if region in STATIC_REGIONS:
        return True
    return any(region.startswith(prefix) for prefix in DYNAMIC_REGION_PREFIXES)


def _strip_markdown_fences(text: str) -> str:
    """Tolerate the LLM wrapping its JSON in ```json fences despite the prompt."""
    stripped = text.strip()
    if stripped.startswith("```"):
        # Drop the opening fence and an optional language tag.
        lines = stripped.splitlines()
        if lines:
            lines = lines[1:]
        # Drop the closing fence if present.
        while lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return stripped


def _safe_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


# ── Production LLM client (Anthropic SDK adapter) ───────────────────────


class AnthropicClient:
    """Production `LLMClient` adapter — thin wrapper around the SDK.

    Imports `anthropic` lazily so unit tests (which never instantiate
    this class) don't require the SDK at import time. ADR-0002 — AI
    only at authoring time, never in CI — means this class must never
    be reachable from `pytest` runs; the renderer wires it only on
    `--ai` runs that the human invokes locally.
    """

    def __init__(self, *, model: str = "claude-sonnet-4-6", max_tokens: int = 4096):
        self._model = model
        self._max_tokens = max_tokens
        self._client = None

    def _client_handle(self):
        if self._client is None:
            import anthropic  # lazy import — see docstring
            self._client = anthropic.Anthropic()
        return self._client

    def call(self, *, system: str, user: str) -> tuple[str, int, int]:
        client = self._client_handle()
        msg = client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # `content` is a list of blocks; concatenate text blocks only.
        text = "".join(block.text for block in msg.content if getattr(block, "type", None) == "text")
        usage = getattr(msg, "usage", None)
        in_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        out_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        return text, in_tokens, out_tokens


__all__ = [
    "AIPlacement",
    "AmbiguityEntry",
    "AnthropicClient",
    "ConvergenceResult",
    "IterationRecord",
    "LLMClient",
    "RubricCheck",
    "converge",
    "DEFAULT_ITERATION_CAP",
    "DEFAULT_TOKEN_CAP",
]
