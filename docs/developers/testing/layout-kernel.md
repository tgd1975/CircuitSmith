---
subsystem: layout-kernel
covers: src/circuitsmith/layout/{kernel,rubric,ai_placer}.py
---

# Layout kernel — test plan

The layout engine turns a `NetGraph` into placed components. It is three
modules with distinct test shapes: the **kernel** (deterministic
canonical-slot placer, mostly golden/snapshot assertions), the
**rubric** (post-placement structural scorer, mostly threshold unit
tests), and the **AI placer** (Phase 2b convergence loop, mostly mocked
LLM tests — never on the CI path, per ADR-0002). The Manhattan router is
a separate stage with its own chapter ([`router.md`](router.md)).

Covers [`kernel.py`](../../../src/circuitsmith/layout/kernel.py),
[`rubric.py`](../../../src/circuitsmith/layout/rubric.py),
[`ai_placer.py`](../../../src/circuitsmith/layout/ai_placer.py).

Test files covering this subsystem:

```pytest
tests/test_kernel.py
tests/test_rubric.py
tests/test_rubric_v1.py
tests/test_ai_placer.py
tests/test_no_ai_flag.py
tests/layout/test_rc_low_pass_rule.py
tests/layout/test_rc_high_pass_rule.py
tests/layout/test_cc_decoupling_rule.py
tests/layout/test_rr_divider_rule.py
tests/layout/test_bjt_load_degeneration_rules.py
tests/layout/test_pullup_ic_anchor.py
tests/layout/test_page_propagation.py
tests/components/test_bjt_profiles.py
```

## Inputs and outputs

- **Kernel** — `place(circuit, graph, profiles, previous_layout=None)`
  → `LayoutResult(placements, capacity_overrides)`; `render_layout_yaml`
  serialises to `layout/v1` text. `previous_layout` enables incremental
  re-placement keyed on per-placement `topology_fingerprint`.
- **Rubric** — `evaluate(layout, router_result, …thresholds)` →
  a result with `.passed`, `.failures` (structured `check`/`refs`/
  `message`), and a `.metrics` dict.
- **AI placer** — `converge(circuit, frozen_layout, ambiguity_queue,
  capacity_map, client, rubric_check, …caps)` → `ConvergenceResult`
  (`.converged`, `.reason`, `.iterations`, `.log`, token totals). The
  `LLMClient` is a Protocol; tests inject a fake.

## Unit tests

