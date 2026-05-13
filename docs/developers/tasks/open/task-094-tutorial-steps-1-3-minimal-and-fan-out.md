---
id: TASK-094
title: Tutorial — steps 1-3 (minimal circuit, fan-out, sub-blocks)
status: open
opened: 2026-05-13
effort: Medium (2-8h)
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

- [ ] `01-minimal-circuit.md`, `02-fan-out.md`, `03-sub-blocks.md`
      are filled in with the structure above.
- [ ] Each step's `.circuit.yml`, `.layout.yml`, `meta.yml`, and
      rendered SVG are committed alongside the prose.
- [ ] Every code block / command in the prose is generated from
      (or trivially excerpted from) the committed files — no
      copy-pasted YAML.
- [ ] `markdownlint-cli2` passes; rendered SVGs are valid SVG.

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
