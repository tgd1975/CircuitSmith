---
status: complete
---

# Step 5 — Exporting the BOM

## What you'll do

Take the step 3 circuit (three R+LED indicator sub-blocks) and emit
its Bill of Materials in both Markdown table and CSV form. Look at
how the exporter groups instances (three identical resistors
collapse into one row; three differently-coloured LEDs stay
separate). Then walk through the *manual* round-trip to
PartsLedger, which the integration intentionally does not automate
yet.

## The `.circuit.yml` (re-using step 3)

Step 5 uses the step 3 circuit
[`03-sub-blocks.circuit.yml`](03-sub-blocks.circuit.yml) verbatim —
no new input file. The BOM exporter walks `components:` directly
(per [ADR-0004](../../developers/adr/0004-exporter-decoupling.md))
without consulting the netgraph, so the input is just the
`.circuit.yml` plus the component profile registry.

## Running the exporter

The BOM exporter ships as a library module — there is no dedicated
CLI. The shipped pipeline driver
([`scripts/regenerate_circuit_artefacts.py`](../../../scripts/regenerate_circuit_artefacts.py))
hard-codes the `data/<target>.circuit.yml` →
`docs/builders/wiring/<target>/bom.{md,csv}` paths it walks; for a
one-off `.circuit.yml`, a four-line Python snippet does the same
job:

```python
from pathlib import Path
from ruamel.yaml import YAML
from circuitsmith.export.bom_exporter import export as export_bom
from circuitsmith.schema.registry import load_profiles

profiles = load_profiles()
circuit = YAML(typ="safe").load(
    Path("docs/users/tutorial/03-sub-blocks.circuit.yml").read_text()
)
md, csv_text = export_bom(circuit, profiles)
Path("docs/users/tutorial/05-bom-export.bom.md").write_text(md)
Path("docs/users/tutorial/05-bom-export.bom.csv").write_text(csv_text)
```

Run with `.venv/bin/python -c "<snippet>"` or save as a one-off
script. A dedicated `python -m circuitsmith.export.bom_exporter`
CLI is a reasonable follow-up; until it lands, the snippet is the
documented path.

## The output

The two artefacts the snippet writes:

- [`05-bom-export.bom.md`](05-bom-export.bom.md) — Markdown table,
  ready to embed in a build guide.
- [`05-bom-export.bom.csv`](05-bom-export.bom.csv) — CSV with the
  column headers KiCad's BOM importer expects (`Reference`, `Type`,
  `Value`, `Footprint`, `Datasheet`, `Manufacturer`).

The Markdown table reads:

```text
| Ref                | Component         | Variant | Qty |
|--------------------|-------------------|---------|-----|
| D_BT               | LED               | green   | 1   |
| D_ERR              | LED               | red     | 1   |
| D_PWR              | LED               | blue    | 1   |
| J1                 | USB-C             |         | 1   |
| R_BT, R_ERR, R_PWR | R                 | 220 Ω   | 3   |
| U1                 | ESP32 NodeMCU-32S |         | 1   |
```

The interesting line is the resistor row: the exporter collapsed
three identical 220 Ω resistors (`R_BT`, `R_ERR`, `R_PWR`) into one
group with quantity 3, and named all three references in the `Ref`
column. The three LEDs stay on separate rows because their
`color:` variant differs — that's the per-category variant
projection from
[`idea-001.exporters.md`](../../developers/ideas/archived/idea-001.exporters.md).

The CSV form is *un-grouped* — one row per reference designator —
because KiCad's importer wants one row per physical part to
populate its component placement. The Markdown form is for
humans; the CSV form is for the tool downstream.

## Round-tripping to PartsLedger

The companion project
[**PartsLedger**](https://github.com/tgd1975/PartsLedger) keeps the
authoritative parts inventory CircuitSmith reads. The eventual
round-trip is:

1. CircuitSmith emits `bom.csv` for a circuit.
2. PartsLedger ingests that CSV, marks the listed parts as
   "consumed by build X," and surfaces shortages or substitutes.
3. CircuitSmith re-renders the circuit *preferring* on-hand parts
   from the inventory when authoring new circuits.

**Status today: step 1 is automated; steps 2 and 3 are manual.**
The `$CS_PARTSLEDGER_PATH` environment variable from
[`.envrc.example`](../../../.envrc.example) holds the path to a
sibling PartsLedger checkout, but no consumer in CircuitSmith reads
from it yet — the inventory-as-input link is filed as
[IDEA-005](../../developers/ideas/open/idea-005-partsledger-inventory-as-input.md).

Until that idea lands, the manual procedure is:

1. Generate the BOM with the snippet above.
2. Copy `05-bom-export.bom.csv` into PartsLedger's inventory
   workflow (consult that repo's README for the import path).
3. Use PartsLedger's UI to mark parts consumed, identify
   shortages, or pick substitutes.
4. Update the `.circuit.yml` by hand if a substitute is needed
   (e.g. swap a 220 Ω resistor for the 330 Ω your inventory
   actually has).
5. Re-run the renderer and re-export the BOM.

The integration is intentionally manual at v0.1 — automating it
before IDEA-005 has a design would lock in choices the inventory
project may not yet be ready to honour.

## What just happened

Two subsystems exercised:

- **The BOM exporter** read `components:`, grouped by category +
  variant, and emitted two forms (Markdown table for humans, CSV
  for tools). It did *not* consult the netgraph — that's an
  invariant in [ADR-0004](../../developers/adr/0004-exporter-decoupling.md).
- **The variant projection** — per-category logic that decides
  what counts as "the same part." For resistors it's `value`; for
  LEDs it's `color`; for capacitors it's `value` (and
  `dielectric` if declared).

## Next

[Step 6 — Iterating on layout](06-layout-iteration.md) — tweak a
`.layout.yml` hint, regenerate, see the SVG change. The layout
layer is parametric, not fixed.
