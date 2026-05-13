# circuit — schematic generation from declarative YAML

`circuit` is a Claude Code skill that takes a declarative
`.circuit.yml` description (components + connections), validates it
against the rule catalog, and emits a documentation-quality SVG
schematic, a BOM, and a KiCad-compatible netlist.

This page is the install + first-circuit walkthrough. For the format
itself, see [`docs/components.md`](components.md) and (when it lands
in EPIC-002) `docs/circuit-yaml.md`. The dossier behind the design
lives in `docs/developers/ideas/archived/idea-001*.md` in the host
project; it is not duplicated here.

## Status

Phase 1 of the dossier roadmap: **component library + schema only**.
The YAML-driven renderer, ERC engine, BOM / netlist exporters, and
Markdown integration ship in EPIC-002..006. The skill is usable
today for profile authoring and schema validation; the full
`/circuit` workflow is not yet wired up.

## Install

Two supported shapes:

1. **Pinned copy inside a host project.** Clone this skill directory
   into `.claude/skills/circuit/` of the consuming repo and pin to a
   tag. This is how the host project currently ships it. The
   directory is fully self-contained — `LICENSE`, `CHANGELOG.md`,
   `components/`, `schema/`, `docs/` — and is designed for this
   drop-in use per the portability contract
   (`idea-001.skill-packaging.md`).

2. **Standalone repository.** Once EPIC-006 lands, the skill is also
   published as its own repo (the "skill extraction" task). At that
   point the install instruction becomes a one-liner clone + symlink;
   this page will be updated then.

Runtime dependencies (declared in the host's `pyproject.toml`):

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

In Phase 1 you can validate this file today:

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
S5 unknown pin reference) before any rendering or ERC work. From
EPIC-002 onward the renderer turns the same file into an SVG.

## Library reference

The day-one component library is documented in
[`docs/components.md`](components.md), with:

- Every profile's category, pin list, and key metadata.
- The profile-authoring workflow (when to add a profile, when to add
  a category, how the schema picks up new files automatically).
- The component-level variant-selection pattern (used by the unified
  `LED` profile with `v_forward_by_color`).

## License

[MIT](../LICENSE).
