---
id: TASK-129
title: Gallery re-attempt — common-emitter amplifier (supersedes TASK-097)
status: closed
opened: 2026-05-14
closed: 2026-05-14
effort: Small (<2h)
complexity: Senior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 20
prerequisites: [TASK-120, TASK-123]
---

## Description

Authors the common-emitter-amplifier gallery entry's `circuit.yml`
against the new `bjt_npn` profile (TASK-120). Single page. Replaces
TASK-097's placeholder README + missing artefacts.

Per TASK-097's notes, pick BJT biasing values for a plausible
audio-frequency amplifier (Av ≈ 10, biased for ~half-supply at the
collector). Random values produce a circuit that renders fine but
reads as nonsense to anyone who actually does electronics.

The deliverable matches the gallery convention established in
TASK-096:

- `circuit.yml` — the input.
- `layout.yml`, `meta.yml` — the generated layout artefacts.
- `common-emitter-amplifier.svg` — the rendered output.
- `erc-report.md` — clean except for any expected biasing-related
  educational warnings.
- `README.md` — six-section template, with the "what makes it
  interesting" paragraph naming the direction-sensitive-active-
  device concept.

Supersedes TASK-097 (kept for history).

## Acceptance Criteria

- [ ] `docs/users/examples/common-emitter-amplifier/` gains `circuit.yml`, `layout.yml`, `meta.yml`, `common-emitter-amplifier.svg`, `erc-report.md`.
- [ ] BJT biasing values produce a plausible amplifier (Av ≈ 10, ~half-supply at collector).
- [ ] `README.md` follows the six-section template fully; the SVG + BOM sections are populated.
- [ ] ERC report is clean (no errors) — any warnings are educational, not defects.
- [ ] The committed SVG is byte-identical to the renderer's output.

## Test Plan

No new automated tests required — TASK-101's gallery regression
script will pick up the new artefacts.

Manual verification:

1. Run the skill against `circuit.yml`; confirm output matches the
   committed artefacts byte-for-byte.
2. Compute the small-signal gain on paper from the biasing
   resistors and the collector resistor; verify Av is in the
   target ballpark.
3. `markdownlint-cli2` passes.

## Documentation

- `docs/users/examples/common-emitter-amplifier/README.md` —
  replace the blocked-on-IDEA-009 prose with an EPIC-014
  implementation pointer; fill the SVG + BOM sections.

## Prerequisites

- **TASK-120** — bjt_npn profile must exist for the YAML to
  reference.
- **TASK-123** — active-device ERC must accept a correctly
  authored CE amplifier (BJT pin-role-unset rule passes negative
  case).

## Notes

- The complexity is `Senior` because the circuit design choices
  (biasing values, coupling cap sizing) require electronics
  knowledge to do convincingly. Don't delegate the value choices
  to pure aesthetic judgement.
- The original TASK-097 has a checklist of what the example
  should stress (layout kernel's analog-flow handling, ERC
  catalog coverage of biasing topology, BOM with caps + Rs +
  active device). Pull from that as the prose backbone for the
  "what makes it interesting" section.
