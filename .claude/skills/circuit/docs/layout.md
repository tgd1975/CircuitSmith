# Layout engine — user guide

> Audience: contributors authoring `.circuit.yml` files and reading the
> rendered SVG / `meta.yml` output. For design rationale and rejected
> alternatives, see the companion concept doc at
> [`docs/developers/ideas/archived/idea-001.layout-engine-concept.md`](../../../../docs/developers/ideas/archived/idea-001.layout-engine-concept.md)
> and the canonical-decision ADRs ([`ADR-0001`](../../../../docs/developers/adr/0001-slots-not-coordinates.md),
> [`ADR-0007`](../../../../docs/developers/adr/0007-skill-directory-is-the-library.md)).

The layout engine turns a validated `.circuit.yml` into a placed and
routed SVG plus a `meta.yml` sidecar. v0.1 is **kernel-only**: a
deterministic placer driven by a small canonical-slot table, a
Manhattan router, and a structural rubric. No AI calls, no
randomness, no backtracking.

## Pipeline

```text
.circuit.yml
    │
    ▼  schema/validator.py     ← S1–S5 checks (TASK-005)
NetGraph                       ← one topology projection (ADR-0003)
    │
    ▼  layout_engine/kernel    ← canonical-slot lookup, §5.3 dispatch
LayoutResult                   ← placements (deterministic)
    │
    ▼  layout_engine/router    ← Manhattan, deterministic
RouterResult                   ← orthogonal segments
    │
    ▼  layout_engine/rubric    ← blocking + advisory checks
RubricResult                   ← gates SVG emission
    │
    ▼  renderer (TASK-012)
out.svg + out.layout.yml + out.meta.yml
```

## Slot vocabulary (v1)

Every component is placed in exactly one **slot** — a `{region, index}`
pair. The slot vocabulary is bounded by ADR-0001 and codified in
[`layout.schema.json`](../schema/layout.schema.json).

| Region | Where | Index |
|---|---|---|
| `mcu-center` | Drawing origin | none — at most one occupant |
| `left-column` | Left of MCU | `row: int` |
| `right-column` | Right of MCU | `row: int` |
| `top-row` | Above MCU | `col: int` |
| `bottom-row` | Below MCU | `col: int` |
| `path-of-<REF.PIN>` | Extends outward from the named pin | `step: int` |
| `bus-<name>` | Between declared backbone endpoints | `position: 0.0–1.0` (1/16 resolution) |
| `pin-symbol-<pin>` | At the pin anchor itself | none |
| `free` | Raw grid coordinate (escape hatch) | `gx: int, gy: int` |

`attached-to` lets a second component share a slot with an anchor
component (e.g. a current-limit resistor stacked with its LED). The
attached placement carries `region` (inherited from the anchor) and
`attached-to`, and **must omit** `row`/`col`/`position`/`step` —
the schema rejects the redundancy with `attach-index-redundant` per
[idea-001.layout-engine-concept.md §4.2](../../../../docs/developers/ideas/archived/idea-001.layout-engine-concept.md).

## Canonical-slot table (v0.1 dispatch)

The kernel dispatches every component to a canonical slot using a small
table. The full §5.3 spec lives in the concept doc; the v0.1 implementation
covers the rows below.

| ID | Component shape | Canonical placement |
|----|-----------------|---------------------|
| —  | MCU / primary IC (`type: mcu/*`) | `mcu-center` |
| 1  | LED (anode → MCU pin P, cathode → GND) | `side-column(P)`, `row: next-free` |
| 2  | Resistor in series with an LED | inherited region, `attached-to: <LED>` |
| 3  | Resistor on a power → MCU path (pull-up, ADR-0017 widened to IC `SIGNAL_INPUT` anchors) | `path-of-<anchor.ref>.<pin>`, `step: 0` |
| 4  | Button (one terminal → MCU pin, other → GND) | `side-column(P)`, `row: next-free` |
| 5  | Decoupling capacitor (between VCC and GND) | `bus-<power-net>`, `position: next-free` |
| 6  | I²C sensor | `left-column` or `right-column` by dominant pin side |
| 7  | Multi-pin header / jack | `top-row` or `bottom-row` |
| 11 | RC low-pass (R in-path, C-to-GND from junction) | `rc-low-pass-<R>-<C>`, rows 0/1 (synthetic region) |
| 12 | RC high-pass (C in series, R-to-GND from junction) | `rc-high-pass-<C>-<R>`, rows 0/1 (synthetic region) |
| 13 | C+C decoupling pair (both caps between the same rail and GND) | `cc-decoupling-<C1>-<C2>`, rows 0/1 (synthetic region) |
| 14 | R+R voltage divider (rail → R1 → tap → R2 → GND; tap-net hinted via `/^(V?REF\|SENSE\|ADC\|DIV\|TAP)/i` or `role: divider`) | `divider-<tap_net>`, rows 0/1 (synthetic region) |
| 15 | BJT canonical slot (ADR-0015) | `right-column`, `row: next-free` |
| 16 | Resistor on the BJT base path (ADR-0015) | inherited region, `attached-to: <BJT>` |
| 17 | Generic IC (`ic_timer` / `ic_opamp` — 555, op-amp) | `left-column` or `right-column` by dominant pin side |
| 18 | BJT collector load (rail → R → Q.C, ADR-0016) | `bjt-load-<BJT>`, row 0 (synthetic region) |
| 19 | BJT emitter degeneration (Q.E → R → GND, ADR-0016) | `bjt-degen-<BJT>`, row 0 (synthetic region) |

