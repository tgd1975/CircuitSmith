# CircuitSmith

> *CircuitSmith forges schematics. [PartsLedger](https://github.com/tgd1975/PartsLedger) keeps the record CircuitSmith reads.*

CircuitSmith turns a declarative `.circuit.yml` into a documentation-quality
schematic — running electrical-rule checks and emitting a bill of materials
and a KiCad-compatible netlist along the way. You describe the circuit in YAML
(or in natural language to the Claude Code skill, which writes the YAML for
you); a deterministic pipeline does the rest. It ships as the
[`circuitsmith`](https://pypi.org/project/circuitsmith/) Python package
(v0.1.0).

## See it first

- **[Tutorial](docs/users/tutorial/)** — a ~30-minute walk from a
  one-resistor circuit to a BOM round-trip. Start here.
- **[Example gallery](docs/users/examples/)** — finished circuits (voltage
  divider, common-emitter amplifier, 555 monostable, op-amp buffer,
  multi-page split) you can read cold.

## What it produces

From a single `.circuit.yml`:

| Artifact | Purpose |
|---|---|
| `*.svg` | The schematic, rendered via Schemdraw. |
| `erc-report.md` | Electrical-rule-check findings, with rationale + source links. |
| `bom.md` / `bom.csv` | Bill of materials. |
| `*.net` | KiCad-compatible netlist. |
| `meta.yml` | Layout provenance + readability-rubric scores. |

## How it works

```text
.circuit.yml
  → schema validation     (rejects unknown components / pins)
  → ERC                    (structural S1–S7 + electrical E1–E22)
  → layout kernel          (canonical-slot placement)
  → Manhattan router       (wire geometry)
  → Schemdraw render       (SVG)
  → rubric + meta.yml      (readability scoring + provenance)
```

ERC runs **strictly pre-layout** — a malformed circuit never reaches the
router. The module boundaries and the decisions behind them are in
[`docs/developers/ARCHITECTURE.md`](docs/developers/ARCHITECTURE.md).

## Install

```bash
pip install circuitsmith        # the Python library (requires Python ≥ 3.11)
```

For natural-language authoring, the Claude Code skill lives at
[`.claude/skills/circuit/`](.claude/skills/circuit/) and delegates to the same
package — so the skill path and the library path render identical output.

## Documentation

| Audience | Where |
|---|---|
| **Users** — tutorial + example gallery | [`docs/users/`](docs/users/) |
| **Builders** — per-target wiring artefacts (BOM, netlist, SVG) | [`docs/builders/`](docs/builders/) |
| **Contributors** — architecture, ADRs, task system, testing, CI | [`docs/developers/`](docs/developers/) |

New contributors start at [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Status

v0.1.0 ships the full pipeline — component library + schema, the NetGraph,
ERC (27 checks), the deterministic layout kernel + Manhattan router, the
Schemdraw renderer, and the BOM / netlist exporters — plus the Claude Code
skill and PyPI packaging. A later cycle (EPIC-014) added first-class
sub-blocks, non-LED kernel rules, active-device profiles (BJT, op-amp, 555),
and a multi-page renderer.

The live work breakdown is in
[`docs/developers/tasks/EPICS.md`](docs/developers/tasks/EPICS.md); the
release history is in [`CHANGELOG.md`](CHANGELOG.md). The original pre-build
design dossier — annotated with what shipped — is archived at
[`idea-001-circuit-skill.md`](docs/developers/ideas/archived/idea-001-circuit-skill.md).

## Explicit non-goals

- Audio signal conditioning (no analog path in the current target).
- Title block / branding overlay inside the SVG.
- PNG conversion as a dedicated pipeline step.
- General-purpose auto-layout (force-directed, hierarchical, etc.).
- An in-repo electronics textbook — the rule catalog links out for theory.
- **Runtime LLM generation of hardware rules.** The catalog is authoritative;
  the LLM only helps author the YAML.

## Related projects

| Project | Relationship |
|---|---|
| [PartsLedger](https://github.com/tgd1975/PartsLedger) | Parts inventory; CircuitSmith reads from it. |
| [AwesomeStudioPedal — IDEA-027](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-027-circuit-skill.md) | The spiritual predecessor CircuitSmith generalises. |

## License

[MIT](LICENSE).