**Kernel** (`tests/test_kernel.py`, TASK-009): deterministic placement
for esp32-like and nrf52840-like circuits (MCU at `mcu-center`, passives
to the pin-side column, resistor `attached-to` its LED inheriting the
anchor's region); byte-identical `render_layout_yaml` across two runs;
the `schema: layout/v1` header; a `topology-fingerprint` on every
placement; and the fail-loud `EscalationError(reason="no-canonical-rule")`
for an unknown component category and for an orphan resistor.

**Canonical-slot rules** (EPIC-014): one test file per rule pins the
specific slot a topology resolves to —
`tests/layout/test_rc_low_pass_rule.py` (TASK-111),
`…rc_high_pass…` (TASK-112), `…cc_decoupling…` (TASK-113),
`…rr_divider…` (TASK-114), `…bjt_load_degeneration…` (TASK-129, the
collector-load + emitter-degeneration rules), `…pullup_ic_anchor…`
(TASK-130, pull-up anchoring widened to IC `SIGNAL_INPUT` pins), and
`…page_propagation…` (TASK-124, `Placement.page` carried end-to-end).
The BJT base-drive rule is exercised by
`tests/components/test_bjt_profiles.py` (TASK-120), shared with
[`schema.md`](schema.md).

**Rubric v0.1** (`tests/test_rubric.py`, TASK-011): the three blocking
checks (`overlaps`, `labels_fit`, `wire_crossings`) pass on a clean
layout and each fail with a structured diagnostic naming the offending
refs; advisory metrics (`min_label_distance`, `density`,
`wire_crossings`, `intra_component_intersections`) land in `.metrics`;
the crossing threshold is configurable (waiver path).

**Rubric v1** (`tests/test_rubric_v1.py`, TASK-019): `min_label_distance`
and `density` promoted from advisory to blocking, with defaults
(`1`, `0.5`) derived from the Phase 2a green corpus's 75th percentile;
`None` thresholds restore v0.1 advisory-only behaviour (metrics still
recorded); both shipped circuits pass at the defaults.

**AI placer** (`tests/test_ai_placer.py`, TASK-017): the §7.1 prompt
contract (system prompt lists slot vocabulary + capacities; user prompt
carries topology, frozen placements, ambiguity queue, and prior
rubric feedback on retry); convergence on first try and after a
feedback retry; the iteration cap returning `ai-cap-exceeded`
(`DEFAULT_ITERATION_CAP == 5`); per-iteration cost + reason logging;
the structural one-shot-exit reasons (`ai-output-invalid`,
`ai-frozen-violation`, `ai-unknown-region`, `ai-missing-component`,
`ai-token-cap-exceeded`); markdown-fence stripping; and fall-through
(empty queue short-circuits with zero LLM calls; a transport exception
degrades to `ai-output-invalid`). All via an injected `_FakeLLM` — the
real `AnthropicClient` is never constructed.

## Integration tests

`tests/test_no_ai_flag.py` (TASK-018) drives the placer through the
renderer: the default `--no-ai` path runs kernel + router + rubric and
surfaces an escalation as a `RenderError` (CLI exit 2) with
`state: incomplete` / `ai_invoked: false` in the meta sidecar; `--ai`
dispatches to the placer with a mocked client and records
`ai_invoked: true` + `ai_invocations` on convergence; both shipped
circuits render rubric-green under `--no-ai` with `escalations: []`. The
meta-sidecar provenance is covered in depth by `tests/test_meta_yml_*`
(see [`renderer.md`](renderer.md)).

## Golden / snapshot tests

The kernel's determinism guarantees are snapshot-style: byte-identical
`layout/v1` output across runs, and the incremental-placement property
(`test_adding_one_led_pair_produces_minimal_diff` — adding a component
adds exactly its lines and moves nothing else; a `topology-fingerprint`
mismatch forces re-placement). There is no separate golden file; the
upstream NetGraph golden ([`netgraph.md`](netgraph.md)) anchors the
input side.

## Property / fuzz tests

**None true-property.** The incremental-diff and determinism guarantees
read like properties but are asserted on fixed fixtures, not generated
circuits. See *Known uncovered*.

## Performance budget

**No budget for kernel/rubric** — both are fast on every shipped
circuit. The AI placer is LLM-latency-bound in production but mocked in
tests; its cost safety nets (`iteration_cap`, `token_cap`) are unit-
tested rather than timed.

## Known uncovered cases

- **The real `AnthropicClient` transport adapter.** By design (ADR-0002)
  the AI path is mocked in CI, so the adapter that actually calls the
  Anthropic API has no automated coverage. Rationale: keeping live LLM
  calls off CI is the explicit policy; the adapter is thin and exercised
  manually. Flagged for TASK-090.
- **Rubric thresholds from a 2-circuit corpus.** The v1 defaults are
  derived from two shipped circuits; the 75th-percentile floor is
  under-sampled. Rationale: the corpus grows with the gallery
  (EPIC-012); revisit when it is larger.
- **No property-based placement fuzzing.** Determinism / incremental
  diff are example-tested. Rationale: the golden + canonical-rule tests
  catch real drift; generated-circuit fuzzing is a lower-priority
  follow-up.

## Cadence

| Test file | PR | Nightly | Release |
|---|:--:|:--:|:--:|
| `tests/test_kernel.py` | ✓ | | |
| `tests/test_rubric.py` | ✓ | | |
| `tests/test_rubric_v1.py` | ✓ | | |
| `tests/test_ai_placer.py` | ✓ | | |
| `tests/test_no_ai_flag.py` | ✓ | | |
| `tests/layout/test_*_rule*.py` (7 files) | ✓ | | |
| `tests/components/test_bjt_profiles.py` | ✓ | | |

All run at PR-time. The AI-placer tests are PR-safe precisely because
they inject a fake `LLMClient`; a live-API smoke test, if ever added,
would belong in a release-only tier (it costs tokens) — currently a gap.
