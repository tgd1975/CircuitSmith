---
id: TASK-017
title: Implement layout_engine/ai_placer.py — convergence loop and reason codes
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Large (8-24h)
effort_actual: Medium (2-8h)
complexity: Senior
human-in-loop: Main
epic: circuit-renderer-layout
order: 10
prerequisites: [TASK-015]
---

## Description

Phase 2b deliverable — opens only when Phase 2a accumulates concrete
kernel-failure modes that a `§5.3` canonical-slot table addition cannot
retire. Implement `.claude/skills/circuit/layout_engine/ai_placer.py`
with the convergence loop, structured input contract, reason-code set,
and per-run token cap + cost accounting.

The AI placer is invoked by the kernel only when a `no-canonical-rule`
escalation fires — it is not the default path. The convergence loop
calibrates against the failure corpus accumulated during v0.1
operation (per the Phase 2b trigger gate in
`idea-001-circuit-skill.md`).

## Acceptance Criteria

- [x] `ai_placer.py` implements the full input contract from `idea-001.layout-engine-concept.md §7`. _`converge()` consumes circuit + frozen layout + ambiguity queue + capacity map; `_build_system_prompt()` lists the slot vocabulary + capacities; `_build_user_prompt()` carries topology, frozen state, ambiguities, and previous-iteration rubric feedback. Three input-contract tests verify._
- [x] Convergence loop terminates within the per-run token cap; over-cap runs fail-loud with an `ai-cap-exceeded` reason code. _Iteration cap defaults to 5 (`DEFAULT_ITERATION_CAP`); over-iteration returns `ai-cap-exceeded`. Cumulative `total_input_tokens + total_output_tokens > token_cap` returns `ai-token-cap-exceeded`. Two dedicated tests cover._
- [x] Reason-code set matches the spec; every AI invocation logs reason, attempt count, and total cost to `meta.yml.provenance`. _Per-iteration `IterationRecord` carries `iteration`, `input_tokens`, `output_tokens`, `response_excerpt`, `rubric_passed`, `rejection_reason`. The TASK-020 renderer change serialises these to `meta.yml.provenance.ai_invocations` (see TASK-020). Reason codes: `converged`, `ai-cap-exceeded`, `ai-output-invalid`, `ai-frozen-violation`, `ai-unknown-region`, `ai-missing-component`, `ai-token-cap-exceeded`._
- [x] AI placer falls through to a `free`-slot hand-authored layout entry if it cannot converge — no silent failure. _Non-success `ConvergenceResult` is the contract: `result.converged is False` for every failure reason. The caller (renderer, TASK-020) writes `meta.yml.layout.state: incomplete` and the operator is directed to hand-author a `free` slot per §7.3 options. `test_non_success_result_is_distinguishable_for_caller` enforces._

## Implementation notes

The AI placer module is path-agnostic and uses an injected `LLMClient`
Protocol so tests stay hermetic. The production `AnthropicClient`
adapter (thin wrapper over the official SDK) imports `anthropic`
lazily, keeping the unit-test path off the real API per ADR-0002.
Effort actual landed at Medium because the convergence loop is small
once the parse-validate-rubric-check shape is laid out; most of the
weight was the §7.1 input contract and the reason-code set.

## Test Plan

Add `tests/test_ai_placer.py` with mock Anthropic-API responses covering: successful convergence in one round, convergence in two rounds, cap-exceeded fail-loud path, and unrecoverable fail-through to manual layout.

## Prerequisites

- **TASK-015** — Phase 2a cutover must be complete and the failure corpus accumulated.

## Sizing rationale

Sized Large because the convergence loop, the reason-code set, the cost accounting, and the fail-loud paths must all be in place. Splitting "loop without reason codes" is shippable as a placeholder but does not satisfy the Phase 2b acceptance bar.

## Notes

This task is contingent — it opens only when the Phase 2b trigger gate
fires (see `idea-001-circuit-skill.md §Phase 2b`). The epic stays open
with this task in the backlog until the trigger fires.
