# circuit — schematic generation from declarative YAML

`circuit` is a Claude Code skill that takes a declarative
`.circuit.yml` description (components + connections), validates it
against the rule catalog, and emits a documentation-quality SVG
schematic, a BOM, and a KiCad-compatible netlist.

This page is the install + first-circuit walkthrough. For the format
itself, see [`docs/components.md`](components.md) and
[`docs/circuit-yaml.md`](circuit-yaml.md). The dossier behind the
design lives in `docs/developers/ideas/archived/idea-001*.md` in the
host project; it is not duplicated here.

## Status

The full `/circuit` skill workflow is wired up: declarative
`.circuit.yml` authoring (including `sub-blocks:` / `instances:`
for repeated-fragment authoring), deterministic layout (kernel +
Manhattan router with twelve canonical-slot rules covering the
day-one library plus the EPIC-014 RC / CC / RR / BJT / generic-IC
shapes, optional AI-placer escape hatch), multi-page rendering
with cross-page net-label glyphs, ERC against a 27-rule catalog
(S1–S7 + E1–E22, including active-device and cross-page rules),
SVG render, BOM, KiCad netlist, and Markdown ` ```circuit ` block
rewriting. Phase 7 of EPIC-006 cuts the first PyPI release of the
`circuitsmith` package; until that tag lands the install path is
the pinned-copy shape below.

## Install

Two supported shapes — both rely on the `circuitsmith` Python
package being importable. Under
[ADR-0012](../../../../docs/developers/adr/0012-library-as-installable-package.md)
the package is the unit of distribution; the skill folder is the
agent-facing surface that *consumes* it.

1. **pip + skill clone (recommended, once `0.1.0` ships).**

   ```bash
   pip install circuitsmith
   git clone <this-skill-folder> .claude/skills/circuit
   ```

   Add `circuit` to `enabled_skills` in your project's
   `.vibe/config.toml` (see [`SKILL.md`](../SKILL.md)). The Python
   package and the skill prompt are versioned independently; pin
   both.

2. **Editable / development install.** Clone the full CircuitSmith
   repo and `pip install -e .` against its `pyproject.toml`; the
   skill folder is already at `.claude/skills/circuit/`. This is
   the in-repo development path the maintainers use.

Runtime dependencies (declared in `circuitsmith`'s `pyproject.toml`,
installed automatically by `pip install circuitsmith`):

- `schemdraw >= 0.20` — schematic rendering primitives.
- `matplotlib >= 3.7` — schemdraw's drawing backend.
- `jsonschema >= 4.0` — schema validation.
- `ruamel.yaml >= 0.17` — round-trip-preserving YAML loader.

## Hello, circuit

A `.circuit.yml` description of an ESP32 with one button and one
indicator LED:

```yaml
meta:
  title: Hello circuit
  target: esp32

components:
  U1:  { type: mcu/esp32 }
  SW1: { type: passives/pushbutton, label: BTN_A }
  R1:  { type: passives/resistor,    value: 220 }
  D1:  { type: passives/led,         color: green, label: PWR_LED }

connections:
  - net: BTN_A
    path: [U1.D13, SW1.1, SW1.2, GND]
    pull: firmware

  - net: PWR_LED
    path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]

  - net: GND
    pins: [U1.GNDL, U1.GNDR]
```

Drive the full pipeline from a `/circuit` session:

> **You.** `/circuit Render the ESP32 hello-circuit above. Save the
> SVG, BOM, and netlist next to it.`
>
> **`/circuit`.** *Runs `python scripts/regenerate_circuit_artefacts.py
> --targets hello`. Reports: SVG written, ERC clean, BOM 1 row
> (220 Ω resistor × 1, green LED × 1), netlist written to
> `hello.net`.*

If you prefer the library API for one-off scripts:

```python
from circuitsmith.schema import validate

import yaml
with open("hello.circuit.yml") as f:
    circuit = yaml.safe_load(f)

findings = validate(circuit)
if findings:
    for finding in findings:
        print(f"{finding.check:7}  {finding.severity:7}  "
              f"{finding.location}: {finding.message}")
else:
    print("OK")
