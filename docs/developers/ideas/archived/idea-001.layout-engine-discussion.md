# Layout Engine — Discussion

> Sub-note of [IDEA-001](idea-001-circuit-skill.md). Predecessor references
> (e.g. `scripts/generate-schematic.py`, IDEA-011/018/019/022) resolve via the
> [Provenance anchor map](idea-001-circuit-skill.md#provenance).
>
> **This document is the exploration log, not the authoritative design.**
> The consolidated, consistent concept — which resolves the contradictions
> flagged in the "Design review: known gaps" section below — lives in
> [idea-001.layout-engine-concept.md](idea-001.layout-engine-concept.md).
> Read that first for the "what"; read this file for the "why" and the
> alternatives that were considered and rejected.

Schemdraw has no auto-layout. The renderer derives placement from the three connection
forms — each form maps to a distinct drawing strategy.

## Strategy per connection form

**`pins` nets — power/ground symbols:**
Each endpoint gets a ground symbol (`elm.Ground`) or a labelled power symbol
(`elm.Label`) placed directly at the pin anchor. No routing wire is drawn. The
renderer iterates the pin list; order does not matter.

**`path` nets — inline chain:**
Elements are placed in declared order. Each element starts at the endpoint of the
previous one, extending in the direction inherited from the MCU pin's `side` field
(left pins extend left, right pins extend right). The rendering loop is:

```
for each consecutive pair (A, B) in path:
    if B is a net name (GND, VCC): place terminal symbol at current position
    else: place B's Schemdraw element at A's anchor, extending in current direction
```

This is exactly what the current `generate-schematic.py` does for LED and button
chains — now generalised to arbitrary path lengths.

Direction is inherited from the first MCU pin in the path and does not change along
the path. If a path must change direction (e.g. a filter that turns a corner), a
`direction` hint can be added to any pin step using the long-form entry:

```yaml
- net: AUDIO_IN
  path:
    - U1.IO32
    - C1.1
    - { pin: C1.2, direction: right }   # override direction from this step onward
    - R2.1
    - R2.2
    - J1.TIP
```

**`bus` nets — backbone + stubs:**

1. The renderer places the backbone as a `elm.Line` between the two `backbone`
   anchor points, using `.tox()` or `.toy()` to span the distance.
2. A `elm.Dot` junction is placed at each tap point along the backbone.
3. A perpendicular stub (`elm.Line`) drops from each dot to the tap component's pin.
4. Tap spacing defaults to equal intervals along the backbone; overridden per tap
   with `layout.position` (0.0–1.0):

```yaml
- net: V33
  bus: true
  backbone: [U1.3V3, OLED.VCC]
  taps:
    - ref: BME280.VCC
    - ref: C2.1
      layout: { position: 0.3 }   # place 30% along the backbone from U1.3V3
```

## MCU placement and pin ordering

The MCU IC block is always placed first, at the drawing origin. Pin ordering on the
IC block follows the profile declaration order within each side — this mirrors the
physical board layout, making the diagram spatially intuitive.

Direction lookup for path rendering:

| Profile `side` | Schemdraw `theta` |
|---|---|
| `left` | 180° |
| `right` | 0° |
| `top` | 90° |
| `bottom` | 270° |

Unused pins get `elm.NoConnect` at their anchor. Power and GND pins get symbols
directly — no chain.

## Position override

When inferred placement produces overlapping elements (most likely with bus taps or
long path chains), any component accepts an absolute position override:

```yaml
components:
  C1:
    type: passives/capacitor
    value: 100nF
    layout:
      x: 4.5
      y: 2.0
```

The renderer places this component at `(x, y)` and connects it to its nets using
`.at()` anchored to the declared position. Use sparingly — if more than two overrides
are needed, the connection model likely needs restructuring first.

## What this renderer cannot do

- **Diagonal routing** — all paths are orthogonal. Schemdraw supports diagonal elements
  via `theta`, but the renderer has no heuristic for when to use them.
- **Crossing avoidance** — the renderer does not detect or route around wire crossings.
  If two paths cross, the author must restructure or use position overrides to separate them.
- **Multi-MCU placement** — if a circuit has two IC blocks of similar weight, the renderer
  places the first one declared at the origin and treats the second as a positioned component.
  An explicit `layout.x/y` on the second IC is required.
- **Custom Schemdraw elements** — elements not in the component library (custom subclasses,
  special symbols) require a hand-authored Python script. The YAML format has no escape
  hatch for this.

## Lessons from TASK-239 — readable layout is hard even for trivial changes

TASK-239 added a *single* new element per button pin (an external 10 kΩ pull-up to 3V3
on top of the existing switch-to-ground) and even that modest change required several
iterations of trial-and-error layout work to avoid overlaps:

- **First attempt** (resistor column directly above each pin) collided with the pin row
  above because `pinspacing` (1.5 units) was smaller than the default `Resistor` length
  (~2 units).
- **Second attempt** (horizontal resistor to the side, switch dropped vertically to
  ground) produced a clean pull-up column but ran the switch's ground symbol into the
  adjacent pin row below.
- **Third attempt** (short horizontal lead to a junction, vertical resistor up with
  `length(1.0)`, horizontal switch to ground, plus `pinspacing` bumped to 2.0) produced
  the final "okay but not good" result: readable, no overlaps, labels legible but
  aesthetically cramped.

The layout that eventually shipped is the third attempt above — acceptable, but
visibly tight. It would not pass review as a reference schematic in a commercial
datasheet.

**Implications for this idea:**

1. **Do not underestimate the layout engine work.** The "three-form strategy" described
   above (pins → power symbols, path → inline chain, bus → backbone + stubs) covers the
   *electrical* topology cleanly, but the concrete geometry (pin spacing, element
   lengths, label offsets) still has to be tuned by hand whenever a new element type is
   introduced. A first-principles layout engine that "just works" is a larger undertaking
   than the rest of the skill combined.
2. **Position overrides are not an edge-case feature — they are load-bearing.** The
   `layout.x`/`layout.y` and `layout.position` escape hatches will likely be used on
   most non-trivial circuits, not "sparingly" as the current text suggests. Budget for
   authoring effort on every new circuit.
3. **"Readable" is the right bar, not "pretty".** TASK-239's output is clear enough for
   a hand-wiring builder to follow and that is sufficient. The skill should aim for the
   same bar — pretty schematics are a KiCad concern (IDEA-011), not Schemdraw's.
4. **Consider adopting per-pin-type spacing as a first-class feature.** TASK-239 worked
   around cramped button rows by globally bumping `pinspacing` from 1.5 to 2.0, which
   wastes vertical space on simple rows (NC pins, plain power rails). A future version
   of the renderer should allow declaring extra spacing *only* for pin rows that carry
   multi-element circuits (button + pull-up, LED + resistor + diode, etc.).
5. **Visual regression is mandatory before any layout refactor.** The Phase 2
   acceptance criterion already specifies structural XML comparison rather than pixel
   diff — keep that, but also render the SVG to PNG and eyeball it as part of every
   layout-engine change. Structural equivalence does not catch overlaps.

---

## Library survey and alternative approaches

The TASK-239 pain opened the question of whether a different library could do the
layout work for us. Survey below; filter is **"good enough for a maker circuit"**
plus **"installable on a GitHub Actions runner without heavy system deps"**, since
the staleness guard runs on every PR.

### Candidate libraries

| Library | Auto-layout | CI install cost | Aesthetic | Verdict |
|---|---|---|---|---|
| Schemdraw (current) | none | trivial (`pip`) | classic schematic | keep as rendering substrate; needs help on placement |
| SKiDL (netlist only) | n/a | trivial (`pip`) | n/a | **adopt for `.net` export** — clean fit, independent of renderer |
| SKiDL (schematic gen) | basic | heavy — needs KiCad on runner | KiCad-style | fragile in CI; reject |
| lcapy | heuristic auto-placement | heavy — needs TeX Live + CircuiTikZ + pdf2svg | classic schematic | best auto-layout aesthetic, but LaTeX in CI is brittle; reject |
| netlistsvg (Node) | excellent (ELK) | low — Node preinstalled on GHA | digital block-diagram | strong fallback if we abandon "roll our own" |
| WireViz | Graphviz | low — `pip` + graphviz | hookup/harness diagram | wildcard; better fit for builder docs than schematics |

Primary reject: **lcapy** (LaTeX on every PR is too heavy and too brittle).
Primary alternative to rolling our own: **netlistsvg via subprocess** (aesthetic
cost is real but install is trivial).
Orthogonal win: **SKiDL for netlist export** regardless of the rendering choice.

---

## Roll-our-own with AI-in-the-loop (exploratory)

The alternative to switching libraries: keep Schemdraw as the rendering substrate,
add a thin deterministic placement kernel, and use AI at **authoring time** to fill
in the geometric judgment that a first-principles engine would need.

### The split that makes this CI-safe

```
authoring (local, runs once per schematic change)
  YAML topology
    → AI proposes positions
    → renderer produces SVG + layout report
    → AI reviews report (and optionally PNG)
    → AI patches positions
    → loop until "acceptable" or iteration cap
  commit: YAML + frozen layout.yml (or inline layout: blocks)

CI (every PR, deterministic)
  committed YAML + committed positions → SVG
  staleness guard diffs committed SVG against re-render
  no AI, no network, no API key
```

AI performs the *judgment*; its conclusions are serialized as data. The renderer
stays pure. This extends the existing "commit the generated SVG" pattern — now we
commit the *positions* too.

### Design decisions

1. **AI outputs grid coordinates, not free floats.** Constrain to integer multiples
   of `pinspacing`. Keeps diffs readable and prevents the AI from flailing in
   continuous space.
2. **Symbolic review before visual review.** Renderer emits a JSON layout report
   (bbox per component, overlap pairs, wire crossings, label clipping,
   signal-flow direction). AI reasons over the JSON. Vision review on the rendered
   PNG is a second-pass escalation only.
3. **Split into deterministic kernel + AI placer.**
   - *Kernel* (always runs, no AI): grid snap, bbox + overlap detection, Manhattan
     wire router given placements, JSON layout report.
   - *Placer* (authoring-time AI): reads topology + current placements + report,
     outputs next placement proposal.
4. **Stop on a rubric, not on vibes.** Zero bbox overlaps; zero (or AI-waived) wire
   crossings; labels fit their rectangles; signal flows left→right, GND bottom,
   VCC top.
5. **Placement search space is a slot vocabulary, not a free grid.** Each
   component category offers a small menu — a 2-lead passive picks from
   {horizontal, vertical, L-shaped}; an IC picks from {left/right/above/below-of-MCU
   with offset}; a bus backbone picks horizontal/vertical + fractional tap positions.
   AI picks a slot, not raw coordinates.

### Honest risks

- AI geometric judgment is mediocre even with a slot vocabulary. The iteration
  count is doing real work; expect 3–5 turns per new circuit.
- Authoring cost is not free: each topology change triggers a local loop with
  API calls. The result is frozen and committed, but the authoring step is slow.
- Contributors without API keys can re-render and can hand-edit positions, but
  cannot invoke the placer. Acceptable for a maintainer-driven project.
- The kernel is where the real engineering lives. If the overlap detector or
  wire router is weak, AI cannot save it. Budget accordingly.

### Minimum viable slice

1. **Kernel v0** — bbox + overlap detection + Manhattan router. Consumes YAML
   with explicit `layout.x/y` on every component; emits SVG + JSON report.
   Mostly a refactor of the current generator.
2. **Slot vocabulary v0** — 5–10 canonical placements per component category,
   enough to describe the existing ESP32 circuit without raw coordinates.
3. **AI placer v0** — single prompt, single turn. Reads YAML + empty placement,
   emits placements using the slot vocabulary.
4. **Iteration loop v0** — feed the layout report back on overlap/crossing, cap
   at 5 turns.

Success criterion for the spike: on the current ESP32 circuit, the loop converges
to a layout at least as readable as TASK-239's third-attempt output. If yes,
Phase 2 of IDEA-001 gets rewritten around this split. If no, fall back to the
`netlistsvg` subprocess plan and accept the digital-block-diagram aesthetic.

---

## Layout stability under incremental change

**Goal.** Adding a 6th LED to a circuit with 5 existing LEDs must not reshuffle
the other 5. Git diffs stay small, reviewers re-read only the new part, and
visual regressions remain trivially inspectable. Stability is load-bearing for
the whole docs-as-code pipeline — a schematic that shifts every commit is a
schematic nobody wants to review.

Three mechanisms combine to deliver this.

### 1. `layout.yml` is committed and authoritative

The placer is **incremental by default**, not regenerative:

```
pre-run:
  diff YAML vs committed layout.yml
    kept components    → freeze their slot (do not reconsider)
    removed components → drop their entry
    new components     → queue for placement

place:
  placer sees queue + occupied-slot map only
  cannot move frozen components
  emits slots for new components only

post-run:
  write layout.yml as (kept ∪ new), keys sorted
```

Adding LED6 reads as: "5 LEDs frozen, find a slot for LED6." The diff is one
new key in `layout.yml` plus one new `<path>` in the SVG. Nothing else moves.

### 2. Slots, not raw coordinates

Raw `{x, y}` couples every component's position to every neighbour. Slot-based
values decouple them:

```yaml
# instead of
LED5: { x: 8, y: 3 }

# use
LED5: { region: right-column, row: 4 }
LED6: { region: right-column, row: 5 }
```

Consequences:

- Delete LED3 → column is `{row0, row1, row3, row4, row5}`. Gaps are fine.
  Nothing else moves.
- Re-order LEDs in YAML → rows don't reshuffle; the component ref is the
  stable key.
- Change inter-row spacing → one kernel constant, not 30 coordinates.
- Diffs read semantically: "LED6 added to right-column row 5."

### 3. Named regions with budgeted capacity

The kernel reserves regions on the grid:

```
mcu-center               (fixed, origin)
left-column, right-column             (top-to-bottom rows)
top-row, bottom-row                   (left-to-right cols)
left-of-mcu-pin-N, right-of-mcu-pin-N (for path-form chains)
bus-backbone-{name}                   (fractional 0.0–1.0 for taps)
```

Each region tracks capacity. Placing LED6 is "next empty row in right-column."
The 13th LED triggers an **overflow event** — explicit, not silent reshuffle.

### Overflow response ladder

Ordered by user disruption; always try lower rungs first:

1. **Local grow** — extend the region by one grid unit if the new space is free.
   No existing component moves.
2. **Neighbour nudge** — if grow would collide with an adjacent region, shift
   only that neighbour's anchor by one grid unit and re-place its contents at
   the new anchor. Diff stays localised.
3. **Explicit reflow** — `/circuit layout --reflow` discards `layout.yml` and
   re-runs the placer from scratch. Opt-in only, never automatic. Used when
   the human decides the layout has drifted or after a large topology change.

### Naturally-stable forms

Two connection forms need no special machinery:

- **Path-form chains** — inserting an element mid-path shifts downstream
  elements along the chain direction; nothing outside the chain moves.
  Acceptable local reflow.
- **Bus taps** — fractional positions (0.0–1.0) along the backbone. Inserting
  a tap at 0.35 between existing taps at 0.3 and 0.5 does not displace them.

### AI-loop interaction

Stability shrinks the AI's job:

- Input narrows to "components to place" + occupied-slot map + region
  capacities.
- Small unambiguous additions (next free row in the obvious region) are pure
  kernel work. The AI is only invoked when the kernel sees ambiguity or
  overflow.
- Authoring cost for incremental edits drops to near zero API calls in the
  common case.

### Accumulated-drift caveat

Stability accumulates visual debt. Over time, deletions leave sparse regions
and the schematic looks gap-ridden even though it still renders correctly.
The answer is not automatic re-layout — it is making `--reflow` an explicit,
reviewable event that a maintainer invokes when the cost of drift exceeds
the cost of re-reviewing the whole diagram.

---

## Sidecar metadata and CI contract

**Problem.** CI needs to answer two questions on every PR:

1. Does this circuit need a fresh (AI) layout pass?
2. Is the committed SVG still in sync with its sources?

Both must be answered without running AI on the CI runner and without
cluttering the builder markdown with bookkeeping.

**Answer.** A machine-written sidecar YAML next to the SVG.

### File layout

```
data/
├── esp32.circuit.yml            ← source: topology
└── esp32.layout.yml             ← source: committed slot positions

docs/builders/wiring/esp32/
├── main-circuit.svg             ← generated artifact
└── main-circuit.meta.yml        ← generated sidecar (metadata only)
```

Sources stay in `data/`; generated SVG + sidecar live together in the builder
docs. Builder markdown embeds the SVG with no reference to the sidecar.

### Sidecar contents

```yaml
schema: circuit-meta/v1
sources:
  circuit: data/esp32.circuit.yml
  layout:  data/esp32.layout.yml
hashes:
  circuit:  sha256:abc123…
  layout:   sha256:def456…
  renderer: circuit-skill@0.3.0 + schemdraw@0.19
layout:
  state:  complete              # complete | incomplete | stale
  placed: 23
  total:  23
rubric:
  overlaps:       0
  wire_crossings: 0
  labels_fit:     true
  signal_flow_ok: true
provenance:
  generated_at: 2026-04-24T10:15:00Z
  tool:         /circuit layout
  iterations:   3
reviewed:                       # optional, human-authored
  by:   tobias
  date: 2026-04-22
  note: accepted for pedal v0.5
```

The `reviewed` block is the only human-authored field. Everything else is
written by the skill.

### CI decision flow

```
1. Parse .circuit.yml  → component set C
2. Parse layout.yml    → slot set L
3. If C ⊄ L:
     fail: "components [X, Y] have no layout entry.
            run /circuit layout locally and commit layout.yml"
     STOP — do NOT attempt to place anything in CI.

4. Compute H = hash(circuit.yml, layout.yml, renderer_version)
5. If meta.hashes == H AND meta.layout.state == complete:
     trust committed SVG; fast-path pass.
6. Else:
     re-render from sources.
     if rendered_svg == committed_svg:
       pass, but flag meta as drifted (hashes need refresh).
     else:
       fail: "SVG out of sync with sources;
              commit regenerated SVG and meta.yml"
```

Properties this gives us:

- **CI never runs AI.** Step 3 is the hard gate; incomplete layout points the
  author at the local skill invocation.
- **Fast path when nothing changed.** Hash match in step 5 skips rendering
  entirely — useful for PRs that touch unrelated files.
- **Defensive fallback.** Hash mismatch triggers re-render + diff, not an
  immediate fail. SVG equality remains the ground truth.

### What the sidecar is NOT

- **Not source of truth.** If lost, regenerate. `.circuit.yml` and `layout.yml`
  are authoritative.
- **Not human-authored** (except the optional `reviewed` block).
- **Not embedded in builder markdown.** The markdown stays `![](main-circuit.svg)`
  and nothing more.

### PR review surface

The sidecar is diffable YAML, so schematic changes surface cleanly in review:

```diff
 rubric:
-  overlaps:       1
+  overlaps:       0
 provenance:
-  iterations:   5
+  iterations:   3
```

Reviewers can see at a glance that a layout pass converged cleanly, without
having to eyeball pixels.

---

## Manual layout escape hatches — why they are (mostly) a bad idea

The question of letting humans edit the schematic by hand — in draw.io, Inkscape,
Excalidraw, or any SVG editor — keeps coming up and the temptation is real. This
section records why the honest answer is **"design-space reserved, not built,"**
and why the default stance should stay "the auto pipeline owns the diagram."

### Five structural problems

**1. Divergence is silent.** `.circuit.yml` and the SVG drift apart with no hard
check to stop them. ERC, BOM, and netlist all read from YAML; a human edit
that only touches the picture will never trip those gates. The picture looks
right, the tools say "OK," the builder wires a broken circuit.

**2. Layout stability collapses.** The slot vocabulary and incremental placer
exist precisely so that adding LED6 is a one-line diff and LED1–5 don't move.
Once a human edits the SVG directly, the slot abstraction is gone — every
subsequent change is geometry work on a free canvas.

**3. Diffs stop being reviewable.** `layout.yml` diffs read semantically
(`right-column row 5 added`). SVG path-data diffs read like
`d="M 12.345 67.89 L 14.0 67.89 …"` × 200 lines. A reviewer cannot tell what
changed without opening the file visually, side-by-side, in two browsers.
Pixel review is slow, error-prone, and the thing the auto pipeline was
supposed to eliminate.

**4. The label-drift check is a fig leaf.** It catches gross divergence
(component present in YAML but absent from SVG, or vice versa). It does not
catch: wrong connection drawn to the wrong pin, flipped polarity, renamed
value on a label whose text didn't change, a capacitor drawn in series when
YAML says parallel. These are electrical errors a hand-drawn edit introduces
silently.

**5. The ratchet effect.** Once one circuit goes manual, the second is easier
to justify, the third is routine. Over time the auto pipeline rots from
disuse — seeders break, rubric checks go untested, kernel improvements stop
because "nobody uses it anyway." The escape hatch eats the thing it was
supposed to escape from.

### Concrete examples

**Example A — the silent polarity flip.**
Contributor opens `main-circuit.svg` in Inkscape to "just move that LED a
little." While dragging, they accidentally flip the element horizontally.
Anode and cathode swap visually. YAML still says `LED5.anode → pin 12,
LED5.cathode → GND`. ERC passes, BOM says one LED, label-drift check passes
(labels unchanged). Builder follows the schematic, wires the LED backwards.
Nothing catches it until the lit-test fails on the bench.

**Example B — the drifting resistor value.**
Contributor decides a pull-up should be 4.7 kΩ instead of 10 kΩ. They
double-click the text in Inkscape, edit "10k" to "4.7k," save. Forget to
update `.circuit.yml`. BOM still says `R3: 10 kΩ`. Builder orders 10 kΩ,
wires it, schematic disagrees with the assembled board. Builder concludes
"the documentation is broken" and starts ignoring it.

**Example C — the reshuffle on add.**
Auto mode, adding LED7: one YAML line, one `layout.yml` line, one new `<path>`
in the SVG. PR diff is three lines, reviewable in thirty seconds.

Manual mode, same change: human opens Inkscape, realizes there's no room in
the current column, shuffles LED4 and LED5 down one grid cell to make space,
redraws three connecting wires. PR diff is ~200 lines of SVG path data.
Reviewer: "I have no idea what changed in this file. LGTM."

**Example D — the unmaintained seeder.**
draw.io updates its XML schema in a minor release. The `/circuit
export-drawio` seeder breaks. The last contributor to use it was six months
ago; nobody notices. A new contributor tries it, gets an error, works around
by editing SVG directly. The seeder stays broken; eventually a cleanup PR
deletes it. Three weeks of original design effort was load-bearing for
nobody.

**Example E — the Fritzing trap.**
A well-meaning contributor ports the build guide to Fritzing breadboard view
because "makers understand breadboards better." Weekend of work, PR opened.
Now the project has three parallel representations — YAML, Schemdraw SVG,
Fritzing `.fzz` — with no clear source of truth. The next contributor asks
"which one do I update?" and the answer is "all of them, sorry." Within two
releases, two of the three are stale.

### What stays acceptable

Two narrow cases remain defensible even with the warnings above:

1. **Annotation overlay.** A separate SVG committed next to the generated
   one, containing only arrows, notes, and highlights. CI ignores it
   entirely. Strictly additive, no drift risk because it carries no
   electrical claims.
2. **One-off final polish for a published artifact.** After a version is
   tagged and the circuit is frozen, a human may hand-edit the SVG for a
   press release, poster, or datasheet-style rendering. Commit it under a
   different filename (e.g. `main-circuit-publication.svg`); do not overwrite
   the generated artifact.

### Recommendation

- **Do not build seeders** (`/circuit export-drawio`, `/circuit
  export-kicad-sch`, etc.) speculatively. Build one only when a real
  maintainer, on a real circuit, has hit a concrete layout need the auto
  pipeline cannot satisfy — and after the annotation-overlay path has been
  tried first.
- **Do not advertise manual modes** in the quick-start docs. The default
  story is "edit YAML, run the skill, commit the outputs."
- **Graduate, do not escape.** The contributor who genuinely needs
  pixel-level schematic control is asking for a real EDA tool. Point them at
  IDEA-011 (KiCad). The netlist exporter is the on-ramp. "Manual layout in a
  drawing tool" is almost never what they actually want.

The contract in the sidecar (`layout.source` enum) stays, so adding a manual
mode later costs nothing today. But the burden of proof sits squarely on the
proposer: show a concrete circuit where the auto pipeline fails, show that
annotation overlay is insufficient, and show that KiCad would be overkill —
only then is a manual escape hatch worth the maintenance cost.

---

## Design review: known gaps

Honest critique of this document read end-to-end, to be addressed before any
Phase-2 implementation begins.

### What's good (keep)

1. **Authoring/CI split.** Running AI at authoring time and committing its
   conclusions as data is the right shape; it dissolves the CI–AI tension
   without tricks.
2. **Slots over raw coordinates.** Load-bearing insight for stability, diff
   readability, and global parameter changes.
3. **Incremental placer as the default.** Freezing existing slots and placing
   only new components is what makes "add LED6" a one-line diff.
4. **Sidecar `meta.yml` with a `layout.source` enum.** One file answers two
   questions (fresh? in sync?); CI contract stays small.
5. **"Graduate to KiCad" framing** for the manual-control case. Clean
   signpost that avoids building a bad escape hatch.
6. **Five concrete failure examples** in the escape-hatch pushback. Future
   challengers of the decision will read them and understand.

### What's bad (fix before Phase 2)

1. **Internal contradiction within this same doc.** The early sections
   (Strategy per connection form, Position override) describe raw-coordinate
   overrides (`layout: { x: 4.5, y: 2.0 }`). The later sections advocate
   slot-based values (`{ region: right-column, row: 4 }`). Both patterns
   co-exist with no reconciliation. Either kill raw coords explicitly or
   define their relationship to the slot vocabulary.
2. **Kernel/AI boundary is fuzzy.** "Small unambiguous additions are pure
   kernel work" (stability section) vs. "AI picks slots from the vocabulary"
   (AI-loop section) are never reconciled. **Who decides something is
   unambiguous — the kernel or the AI?** Without a deterministic "kernel can
   handle this alone" rule, every change requires AI and the cheap-incremental
   promise collapses.
3. **Slot vocabulary is hand-waved.** "5–10 canonical placements per component
   category" is the heart of the proposal and never made concrete. No example
   list, no composition rules, no overflow ordering.
4. **Manhattan router is hand-waved harder.** "Orthogonal routing given
   placements" is a sub-problem. Routing multi-terminal nets without
   crossings is where most layout engines fail; the doc treats it as one
   bullet.
5. **AI-loop convergence is not guaranteed.** "Cap at 5 iterations" is a
   hack. What happens on iteration 6 — commit a broken layout, fail loudly,
   or escalate to human? Undefined.
6. **Labels are absent from the rubric except as "labels fit."** TASK-239
   was a label problem as much as an element problem. Where does a
   component value text go — above, below, right? Does it collide with the
   next row? No treatment.
7. **`--reflow` semantics are unclear.** Does it re-run AI on every
   component? What's the cost? What triggers it — overflow, schema version
   bump, user explicit? Not specified.
8. **Sidecar hash inputs are under-specified.** `renderer_version` alone is
   weak; Schemdraw, matplotlib, font, and Python versions all affect the
   SVG. Either the hash must be more precise, or the "fast path" gets
   downgraded to advisory only.

### What's missing (real gaps)

1. **Schema versioning for `layout.yml` itself.** Rename a region in kernel
   v2 and every committed layout breaks. Needs `schema: layout/v1` plus a
   migration story.
2. **Deterministic no-AI placer.** The kernel must place *at all* without AI:
   for contributors with no API keys, for offline work, for testing the
   kernel itself. A naïve default ("next free row in the canonical region
   for the component's category") is missing and load-bearing.
3. **Label placement as a first-class concept.** Slots should include not
   just component position but label direction (above/below/left/right).
   Without this the rubric keeps failing on label collisions.
4. **Pin grouping strategy.** The MCU has dozens of pins; the slot
   vocabulary doesn't say which pins go on which side or how related pins
   (I2C SDA+SCL, SPI MOSI+MISO+SCK) group. Buried in the MCU profile today;
   needs explicit treatment in layout terms.
5. **Fixture bank / regression suite.** A small library of canonical
   circuits (minimal, MCU+LEDs, MCU+buttons+pull-ups, I2C sensor, bus
   topology, multi-MCU) the kernel+AI must handle. Without this, "good
   enough" has no operational definition.
6. **End-to-end contributor workflow.** When does the placer run — YAML
   save, pre-commit, explicit skill invocation? What does a contributor *do*
   to edit a circuit? Currently described in pieces across the doc, never
   as a single narrative.
7. **Measurement criteria for "readable."** TASK-239's third attempt is
   cited as the bar but there is no numeric threshold. Proposal: element
   density, minimum label-to-element distance, maximum wire-length ratio —
   even rough thresholds beat "looks OK."
8. **Gap comparison with the current `generate-schematic.py`.** Which
   specific circuits and changes does the new design handle that the
   current script does not? Explicit list would ground the whole proposal.
9. **Kernel testing strategy.** No word on unit/snapshot/property tests.
   Given that kernel correctness decides whether AI can save the design,
   this is where the CLAUDE.md testing policy must land most firmly.
10. **Explicit non-goals.** Multi-page schematics, sub-circuit zoom,
    theming/colour, i18n, accessibility — probably all out of scope, but
    name them to stop scope creep.

### The single biggest risk

**The kernel/AI boundary is the whole ballgame, and it is the least
specified part of the doc.** If the kernel can't do ~80% of placements
deterministically, AI cost dominates and incremental edits aren't cheap.
If the kernel tries to do 100%, we're building a real auto-layout engine —
by this doc's own admission, "larger than the rest of the skill combined."

### Three artifacts required before Phase 2

Before writing code, the next design pass must produce:

1. **A concrete list of ~15 slot names with composition rules.**
2. **A decision procedure** of the form: *"given a new component of type T
   with connections C, if the canonical slot is free and adjacent slots
   have room for labels, the kernel places deterministically; otherwise it
   flags ambiguity and escalates to AI."*
3. **A minimum fixture bank** (5 canonical circuits) the design must pass
   before Phase 2 can ship.

Everything else in this document is scaffolding. These three artifacts are
where the design becomes implementable — or remains prose.

---
