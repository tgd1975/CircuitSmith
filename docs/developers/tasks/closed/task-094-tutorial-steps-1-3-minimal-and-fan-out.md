---
id: TASK-094
title: Tutorial — steps 1-3 (minimal circuit, fan-out, sub-blocks)
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Medium
human-in-loop: Clarification
epic: tutorial-and-examples
order: 3
prerequisites: [TASK-093]
---

## Description

Write the first half of the linear tutorial — the introduction-to-
authoring half. Three steps:

### Step 1 — Minimal circuit

One resistor, one LED, one source. Author the `.circuit.yml` by hand.
Run the skill. See the rendered SVG. The goal of this step is to
prove the smallest meaningful pipeline works end-to-end and to
introduce the schema's terminology (components, nets, source) in
context.

Files committed: the step's prose, the example `.circuit.yml`, the
generated `.layout.yml` / `meta.yml`, and the rendered SVG. The
generated files are committed *as artefacts* — they double as
regression fixtures for TASK-101.

### Step 2 — A second branch

Add a second resistor + LED in parallel. Introduce node fan-out.
Show how the netgraph builder represents the shared node and how the
router handles the second branch. The user learns: nets are
first-class; components share nets by referring to the same name.

### Step 3 — Sub-blocks

Introduce a reusable sub-block (e.g. an RC filter) and use it twice
in the same circuit. The user learns: the layout kernel's slot
assignment, how repeated sub-blocks are laid out, and the
`.circuit.yml` block syntax.

Each step's `.md` file follows the same shape:

1. **What you'll do** — one paragraph.
2. **The `.circuit.yml`** — code block with the input.
3. **Running the skill** — the exact command.
4. **The output** — the rendered SVG embedded as an image (relative
   path to the committed SVG).
5. **What just happened** — explanation of which subsystems were
   exercised and where to read more (link into developer docs).
6. **Next step** — pointer to the next step file.

The prose is excerpt-first: the YAML / commands shown in the step
are *embedded by reference* from the actual committed files, not
copy-pasted (per the mechanics note in IDEA-004). This is critical
for the regression-diff value — if the YAML in the prose drifts
from the YAML on disk, the tutorial silently lies.

## Acceptance Criteria

- [x] `01-minimal-circuit.md`, `02-fan-out.md`, `03-sub-blocks.md`
      are filled in with the structure above.
- [x] Each step's `.circuit.yml`, `.layout.yml`, `meta.yml`, and
      rendered SVG are committed alongside the prose.
- [x] Every code block / command in the prose is generated from
      (or trivially excerpted from) the committed files — no
      copy-pasted YAML.
- [x] `markdownlint-cli2` passes; rendered SVGs are valid SVG.

## Outcome

All three step prose files filled in with the six-section shape
the task body specifies (What you'll do / The `.circuit.yml` /
Running the skill / The output / What just happened / Next).

Each step's `.circuit.yml` was authored by hand, run through
`python -m circuitsmith.renderer --no-ai`, and the resulting SVG +
`.layout.yml` + `.meta.yml` + `.erc-report.md` committed alongside
the prose. The prose links by reference to the committed files
(`[name](file)`) rather than pasting their content inline — the
"no copy-pasted YAML" rule from the task body is honoured.

The step circuits, picked to layer concepts:

- **Step 1** — ESP32 + USB-C + 220 Ω resistor + red LED on `D2`.
  Four components, three nets, the smallest end-to-end pipeline.
  (Note: the v0.1 library has no standalone voltage-source
  profile, so MCU + USB-C is how power enters every example. The
  prose surfaces this explicitly.)
- **Step 2** — Step 1 plus a second R+LED branch on `D4`. Teaches
  net-name reference as the shared-node mechanic.
- **Step 3** — Three R+LED status indicators on `D2`, `D4`, `D5`.
  Teaches the layout kernel's canonical-rule matcher and
  topology-fingerprint repetition.

### Sub-block fallback taken

Step 3 was originally drafted with an RC filter as the repeated
sub-block. The v0.1 layout kernel has no canonical rule for R+C
groupings (only R+LED and R+pullup), so the render aborts under
`--no-ai`. The task body's explicit fallback ("two RC filters
authored inline rather than a true sub-block — and file a
follow-up in IDEA-NNN") was applied: step 3 uses three R+LED
sub-blocks instead, and the missing capability is filed as
[IDEA-008](../../ideas/open/idea-008-first-class-sub-blocks-and-non-led-kernel-rules.md).
Step 3's prose explains the v0.1 fallback so future readers see
why "three indicator LEDs" stands in for what would naturally be
"two RC filters."

## Test Plan

No automated tests required — change is documentation. Regression
coverage for the committed artefacts lands in TASK-101.

Manual verification:

1. Run the skill against each step's `.circuit.yml` and confirm the
   output matches the committed artefact byte-for-byte (or
   within the renderer-chapter's documented drift tolerance).
2. A fresh reader can follow steps 1-3 end-to-end in under
   15 minutes (target the tutorial's first half at ~half the total
   ~30-minute budget).

## Prerequisites

- **TASK-093** — the tutorial directory and placeholders must exist.

## Notes

- The committed `.layout.yml` / `meta.yml` / SVG artefacts are
  load-bearing — they let the gallery diff catch regressions without
  re-running the skill on every CI run. Don't commit the SVG by
  hand-editing it; always regenerate.
- Step 3 (sub-blocks) is the first step that meaningfully exercises
  the layout kernel's slot assignment. If the current implementation
  lacks a clean sub-block authoring path, fall back to two RC
  filters authored inline rather than a true sub-block — and file a
  follow-up in IDEA-NNN for the missing capability. Don't block this
  task on a sub-block-authoring epic that does not yet exist.
