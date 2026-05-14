---
id: TASK-096
title: Example gallery — voltage divider
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: Clarification
epic: tutorial-and-examples
order: 5
prerequisites: [TASK-093]
---

## Description

The smallest meaningful gallery entry: a two-resistor voltage
divider. Single page, no active devices, no biasing, no exotic
components. Establishes the gallery directory's conventions.

Deliverable: `docs/users/examples/voltage-divider/` containing:

- `circuit.yml` — the input.
- `layout.yml`, `meta.yml` — the generated layout artefacts.
- `voltage-divider.svg` — the rendered output.
- `README.md` — what the example demonstrates and what makes it
  the "minimal" gallery entry. Includes the rendered SVG inline,
  the input YAML in a code block (excerpted from `circuit.yml`),
  and a short "what to read next" pointer to the next example.

Gallery README conventions to lock in here (followed by TASK-097
through TASK-100):

1. **Top heading**: H1 with the example's name.
2. **What it demonstrates**: one paragraph, no jargon.
3. **The input**: fenced YAML excerpt from the committed
   `circuit.yml` (do not paraphrase).
4. **The output**: the SVG inline + the BOM table (if non-trivial).
5. **What makes it interesting**: a short prose paragraph naming
   the subsystems exercised and any layout / ERC subtleties.
6. **Next example**: pointer to the next entry in the gallery's
   suggested reading order.

The voltage divider is deliberately first because its README sets
the template every other example follows.

## Acceptance Criteria

- [~] `docs/users/examples/voltage-divider/` exists with all four
      artefacts (`circuit.yml`, `layout.yml`, `meta.yml`, the SVG).
      **Partial — only `circuit.yml` and `README.md` are committed;
      the three rendered artefacts (SVG, layout, meta) are blocked
      on IDEA-008 (see Outcome).**
- [x] `README.md` follows the six-section structure above.
- [~] The committed SVG is byte-identical to the output of running
      the skill against the committed `circuit.yml`.
      **Not applicable until SVG lands — the v0.1 kernel cannot
      render this circuit under `--no-ai`.**
- [x] The example index in `docs/users/examples/README.md` (from
      TASK-093) gains a row for this entry. (Index was authored in
      TASK-093; no edit required.)

## Outcome

Hit a hard v0.1 layout-kernel limitation at first attempt. The
voltage divider's `R + R` topology between VCC and GND has no
canonical rule in the kernel (which today covers only `R + LED`
and `R + pull-up`). Under `--no-ai` — the CI default per ADR-0002
— the kernel escalates with `no-canonical-rule` on the second
resistor and refuses to place it. Under `--ai`, the Anthropic SDK
is missing from the venv and the per-render LLM cost would not be
appropriate for a committed gallery fixture anyway.

What landed:

- [`docs/users/examples/voltage-divider/circuit.yml`](../../users/examples/voltage-divider/circuit.yml)
  — the input. Electrically sound; the ERC engine (run
  standalone) accepts it with the expected E9 pending-promotion
  warning only.
- [`docs/users/examples/voltage-divider/README.md`](../../users/examples/voltage-divider/README.md)
  — the gallery README in the six-section template the task body
  specifies, with an honest "v0.1 layout-kernel limitation" note
  explaining why the SVG is not yet committed and pointing at
  IDEA-008 for the unblocking work.

What did **not** land (deferred until IDEA-008 closes):

- The rendered `.svg`, `.layout.yml`, `.meta.yml`, and
  `.erc-report.md` (the latter is renderer-driven; the standalone
  ERC report is plain text and the renderer is the markdown
  formatter for `.md` reports).

This task closes as "scaffolded with documented blocker" rather
than waiting on IDEA-008 — the gallery README template is
established for TASK-097..100 to follow, the input YAML is
committed and ready to render the moment the kernel unblocks, and
TASK-101's CI regression script will skip this entry until the
SVG appears.

The same kernel limitation blocks TASK-097..100 plus the
underlying component-profile gaps (BJT, 555, op-amp, multi-page
support). Those tasks land with the same shape and the same
follow-up pointer.

## Test Plan

No automated tests required — change is documentation. Regression
coverage for the committed artefacts lands in TASK-101.

Manual verification:

1. Run the skill against `circuit.yml`; confirm output matches the
   committed artefacts.
2. `markdownlint-cli2` passes.

## Prerequisites

- **TASK-093** — the example sub-directory and gallery index must
  exist.

## Notes

- This task is `complexity: Junior` deliberately — the technical
  content is the simplest possible circuit. The complexity lives in
  *establishing the template*, which is a documentation skill, not
  a circuit-design skill.
- Don't add a third resistor "for interest". The whole point of the
  voltage divider is that it's the smallest non-trivial gallery
  entry; complicating it defeats its role.