```

The validator catches structural errors (S4 unknown component type,
S5 unknown pin reference) before any rendering or ERC work.

## Using `/circuit` — worked invocation examples

These are illustrative interactions, drawn from the skill's behaviour
contract in [`SKILL.md`](../SKILL.md). Real five-test acceptance
transcripts replace them when
[TASK-041](../../../../docs/developers/tasks/open/task-041-run-five-acceptance-tests.md)
lands.

### Example 1 — happy path

> **You.** `/circuit Author a minimal LED blinker for an ESP32:
> one indicator LED on a free GPIO, a 220 Ω current-limit resistor,
> ground reference. Render the schematic.`
>
> **`/circuit`.** *Picks `GPIO5` (free, non-strapping). Writes
> `blinker.circuit.yml` with `U1: mcu/esp32`, `D1: passives/led`,
> `R1: passives/resistor (220 Ω)` and a `[U1.D5, R1.a, R1.b, D1.A,
> D1.K, GND]` path. Runs ERC — clean. Renders `blinker.svg`. Reports
> the BOM (1× LED, 1× 220 Ω resistor) and confirms the netlist is
> ready for KiCad import.*

### Example 2 — ERC error surfaces the catalog

> **You.** `/circuit I want to drive an LED directly from GPIO13.
> Skip the resistor.`
>
> **`/circuit`.** *Authors the YAML, runs ERC. **E2** fires (LED
> missing resistor) from the catalog — quotes the rationale
> (forward-voltage drop and Vf/Vsupply current calc) from
> [`docs/erc-checks.md`](erc-checks.md). Does **not** silently work
> around the rule. Offers two paths: insert a 220 Ω current limiter
> (E2-compliant) or document an explicit suppression with the
> per-net override syntax (rare; flags the trade-off).*

### Example 3 — add a component profile

> **You.** `/circuit Add a BME280 over I2C. Use GPIO21/22 for the
> bus.`
>
> **`/circuit`.** *Notes BME280 is missing from
> `src/circuitsmith/components/sensors/`. Writes a new profile with
> pins (`VCC`, `GND`, `SDA`, `SCL`), declared `i2c` bus role.
> Validates the profile via
> `python -m circuitsmith.knowledge.validate_catalog`. Updates the
> circuit YAML. Runs ERC — **E7** (I2C missing pull-up) fires;
> resolves by adding two 4.7 kΩ pull-ups to VCC. Reports: profile
> added, ERC clean.*

These three examples cover the three high-frequency flows: clean
authoring, ERC-driven correction, and library extension. The full
five-test acceptance script lives in TASK-041.

## Library reference

The day-one component library is documented in
[`docs/components.md`](components.md), with:

- Every profile's category, pin list, and key metadata.
- The profile-authoring workflow (when to add a profile, when to add
  a category, how the schema picks up new files automatically).
- The component-level variant-selection pattern (used by the unified
  `LED` profile with `v_forward_by_color`).

## BOM export

The BOM exporter walks a validated `.circuit.yml`'s `components`
section, groups instances by `(type, variant_key)`, and emits two
artefacts side-by-side:

- `bom.md` — Markdown table for human review (one row per group,
  reference designators run-length-encoded).
- `bom.csv` — One row per instance, columns named to satisfy KiCad's
  BOM importer (`Reference`, `Value`, `Footprint`, `Datasheet`).

The `Value` column carries the per-category variant projection
(resistor on `value`, LED on `color`, capacitor on
`value` + `dielectric`). Two 220 Ω resistors collapse to one BOM row;
a green LED and a red LED produce two rows. ADR-0004 forbids the BOM
exporter from consuming `NetGraph` — it is a counting problem, not a
topology problem.

```python
from pathlib import Path
from ruamel.yaml import YAML
from circuitsmith.export.bom_exporter import export as export_bom
from circuitsmith.schema.registry import load_profiles

yaml = YAML(typ="safe")
circuit = yaml.load(Path("hello.circuit.yml").read_text())
bom_md, bom_csv = export_bom(circuit, load_profiles())
Path("bom.md").write_text(bom_md)
Path("bom.csv").write_text(bom_csv)
```

The committed BOM artefacts at
`docs/builders/wiring/<target>/{bom.md,bom.csv}` are guarded against
drift by `scripts/check_exporters.py`, run in CI and in the
pre-commit hook.

See `docs/developers/ideas/archived/idea-001.exporters.md` §"BOM
Exporter" for the canonical row format and the per-category variant
projection.

## Netlist export

The netlist exporter is a thin projection of `NetGraph` (the shared
contract from ADR-0003) into a KiCad 7.x intermediate netlist
(`(export (version "E") ...)`). All flattening (`pins` membership,
`path` segmentation, terminal net-name merging, bus collapse)
happens inside `NetGraph` — the exporter walks `NetGraph.nets` once
and emits one `(net ...)` block per entry.

```python
from pathlib import Path
from ruamel.yaml import YAML
from circuitsmith.export.netlist_exporter import export as export_netlist
from circuitsmith.netgraph import NetGraph
from circuitsmith.schema.registry import load_profiles

