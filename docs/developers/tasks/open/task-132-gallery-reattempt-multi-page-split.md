---
id: TASK-132
title: Gallery re-attempt — multi-page split (supersedes TASK-100)
status: open
opened: 2026-05-14
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 23
prerequisites: [TASK-126, TASK-127, TASK-120]
---

## Description

Authors the multi-page-split gallery entry. Picks the
multi-section audio chain shape from TASK-100's candidates: input
buffer → gain stage → tone control → output buffer. Uses
`bjt_npn` profile (TASK-120) for at least one stage so the example
exercises both halves of IDEA-009 (active devices *and* multi-page
rendering).

`pages:` block in `.layout.yml` splits the chain into two pages:
input-side stages on `p1`, output-side stages on `p2`. At least
one signal net spans the page boundary to exercise the cross-page
label glyph from TASK-126.

Single circuit, multi-file output: the renderer emits
`multi-page-split-p1.svg` and `multi-page-split-p2.svg`. The
gallery README's "what makes it interesting" section narrates the
page-break behaviour and walks the cross-page net by name.

Supersedes TASK-100 (kept for history).

## Acceptance Criteria

- [ ] `docs/users/examples/multi-page-split/` gains `circuit.yml`, `layout.yml`, `meta.yml`, `multi-page-split-p1.svg`, `multi-page-split-p2.svg`, `erc-report.md`.
- [ ] The rendered output has exactly two pages (matches TASK-100's "at least two pages" criterion).
- [ ] At least one signal net spans the page boundary; the cross-page label glyph renders correctly on both pages.
- [ ] `README.md` follows the six-section template; the "what makes it interesting" section explicitly narrates the page-break.
- [ ] No "Excessive cross-page net count" warning from TASK-127 (page split chosen with care).
- [ ] All committed SVGs are byte-identical to the renderer's output.

## Test Plan

No new automated tests required — TASK-101's gallery regression
script picks up the multi-file artefacts.

Manual verification:

1. Run the skill against `circuit.yml`; confirm output matches
   the two committed SVGs.
2. Walk every cross-page net label and confirm the reference
   resolves to the other page.
3. `markdownlint-cli2` passes.

## Documentation

- `docs/users/examples/multi-page-split/README.md` — replace the
  blocked-on-IDEA-009 prose with an EPIC-014 implementation
  pointer; fill the SVG (both pages inline) + BOM sections; the
  "what makes it interesting" section names the page-break
  behaviour and walks one cross-page net.

## Prerequisites

- **TASK-126** — cross-page net labels must render; the gallery
  entry showcases this behaviour.
- **TASK-127** — cross-page ERC must accept a correctly-paginated
  multi-page circuit.
- **TASK-120** — bjt_npn profile must exist (the audio-chain
  shape uses at least one BJT stage).

## Notes

- The original TASK-100 listed three candidate shapes; the audio
  chain is chosen here because it composes naturally with the
  bjt_npn profile and produces a clear page-break boundary
  (input-side vs output-side stages). The other candidates
  (multi-rail PSU, sensor-MCU-actuator) are saved for a future
  gallery expansion if needed.
- Pick a page split where ≤ 4 nets cross the boundary; the
  TASK-127 heuristic warns at > 6, but a tight split (≤ 4)
  reads more clearly than one that just stays under the
  warning threshold.