`side-column(P)` resolves to `left-column` when pin P has
`side: left` and `right-column` when it has `side: right`. **Synthetic
regions** (rows 11–14, 18–19) are uncoordinatised in the v0.1
router — the kernel records the placement and the BOM / ERC see
the components, but the SVG omits the symbol. Coordinatising
synthetic regions for the renderer is a planned follow-up.

A component that matches no row raises a `no-canonical-rule`
escalation (see below) and the renderer aborts. The fix is either to
restructure the topology so an existing row matches, hand-author a
`free` slot in `layout.yml`, or — once Phase 2b lands — let the AI
placer attempt a placement.

## Incremental stability

The kernel is incremental by default. Given an edited `.circuit.yml`:

```text
kept     = components in both the previous layout and the current circuit
removed  = components in the previous layout but not the current circuit
new      = components in the current circuit but not the previous layout
```

`kept` placements stay frozen **as long as their topology-fingerprint
matches**; otherwise the placement auto-invalidates and re-queues into
`new`. `new` runs through canonical-slot dispatch. `removed` is dropped
from `layout.yml`.

The fingerprint is a SHA-1 prefix of `(rule ID, canonical shape form)`.
Renaming a pin (`D25 → D26`) invalidates; re-indenting the YAML does not.
See `idea-001.layout-engine-concept.md §8.4` for the full canonicalisation
contract.

**The single-line-diff invariant**: adding one component to an existing
layout produces **exactly one new line** in `layout.yml` and zero
changes to other lines. The kernel's `next-free` row/col bookkeeping is
what makes this true; rung 2 of the overflow ladder (neighbour-nudge)
breaks it deliberately by shifting an entire region.

## Sub-block instances (inline-box mode)

When a `.circuit.yml` declares `sub-blocks:` / `instances:` (see
[`circuit-yaml.md`](circuit-yaml.md#sub-blocks-and-instances)),
the renderer flattens every instance before the kernel runs.
The placer sees ordinary flat refdes (`R_PWR`, `D_PWR`, …); the
canonical-slot table doesn't know — or care — that the components
came from a sub-block.

The renderer preserves the instance grouping in two places:

- The placements in `layout.yml` group naturally because every
  member of an instance shares the same canonical rule. Three
  instances of an `R+LED` sub-block produce three adjacent rows
  in `right-column`, each with the resistor `attached-to:` its
  LED.
- The `meta.yml` sidecar carries an `instances:` block that
  names each instance, its sub-block, and its flat refdes
  constituents:

  ```yaml
  instances:
    PWR:
      sub-block: led_indicator
      label: "PWR: led_indicator"
      constituents: [D_PWR, R_PWR]
  ```

  Downstream tools (BOM grouping, the planned inline-box SVG
  annotator) read this map instead of re-running the flattener.

v0.1 ships **inline-box mode** — the constituents of an instance
appear in the SVG exactly where the canonical-slot rules would
place them, with no enclosing rectangle, no explicit hierarchy
glyph. The grouping survives via the `meta.yml.instances` map
above and via the shared `attached-to:` chains in `layout.yml`.

**Hierarchical-port mode** — a Schemdraw bounding-box rectangle
around each instance's constituents plus labelled hierarchical
ports on the box's edges — is the planned alternative for when
sub-block contents grow past two or three components. The
hierarchical-port renderer is gated on EPIC-014's multi-page
work; until that phase lands, the renderer always falls through
to inline-box mode.

## Pages partition (multi-page layouts)

EPIC-014 / TASK-124 — opt-in. A `.layout.yml` can declare a list
of named pages and tag each placement with the page it belongs
to. The kernel does not derive pages from circuit topology;
pages are a *rendering* concern. Slot assignment happens within
a page's region/slot vocabulary (per
[ADR-0001](../../../docs/developers/adr/0001-slots-not-coordinates.md)),
so a `right-column` slot on `p1` is independent of a
`right-column` slot on `p2`.

```yaml
schema: layout/v1
pages:
  - { name: p1, title: Power and clock }
  - { name: p2, title: Signal chain }
placements:
  U1:  { region: mcu-center, page: p1, topology-fingerprint: sha1:... }
  D1:  { region: left-column, row: 0, label: left, page: p2, topology-fingerprint: sha1:... }
```

Validator invariants (`layout-pages-duplicate-name`,
`layout-page-undeclared`):

- `pages[*].name` is unique within the document.
- Every `placements.<ref>.page` must name a declared page.
- A `.layout.yml` with **no** `pages:` block continues to render
  as today (one SVG, no `-p1` suffix). Pages are strictly
  additive; existing v0.1 fixtures are byte-identical.

Attached-to components inherit the anchor's page (so a current-
limit resistor never separates from its LED, a base-drive
resistor never separates from its BJT). The user can override
by setting `page:` on the attached entry explicitly; the
previous-layout parse honours that.