yaml = YAML(typ="safe")
src = Path("hello.circuit.yml")
circuit = yaml.load(src.read_text())
graph = NetGraph.from_yaml_dict(circuit)
net_text = export_netlist(circuit, graph, load_profiles(), src)
Path("main-circuit.net").write_text(net_text)
```

Output is consumed by KiCad's "Tools → Update PCB from Netlist"
workflow — the direct bridge to PCB layout. The committed netlist
at `docs/builders/wiring/<target>/main-circuit.net` is guarded
against drift by the same `check_exporters.py` script that guards
the BOM artefacts.

A round-trip parse test
(`tests/test_netlist_exporter.py::test_round_trip_preserves_pin_memberships`)
defends the bus-collapse and segment-naming invariants — both are
the kind of bug that produces a KiCad-importable but electrically
wrong netlist.

See `docs/developers/ideas/archived/idea-001.exporters.md` §"Netlist
Exporter" for the format target, segment-naming scheme, and member
emission order.

## ERC reference

When ERC fires on a PR, [`docs/erc-checks.md`](erc-checks.md) is the
contributor-facing reference for each of the 27 check codes
(S1–S7 + E1–E22): what the trigger is, what hardware failure it
prevents, severity defaults, and how to suppress per-net /
per-component / per-circuit. Cross-references to the catalog entries
in `circuitsmith.knowledge.rules.json` carry the
Why / Senior's tip / Source content the report writer embeds.
EPIC-014 added 12 new codes — S6/S7 (sub-block validation), E11–E15
(sub-block flatten / port-net ERC), E16–E18 (active-device ERC: BJT
role, op-amp power floating, 555 pin-naming drift), E19–E22
(cross-page ERC).

## Markdown ` ```circuit ` blocks

Embed a `.circuit.yml` snippet directly inside a Markdown page; the
build pipeline renders it to an SVG and rewrites the block to an
image embed. Filenames carry an 8-char hash of the source, so a stale
embed is detected by a file-name lookup alone.

```markdown
```circuit
meta:
  title: Inline button demo
  target: esp32
components:
  U1:  { type: mcu/esp32 }
  SW1: { type: passives/pushbutton }
connections:
  - { net: BTN_A, path: [U1.D13, SW1.1, SW1.2, GND], pull: firmware }
```

```

Add `show_source` to the info string for a `<details>` wrapper that
reveals the source YAML on click:

```markdown
```circuit show_source
…
```

```

The `<details>` element renders natively on GitHub and on MkDocs —
no theme-specific extension is required.

### Build-time mechanism

The rewriter ships two execution paths and the consuming project
picks one:

- **CI workflow.** A GitHub Actions job calls
  `python -m circuitsmith.markdown <paths>` on push (rewrite blocks
  + commit the result) and `--check` on PRs (fail the job on drift).
  The CircuitSmith repo ships an example at
  `.github/workflows/generate-circuits.yml`.
- **In-process during site build.** When the consuming project uses
  MkDocs with `pymdownx.superfences`, a custom formatter calls
  `circuitsmith.markdown.compute_hash` + `render_block_to_svg` at
  site-build time. No CI rewrite needed.

The block contract (info-string flags, hash-derived filenames) is
identical across both paths.

The `find_blocks` / `compute_hash` / `format_embed` helpers in
`circuitsmith.markdown` are the shared surface — both paths consume
the same scanner. See the API in your installed package
(`python -c "from circuitsmith import markdown; help(markdown)"`).

## Portability

Under ADR-0012 the skill folder is **self-contained against the
installed `circuitsmith` package**: it does not require any sibling
file from the host project to function. Informational cross-references
elsewhere in this `docs/` directory (to ADRs, dossier files, or
host-repo CI workflows) are allowed because they are explanatory —
not load-bearing. A consumer installing only `pip install
circuitsmith` plus the skill folder can drive the full `/circuit`
workflow without those references being resolvable.

## License

[MIT](../LICENSE).
