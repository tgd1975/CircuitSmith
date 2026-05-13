# ESP32 NodeMCU default build

Generated artefacts for the ESP32 target. Re-rendered from
[`data/esp32.circuit.yml`](../../../../data/esp32.circuit.yml) by the
renderer pipeline; do not edit by hand. The CI staleness guard fails
the build if any file here drifts from a fresh render.

## Artefacts

- [`bom.md`](bom.md) — Bill of materials, Markdown table form.
- [`bom.csv`](bom.csv) — Bill of materials, KiCad importer-friendly CSV.
- [`erc-report.md`](erc-report.md) — Electrical-rule-check findings.
- [`main-circuit.svg`](main-circuit.svg) — Rendered schematic.
- `main-circuit.net` — KiCad netlist (lands with TASK-033).

The BOM table content lives in `bom.md` so it can be transcluded
into a future MkDocs build-guide page via `pymdownx.snippets`. See
[ADR-0013](../../../developers/adr/0013-build-guide-include-via-link.md)
for the embed mechanism rationale.