The renderer driver (TASK-125), cross-page net labels
(TASK-126) and cross-page ERC rules (TASK-127) are the
consumers of this schema field. TASK-124 lands the schema and
the kernel propagation only — without TASK-125, a `pages:`
block is parsed, validated, and round-tripped, but the renderer
ignores it (defensible intermediate state).

## Manhattan router

The router takes the kernel's placements + the `NetGraph` and emits one
orthogonal wire path per consecutive pin pair on each net. v0.1 uses
L-shaped (H→V) routing for every pair; Z-shape break enumeration is a
post-v0.1 enhancement.

- Wires are pure right-angle (no diagonals).
- Crossings are **reported, not avoided** — see the rubric below.
- Wires that pass through a non-endpoint component's bbox are
  also reported; routing-around is a follow-up.
- Two runs against the same inputs produce byte-identical geometry.

## Rubric

The rubric runs after the router and gates SVG emission.

**Blocking checks (failure aborts the run):**

| Check | What it measures | Default threshold |
|---|---|---|
| `overlaps` | Distinct component pairs whose bboxes share a grid cell | `0` |
| `labels_fit` | Every placement's label text fits inside its per-region budget | budget = 8 chars |
| `wire_crossings` | Pairs of segments from different wires that cross at an interior point | `0` |
| `min_label_distance` | Nearest-neighbour Manhattan distance on labeled placements | `≥ 1` grid unit (TASK-019) |
| `density` | Occupied-cells / bbox-area ratio | `≤ 0.5` (TASK-019) |

The bottom two checks were advisory-only in v0.1; under TASK-019 they
are promoted to blocking with thresholds derived from the Phase 2a
green corpus (75th-percentile floor per `idea-001.layout-engine-concept.md §10`
— two shipped circuits both report `min_label_distance = 1` and
`density = 0.1453`). Pass `min_label_distance_threshold=None` /
`density_threshold=None` to `evaluate()` for pre-v1 fixture
re-baselining.

**Advisory checks (recorded, never blocking):**

| Check | What it measures |
|---|---|
| `intra_component_intersections` | Wires passing through a non-endpoint component cell |

A failure surfaces in `meta.yml.provenance.escalations` (see below) so
the trigger gate observer ([TASK-058](../../../../docs/developers/tasks/closed/task-058-implement-check-phase2b-trigger.md))
sees it.

## `meta.yml` sidecar

Written by the renderer alongside every SVG. Schema:
[`meta.schema.json`](../schema/meta.schema.json).

```yaml
schema: circuit-meta/v1
sources:
  circuit: path/to/esp32.circuit.yml
  layout:  path/to/esp32.layout.yml
layout:
  state: complete         # or `incomplete` on rubric/kernel failure
  placed: 16
  total:  16
rubric:
  overlaps:                       0
  labels_fit:                     true
  wire_crossings:                 0
  min_label_distance:             2
  density:                        0.83
  intra_component_intersections:  0
provenance:
  tool:        circuit-renderer
  skill:       circuit-skill@0.4.0
  ai_invoked:  false
  iterations:  0
  escalations: []
```

The `provenance.escalations` array is **always written** — `[]` on a
clean run, never absent. Each entry is the record of a fail-loud event:

