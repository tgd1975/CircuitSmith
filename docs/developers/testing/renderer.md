---
subsystem: renderer
covers: src/circuitsmith/renderer.py
---

# Renderer — test plan

The renderer is the pipeline driver and the visual sink: it loads a
`.circuit.yml`, runs schema → NetGraph → ERC → kernel → router → rubric,
and emits the SVG plus the `.layout.yml` / `.meta.yml` sidecars (and,
for multi-page layouts, one SVG per page). Its test surface is dominated
by **golden-SVG comparison** and **fail-loud staging** — a malformed
circuit must halt with a structured `RenderError`, never a half-rendered
SVG.

Covers [`renderer.py`](../../../src/circuitsmith/renderer.py).

Test files covering this subsystem:

```pytest
tests/test_renderer.py
tests/test_renderer_erc.py
tests/test_renderer_staleness.py
tests/test_full_pedal_fixture.py
tests/test_meta_yml_provenance.py
tests/test_meta_yml_escalations.py
tests/render/test_multi_page_driver.py
tests/render/test_cross_page_labels.py
```

## Inputs and outputs

- **Input** — `render(circuit_path, layout_path=None, out_svg, …,
  use_ai_placer=False, ai_client=None)`; `_main(argv)` is the CLI.
- **Output** — the SVG at `out_svg`, sidecars `<stem>.layout.yml` /
  `<stem>.meta.yml`, and (when ≥ 2 pages are declared)
  `<stem>-p<N>.svg` per page. A `RenderResult` carries `.rubric`,
  `.layout_path`, `.meta_path`. Failures raise `RenderError(stage,
  summary, findings)`.

## Unit tests

`tests/test_renderer.py` (TASK-012): a clean ESP32 circuit renders
rubric-green with a `data-ref="<ref>"` attribute per component (the
structural-equality hook); the `.layout.yml` sidecar is written
alongside (`schema: layout/v1`, MCU at `mcu-center`); the `.meta.yml`
records `rubric:` scores, advisory metrics (`overlaps`,
`wire_crossings`, `min_label_distance`, `density`) and `provenance:`
(`ai_invoked: false`); the renderer round-trips its own `.layout.yml` on
a second run; an unknown component type halts with `RenderError(stage in
{circuit-schema, kernel})`; the CLI is path-agnostic and returns
non-zero on schema failure; and the module carries no host-project
imports (ADR-0012).

Multi-page rendering: `tests/render/test_multi_page_driver.py`
(TASK-125) covers the one-SVG-per-page driver, and
`tests/render/test_cross_page_labels.py` (TASK-126) the `▶`/`◀`
cut-wire boundary glyphs — these are the page-break fixtures the chapter
template asks for.

Meta-sidecar provenance: `tests/test_meta_yml_provenance.py` (TASK-020,
`ai_invoked` + `ai_invocations`) and `tests/test_meta_yml_escalations.py`
(TASK-057, kernel fail-loud events serialised to
`provenance.escalations`).

## Integration tests

- `tests/test_renderer_erc.py` (TASK-023) confirms ERC runs *inside* the
  render pipeline, pre-layout — an ERROR-level finding aborts before the
  router (the cross-subsystem contract with [`erc-engine.md`](erc-engine.md)).
- `tests/test_full_pedal_fixture.py` (TASK-014) is the end-to-end
  fixture: the full pedal circuit renders green through every stage.

## Golden / snapshot tests

`tests/test_renderer_staleness.py` (TASK-015) is the golden gate: it
re-renders each shipped target and diffs against the committed
artefacts. **The SVG comparison is byte-exact** — there is no tolerance
for font-metric or geometry drift. The policy follows from that:

- **SVG** — byte-exact. A legitimate change (a Schemdraw/matplotlib
  upgrade, a deliberate topology edit) requires re-baselining the
  committed SVG, reviewed as part of the same commit.
- **`.meta.yml`** — diffed with the `sources:` block normalised away
  (it records invocation paths that drift per-runner), per
  `check_gallery_regression.py:_normalise_meta`.
- **`.erc-report.md`** — diffed with the auto-stamped header date
  normalised (see [`erc-engine.md`](erc-engine.md) and the
  `check_erc_reports.py` / `check_gallery_regression.py` gates).

The same byte-exact policy backs the tutorial/gallery regression gate
([`ci-gates.md`](ci-gates.md)).

## Property / fuzz tests

**None.** Rendering is asserted on fixed fixtures and the shipped
circuits; there is no generated-circuit rendering fuzz. Rationale: the
byte-exact golden gate on real circuits is the high-value guard.

## Performance budget

**No budget.** Rendering the shipped circuits is a small part of the
~9 s suite; matplotlib import dominates and is a fixed cost. No number
is pinned.

## Known uncovered cases

- **SVG visual semantics.** The byte-exact diff catches *any* change but
  understands *none* — it cannot tell an intended restyle from a
  regression. Rationale: a semantic SVG differ is high-effort and
  low-return at this scale; human review of the re-baseline diff is the
  control. Documented so re-baseliners know to look.
- **matplotlib/Schemdraw upgrade drift.** A dependency bump can shift
  every SVG byte, forcing a full re-baseline. Rationale: pinned deps
  keep this rare; no automated cross-version render matrix exists —
  a TASK-090 candidate if upgrades become frequent.
- **Cross-platform SVG determinism.** The staleness gate is scoped to
  Ubuntu in CI because matplotlib float geometry is OS-dependent
  (`ci.yml`). Windows renders are not golden-checked — intentional, to
  avoid OS-driven false positives.

## Cadence

| Test file | PR | Nightly | Release |
|---|:--:|:--:|:--:|
| `tests/test_renderer.py` | ✓ | | |
| `tests/test_renderer_erc.py` | ✓ | | |
| `tests/test_renderer_staleness.py` | ✓ | | |
| `tests/test_full_pedal_fixture.py` | ✓ | | |
| `tests/test_meta_yml_provenance.py` | ✓ | | |
| `tests/test_meta_yml_escalations.py` | ✓ | | |
| `tests/render/test_multi_page_driver.py` | ✓ | | |
| `tests/render/test_cross_page_labels.py` | ✓ | | |

All run at PR-time (Ubuntu golden-checks the SVGs; Windows runs the
non-golden subset). A cross-version matplotlib render matrix, if added,
would be a nightly tier.
