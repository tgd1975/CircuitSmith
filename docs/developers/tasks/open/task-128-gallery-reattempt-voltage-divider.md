---
id: TASK-128
title: Gallery re-attempt — voltage divider (supersedes TASK-096)
status: open
opened: 2026-05-14
effort: Small (<2h)
complexity: Junior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 19
prerequisites: [TASK-114]
---

## Description

Re-attempts the voltage-divider gallery entry now that the R+R
canonical rule (TASK-114) exists. TASK-096 closed with only
`circuit.yml` and a placeholder `README.md` because the v0.1
kernel had no R+R rule — the rendered SVG, layout.yml, and
meta.yml could not be generated. This task completes the
deliverable.

Supersedes TASK-096 (kept for history). The work:

- Re-run the renderer against the existing
  [`docs/users/examples/voltage-divider/circuit.yml`](../../users/examples/voltage-divider/circuit.yml).
- Commit the produced `voltage-divider.svg`, `layout.yml`,
  `meta.yml`, `erc-report.md` byte-identical.
- Edit the existing
  [`docs/users/examples/voltage-divider/README.md`](../../users/examples/voltage-divider/README.md)
  to replace the "blocked-on-IDEA-008" note with an
  implementation note pointing at EPIC-014, and fill the SVG +
  BOM sections of the six-section template.

The voltage-divider's `.circuit.yml` is already committed and
electrically sound (it passed ERC standalone in TASK-096); it just
needs a kernel that knows how to place R+R.

## Acceptance Criteria

- [ ] `docs/users/examples/voltage-divider/` gains `voltage-divider.svg`, `layout.yml`, `meta.yml`, `erc-report.md`.
- [ ] `README.md`'s blocked-on note is replaced with an implementation note (EPIC-014 / TASK-114).
- [ ] `README.md` follows the six-section template fully (SVG inline, BOM table populated).
- [ ] The committed SVG is byte-identical to the output of running the skill against the committed `circuit.yml`.

## Test Plan

No new automated tests required — the SVG diff is covered by
TASK-101's gallery regression script (which currently skips this
entry because the SVG is missing; the skip lifts once the SVG
lands).

Manual verification:

1. Run the skill against `circuit.yml`; confirm output matches the
   committed artefacts byte-for-byte.
2. Check the BOM table reads as two resistors with the values from
   the YAML.
3. `markdownlint-cli2` passes.

## Documentation

- `docs/users/examples/voltage-divider/README.md` — replace the
  blocked-on-IDEA-008 prose with an EPIC-014 implementation
  pointer; fill the SVG + BOM sections of the six-section
  template.

## Prerequisites

- **TASK-114** — R+R voltage-divider canonical rule must exist
  for the kernel to place the circuit.

## Notes

- This task is `complexity: Junior` because the engineering is
  already done in TASK-114; the work here is running the
  renderer and updating prose.