| Category | Meaning | §5.3-addressable? |
|---|---|---|
| `no-canonical-rule` | Kernel could not find a §5.3 entry for `(category, shape)` | **yes** |
| `no-profile` | Component `type:` does not resolve to any profile | no — schema problem |
| `slot-overflow` | A region's capacity was exceeded | no — topology problem |
| `bus-saturated` | A `bus-<name>` region exhausted its 1/16 resolution | no — topology problem |
| `router-stall` | Manhattan router could not route a net | no — topology problem |
| `kernel-bug` | Internal invariant violated | n/a — bug report |
| `rubric-fail-overlaps` | Rubric blocked emission on `overlaps` | no — rendering problem |
| `rubric-fail-labels-fit` | Rubric blocked emission on `labels_fit` | no |
| `rubric-fail-wire-crossings` | Rubric blocked emission on `wire_crossings` | no |

Only `no-canonical-rule` is "addressable" by adding a row to the §5.3
table. Every other category is a topology or rendering problem the AI
placer cannot resolve, so the Phase 2b trigger counts only those.

## Overflow response ladder

When a new placement exceeds a region's capacity, the kernel tries the
rungs of the [§8.3 overflow ladder](../../../../docs/developers/ideas/archived/idea-001.layout-engine-concept.md)
in order:

1. **Local grow.** Extend the region's capacity by one cell. A
   `capacity-overrides:` block is written to `layout.yml`. No other
   placement moves — single-line diff guarantee holds.
2. **Neighbour nudge.** Not yet implemented (post-v0.1). Shifts an
   adjacent region's anchor by one grid unit. SVG bounding box diffs
   but `layout.yml` stays local.
3. **Explicit reflow.** Run `/circuit layout --reflow` (post-v0.1) to
   discard `layout.yml` and re-place every component from scratch.
   Never automatic.

## AI placer (Phase 2b)

The AI placer fires **only when the kernel raises an
`EscalationError`** — i.e. a component has no matching §5.3 row, or
an overflow / collision can't be resolved deterministically. On clean
inputs the AI placer never runs. The design rationale lives in
[`idea-001.layout-engine-concept.md §7`](../../../../docs/developers/ideas/archived/idea-001.layout-engine-concept.md)
and [ADR-0008](../../../../docs/developers/adr/0008-phase-2b-trigger-on-evidence.md).

### Invocation

```bash
# Kernel-only (CI default, ADR-0002 hermetic path):
python -m circuit.renderer --circuit path/to/esp32.circuit.yml --out build/esp32.svg

# Opt in to the Phase 2b AI placer (local authoring time only):
python -m circuit.renderer --circuit path/to/esp32.circuit.yml --out build/esp32.svg --ai
```

The Python API mirrors the CLI: `render(..., use_ai_placer=True,
ai_client=…)`. Tests inject a mock `LLMClient`; production uses
[`AnthropicClient`](../layout_engine/ai_placer.py) which lazy-imports
the SDK and reads `ANTHROPIC_API_KEY` from the environment.

### Input contract

The placer receives:

- The full circuit topology.
- The kernel's frozen placements (whatever it could place
  deterministically). These are off-limits — proposing a slot for
  any frozen ref returns `ai-frozen-violation`.
- The ambiguity queue: one entry per unplaceable ref with the
  kernel-side reason code (`no-canonical-rule`, `slot-overflow`, …)
  and a human-readable detail.
- Region capacity map (rows/cols available).
- The slot vocabulary.

### Output contract

Strict JSON:

```json
{
  "placements": {
    "R_PWR": { "region": "left-column", "row": 3 },
    "Q1":    { "region": "free", "gx": 7, "gy": -2 }
  }
}
```

Grid-discrete only. Raw `gx`/`gy` coordinates are valid solely under
`region: free`. The renderer validates each entry against the slot
vocabulary; unknown regions, frozen refs, or malformed JSON all
short-circuit with their own reason code (`ai-unknown-region`,
`ai-frozen-violation`, `ai-output-invalid`).

### Convergence behaviour

- **Iteration cap:** 5 turns (provisional per §7.3; calibrated
  against the v0.1 failure corpus once the trigger gate accumulates
  evidence). Each turn:
  1. The renderer prompts the LLM with topology + frozen layout +
     ambiguity queue + (on retries) the previous turn's rubric
     feedback.
  2. The LLM responds with slot proposals.
  3. The renderer merges proposals into a trial layout, runs the
     router + rubric, and feeds the verdict back into the loop.
  4. Convergence: every blocking rubric check passes → emit SVG +
     `meta.yml` with `state: complete` and `ai_invoked: true`.
