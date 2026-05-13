---
id: TASK-018
title: Add --no-ai fallback flag to layout.py
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-renderer-layout
order: 11
prerequisites: [TASK-017]
---

## Description

Add the `--no-ai` flag to `.claude/skills/circuit/layout.py` so
contributors without API access can still render — when `--no-ai` is
set, a `no-canonical-rule` escalation surfaces directly as a fail-loud
diagnostic instead of triggering the AI placer.

This is the contributor-friendly fallback per `layout §13`. It also
serves as the deterministic CI mode for cost-free runs.

## Acceptance Criteria

- [x] `renderer.py --no-ai` runs the kernel + router + rubric without invoking the AI placer. _CLI parses `--no-ai` / `--ai` as a mutually exclusive group; `--no-ai` is the default. Renderer's `use_ai_placer` parameter is `False` by default, so the Python API is hermetic for tests. `test_no_ai_flag_is_explicit_no_op_for_default` verifies._
- [x] A `no-canonical-rule` escalation under `--no-ai` produces a structured fail-loud diagnostic and non-zero exit code. _CLI exits with code 2 on `RenderError`; `meta.yml.layout.state: incomplete` is still written. `test_cli_defaults_to_no_ai` and `test_no_ai_path_fails_loud_on_no_canonical_rule` cover both the CLI and the Python-API paths._
- [x] The CI pipeline uses `--no-ai` by default — only triggered manually for AI-placer runs. _The renderer's API default is `use_ai_placer=False`, so `tests/test_full_pedal_fixture.py` (which CI runs under pytest) never reaches the AI placer. The CLI default also matches, which means anyone adding a direct CLI invocation to CI inherits the hermetic behaviour for free. ADR-0002 is the policy this satisfies._
- [x] Both shipped circuits pass under `--no-ai` (kernel-only path is sufficient). _`test_shipped_circuit_passes_under_no_ai` is parametrised over `esp32` and `nrf52840` and asserts `result.rubric.passed`, `ai_invoked: false`, and `escalations: []`._

## Implementation notes

The integration also required a small kernel refactor: `place()` gained
a `collect_escalations: bool = False` parameter so the AI placer can
see the full set of unplaceable components rather than the first one
the kernel hits. With `collect_escalations=False` (the default) the
behaviour is identical to TASK-009's original contract. The renderer
toggles the flag based on `use_ai_placer`.

The renderer's `_dispatch_ai_placer()` wires the `LLMClient` Protocol
to either the injected mock (tests) or the production `AnthropicClient`
adapter (lazy-imported, ADR-0002 compliant). The rubric-check callback
runs the proposed placements through the same router + rubric the
happy path uses — so AI proposals are validated against the same
contract as kernel placements.

## Test Plan

Add CLI integration test: `python layout.py --no-ai data/esp32.circuit.yml` produces the expected SVG; a synthetic circuit with no canonical-slot rule produces the expected fail-loud exit code.

## Prerequisites

- **TASK-017** — AI placer must exist so `--no-ai` has something to suppress.

## Notes

See `idea-001.layout-engine-concept.md §13`.
