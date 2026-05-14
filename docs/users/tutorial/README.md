# Tutorial

A linear, ~30-minute walkthrough from a minimal `.circuit.yml` to a
BOM round-trip. Each step layers a new concept on top of the
previous one — read in order on a first pass; jump around once you
know what each step covers.

## Steps

| # | Step | Covers |
|---|---|---|
| 1 | [Minimal circuit](01-minimal-circuit.md) | The smallest end-to-end pipeline: one resistor, one LED, one source. |
| 2 | [A second branch](02-fan-out.md) | Net fan-out — multiple components share one node. |
| 3 | [Sub-blocks](03-sub-blocks.md) | Reusable building blocks (e.g. an RC filter) used twice. |
| 4 | [Fixing an ERC failure](04-erc-fix.md) | Trigger an ERC check, read the diagnostic, fix the YAML. |
| 5 | [Exporting the BOM](05-bom-export.md) | The BOM round-trip — what gets emitted, how to read it. |
| 6 | [Iterating on layout](06-layout-iteration.md) | Reading `meta.yml`, nudging the placer with `.layout.yml`. |

## How to use the tutorial

- Each step's `.circuit.yml`, generated `.layout.yml`, `meta.yml`,
  and rendered SVG live in this directory next to the step's
  Markdown file. The prose **references** those files rather than
  pasting their content — running the example end-to-end on your
  own machine should produce byte-identical output.
- CI re-runs every step's `.circuit.yml` through the pipeline and
  fails the build on drift, per
  [TASK-101](../../developers/tasks/open/task-101-ci-regression-diff-for-gallery.md).
  Treat the committed artefacts as the canonical output.

## See also

- [Example gallery](../examples/) — finished circuits you can read
  cold without following a step-by-step.
- Developer docs:
  - [`circuit-yaml.md`](../../developers/circuit-yaml.md) — full
    `.circuit.yml` reference.
  - [`ARCHITECTURE.md`](../../developers/ARCHITECTURE.md) — how the
    pipeline fits together.
  - [`erc-checks.md`](../../developers/erc-checks.md) — what each
    ERC check enforces.

> Status: tutorial step content is filled in across
> [TASK-094](../../developers/tasks/open/task-094-tutorial-steps-1-3-minimal-and-fan-out.md)
> (steps 1-3) and
> [TASK-095](../../developers/tasks/open/task-095-tutorial-steps-4-6-erc-bom-iteration.md)
> (steps 4-6) of EPIC-012. Until those land, the step files are
> placeholders.