- **Fail-loud paths** (all surface as `RenderError` at stage
  `ai-placer`, `state: incomplete` in `meta.yml`):
  - `ai-cap-exceeded` — hit iteration 6 without converging.
  - `ai-token-cap-exceeded` — cumulative cost overshot the run cap.
  - `ai-output-invalid` — LLM returned unparseable JSON.
  - `ai-frozen-violation` — proposed to move a kernel-placed ref.
  - `ai-unknown-region` — region not in the vocabulary.
  - `ai-missing-component` — didn't address every ambiguity.

Per §7.3, **no silent fallback**: on non-convergence the operator
hand-authors a `free`-slot entry, raises a region's capacity, or
restructures the topology.

### Cost notes

- **Per-run iteration cap:** 5 turns. The cap's job is to bound cost
  and guarantee termination, not to hit a measured sweet spot.
- **Per-run token cap:** `DEFAULT_TOKEN_CAP = 50_000` (cumulative
  input + output across all iterations). Acts as a safety net
  against a runaway prompt or output; exceeding it short-circuits
  with `ai-token-cap-exceeded` even if iterations remain.
- **Typical converged run:** one or two LLM calls, ~1–3k input
  tokens + ~200–500 output tokens per call. Cost-per-run is
  bounded; the cumulative cost across a release-prep period is
  what the §17.2 drift guard exposes via
  `meta.yml.provenance.ai_invocations[].{input_tokens, output_tokens}`.
- **CI runs never invoke the placer** — ADR-0002 forbids it. The
  renderer's `use_ai_placer` default is `False`; the only way the
  placer runs in CI is by explicitly passing `--ai` to the CLI,
  which isn't wired into any workflow step.

### `--no-ai` (opt-out)

`--no-ai` is the explicit kernel-only flag. It's already the default
for both the CLI and the Python API; the flag exists so contributor
scripts and CI jobs can declare their intent explicitly rather than
relying on the default. Under `--no-ai`, a kernel escalation
surfaces as a `RenderError` at stage `kernel` (TASK-018) — the same
behaviour the v0.1 renderer has always had.

### `meta.yml.provenance` fields

Every renderer run writes:

| Field | When | Meaning |
|---|---|---|
| `ai_invoked: true\|false` | Always | Did the placer actually run this turn? |
| `iterations: <int>` | Always | Cumulative AI iterations across all dispatches (0 on kernel-only) |
| `ai_invocations: [<entry>]` | Only when the placer ran | One entry per dispatch — `reason`, `iterations`, `input_tokens`, `output_tokens`, `components` |
| `escalations: [<entry>]` | Always | The §17.2 drift-guard corpus — empty list on clean runs |

`ai_invocations[].reason` and `escalations[].category` are documented
in [`meta.schema.json`](../schema/meta.schema.json) as enums; the
list is the contract the Phase 2b trigger gate (TASK-058) reads.

## Phase 2b flags (cheat sheet)

The following flags ship as part of Phase 2b alongside the AI placer:

- `--no-ai` — explicit kernel-only path. Default for CI per ADR-0002.
- `--ai` — opt into the AI placer. Requires `ANTHROPIC_API_KEY`;
  reaches the network only when the kernel kicks up an escalation.
- `--reflow` — discard `layout.yml` and re-place every component
  from scratch. Documented for completeness; not yet implemented
  (post-v1 enhancement).

## Known limitations (v0.1)

- Pin coordinates collapse to the component origin; per-pin offsets
  arrive with the rich-glyph follow-up to the renderer.
- The router does not avoid routing through non-endpoint component
  cells; it reports `intra_component_intersections` instead.
- Z-shape routing break enumeration is not yet implemented; L-shape
  H→V is the only candidate orientation.
- Schemdraw glyphs are not yet selected per category; v0.1 SVG draws
  a labelled rectangle per component and a polyline per wire. The
  structural-equality test in CI (idea-001 §12 step 6) uses
  `data-ref` / `data-net` attributes, which are stable across the
  pending glyph upgrade.

See also:

- [`circuit-yaml.md`](circuit-yaml.md) — the `.circuit.yml` format
  reference the layout engine reads.
- [`meta.schema.json`](../schema/meta.schema.json) — machine-readable
  schema for the `meta.yml` sidecar.
- [`layout.schema.json`](../schema/layout.schema.json) — machine-readable
  schema for `layout.yml`.
