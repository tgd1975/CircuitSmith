---
status: complete
---

# Step 3 — Sub-blocks

## What you'll do

Replace step 2's three hand-wired `(R + LED)` chains with a single
`sub-blocks:` definition instantiated three times, and learn how
the kernel still recognises each instance as one canonical `R+LED`
shape stacked in the right column.

## What a sub-block is

A **sub-block** is a named, reusable mini-circuit you declare
once and instantiate by reference. The `sub-blocks:` map defines
its internal components, connections, and the **ports** through
which the surrounding circuit talks to it. The `instances:` map
mints concrete copies.

The renderer **flattens** sub-blocks before the placer runs: each
instance's components are renamed `<local-refdes>_<instance>`
(e.g. `R_PWR`, `D_PWR`) and the instance's internal nets are
prefixed with the instance name. From there the rest of the
pipeline — ERC, kernel, router, BOM, KiCad netlist — sees one
flat circuit. The first-class sub-block syntax shipped in
[EPIC-014](../../developers/tasks/active/epic-014-circuit-library-and-renderer-v2.md);
the EPIC-014 frozen-decisions table fixes the contract for
refdes flattening, port naming, and nesting rules.

## The `.circuit.yml`

[`03-sub-blocks.circuit.yml`](03-sub-blocks.circuit.yml) declares
one `led_indicator` sub-block — an `R` in series with an `LED`,
with `drive` and `gnd` ports — and instantiates it three times
(`PWR`, `BT`, `ERR`). The top-level `connections:` wires each
instance's `drive` port to a GPIO pin (`U1.D2`, `U1.D4`, `U1.D5`)
and joins every instance's `gnd` port to the shared `GND` net.

Two structural notes worth reading the YAML carefully for:

- The sub-block's internal `R→LED` chain uses `path:` form, not
  `pins:`. The kernel's R+LED rule walks `path:`-sourced nets;
  declaring the chain as a path is what lets each instance be
  detected as an R+LED pair after flattening.
- The schema's `instance:` block only carries `sub-block:` in
  v1 — there is no per-instance override for component values,
  labels, or LED colour. Every instance of a sub-block is
  electrically identical; differentiation lives in the top-level
  `connections:` (which net the instance's `drive` port joins).

## Running the skill

Same renderer command as before:

```bash
python -m circuitsmith.renderer \
  --circuit docs/users/tutorial/03-sub-blocks.circuit.yml \
  --out    docs/users/tutorial/03-sub-blocks.svg \
  --out-layout      docs/users/tutorial/03-sub-blocks.layout.yml \
  --out-meta        docs/users/tutorial/03-sub-blocks.meta.yml \
  --out-erc-report  docs/users/tutorial/03-sub-blocks.erc-report.md \
  --no-ai
```

## The output

![Repeated sub-blocks](03-sub-blocks.svg)

Read [`03-sub-blocks.layout.yml`](03-sub-blocks.layout.yml) — the
placer sees `D_PWR`, `D_BT`, `D_ERR` (the flattened LEDs) and
`R_PWR`, `R_BT`, `R_ERR` (the flattened resistors):

- All three LEDs land in `region: right-column`, on rows `0`,
  `1`, `2`. The kernel's `next-free` row bookkeeping stacks the
  instances in lexicographic order of the flattened refdes.
- Each resistor is `attached-to:` its LED. The "resistor rides
  with the LED" rule fires once per instance.
- Every LED's `topology-fingerprint` is a SHA-1 prefix of the
  canonical `(rule ID, shape form)` pair. The fingerprints differ
  per instance because each LED sits on a different driver net
  (`LED_PWR` / `LED_BT` / `LED_ERR`), but the placement *shape*
  is identical.

The renderer also writes an `instances:` block into the meta
sidecar — see [`03-sub-blocks.meta.yml`](03-sub-blocks.meta.yml).
Each entry names the sub-block, a human-readable label, and the
flat refdes constituents. Downstream tools (BOM grouping, the
in-progress inline-box SVG annotator) read this map instead of
re-running the flattener.

## What just happened

Three subsystems exercised in this step:

- The **netgraph flattener** (`flatten_sub_blocks()`) — mints
  `<local>_<instance>` refdes and prefixes instance-internal net
  names so global nets stay unique across instances.
- The **layout kernel's canonical-rule matcher** — applies the
  R+LED rule independently to each post-flatten pair, producing
  the stacked-instances layout.
- The **sub-block ERC checks** (E11–E15) — validate that every
  instance's `sub-block:` resolves, every `<instance>.<port>`
  reference in top-level `connections:` is declared, and no
  sub-block instantiates another sub-block (nested sub-blocks
  are out of scope in v1).

Deep-dive references:

- [`circuit-yaml.md`](../../../.claude/skills/circuit/docs/circuit-yaml.md)
  — `sub-blocks:` / `instances:` / `ports:` grammar with
  worked examples.
- [`layout.md`](../../../.claude/skills/circuit/docs/layout.md) —
  slot vocabulary, region names, the **inline-box mode** the
  renderer ships in this epic.
- [ADR-0001](../../developers/adr/0001-slots-not-coordinates.md)
  — why the kernel speaks slots rather than coordinates; the
  invariant the canonical-rule matcher leans on.

## Next

You've now seen authoring, fan-out, and reusable sub-blocks. The
tutorial pivots from authoring to **diagnostics** in the second
half.

[Step 4 — Fixing an ERC failure](04-erc-fix.md) — author a circuit
that the ERC engine rejects, read the diagnostic, fix it.
