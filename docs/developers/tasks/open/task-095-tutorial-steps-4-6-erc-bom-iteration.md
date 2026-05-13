---
id: TASK-095
title: Tutorial — steps 4-6 (ERC fix, BOM export, layout iteration)
status: open
opened: 2026-05-13
effort: Medium (2-8h)
complexity: Medium
human-in-loop: Clarification
epic: tutorial-and-examples
order: 4
prerequisites: [TASK-094]
---

## Description

Write the second half of the tutorial — the "real-world workflow"
half. Three steps:

### Step 4 — Fix an ERC error on purpose

Introduce a deliberately broken `.circuit.yml` (e.g. a floating
input, or a missing pull-up where the rule catalog expects one),
show the ERC report's output in `meta.yml`, walk through reading the
rule catalog reference (`docs/erc-checks.md`) for the offending
rule, then fix the input and re-run. The user learns: how ERC
failures surface, how to find the rule's rationale, and how to
iterate on a fix.

### Step 5 — Export the BOM

Generate the BOM in Markdown and CSV form, embed the table in a
hypothetical build guide, then round-trip the CSV into PartsLedger
(`$CS_PARTSLEDGER_PATH`). The PartsLedger half is **manual** — the
step describes the procedure but does not pretend to automate the
cross-repo integration. The user learns: the BOM is a first-class
deliverable, not a side effect.

### Step 6 — Iterate on the layout

Tweak a layout hint (component group, fixed slot, page break),
regenerate, diff the SVG to see what changed. The user learns: the
layout is *parametric* through hints, not fixed; iteration is fast
because the layout layer is separable from the schema layer.

Each step uses the same shape established in TASK-094: what you'll
do, input YAML, command, output, explanation, next-step pointer.

The "fix an ERC error" step is the trickiest because the prose must
explicitly walk a *failure* state without the SVG embed breaking
markdown rendering. Approach: commit the broken `.circuit.yml`, the
ERC failure's `meta.yml` (which exists even on failure), and a
"no SVG produced" placeholder. Then commit the fixed `.circuit.yml`
and its full artefact set.

## Acceptance Criteria

- [ ] `04-erc-fix.md`, `05-bom-export.md`, `06-layout-iteration.md`
      are filled in with the same shape as TASK-094's three steps.
- [ ] Step 4 commits both the broken and the fixed `.circuit.yml`
      and the corresponding artefacts; the prose makes the
      before/after relationship explicit.
- [ ] Step 5 documents the manual PartsLedger round-trip procedure
      without automating it. Includes a note pointing at IDEA-005
      (PartsLedger inventory as input) as the related future work.
- [ ] Step 6 commits at least two layout iterations (before/after
      hint change) and shows the SVG diff in prose.
- [ ] `markdownlint-cli2` passes.

## Test Plan

No automated tests required — change is documentation.

Manual verification:

1. Step 4: confirm the broken `.circuit.yml`'s ERC failure mode
   matches what the user sees when they actually run the skill.
2. Step 5: do the PartsLedger round-trip manually once, end-to-end,
   and confirm the documented procedure actually works.
3. Step 6: confirm the layout-hint syntax in the example matches
   the renderer's current input expectations.
4. End-to-end: a fresh reader can complete steps 4-6 in the second
   ~15 minutes of the ~30-minute tutorial budget.

## Prerequisites

- **TASK-094** — steps 1-3 establish the structure and conventions
  steps 4-6 follow.

## Notes

- The committed-failure-state pattern in step 4 is unusual; consider
  whether to additionally commit a `_failure_artifacts/` sub-directory
  to keep the broken-state files visually separated from the
  fix-state files. Decide at authoring time, not in the task spec.
- The PartsLedger half of step 5 is the soft edge of this tutorial.
  If the integration cannot be performed cleanly today (path issues,
  schema mismatch, etc.), the step should still describe the
  *intent* and link to IDEA-005 — but not pretend a broken
  integration works.
