# CircuitSmith

> *CircuitSmith forges schematics. [PartsLedger](https://github.com/tgd1975/PartsLedger) keeps the record CircuitSmith reads.*

**⚠️ Concept stage.** Everything below describes the *target* state of the
project. None of the pipeline, skill, or component library exists yet — they
are work items in [EPIC-001..006](docs/developers/tasks/EPICS.md). Phase 0
(EPIC-007) bootstraps the Python project config; Phase 1 (EPIC-001) produces
the first component profile. Read this README as a design preview, not a
manual.

CircuitSmith generates **circuit schematics from declarative YAML**, validates
them against electrical rules, and exports both a bill of materials and a
KiCad-compatible netlist — all driven by a Claude Code skill so that
contributors describe what they want in natural language rather than writing
Schemdraw code.

**Status:** concept stage. The full design dossier was copied from
[AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal)'s IDEA-027
companion files, archived on conversion to EPIC-001..006, and now lives in
[docs/developers/ideas/archived/idea-001-circuit-skill.md](docs/developers/ideas/archived/idea-001-circuit-skill.md).
Predecessor artefacts the dossier references —
[`scripts/generate-schematic.py`](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/scripts/generate-schematic.py),
[`data/config.json`](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/data/config.json),
[`docs/builders/wiring/`](https://github.com/tgd1975/AwesomeStudioPedal/tree/main/docs/builders/wiring) —
live in that repo, not here. Implementation has not started.

## Why

The project this skill grew out of generates schematics from hand-authored
Python (Schemdraw). Adding a sensor means knowing Schemdraw's API. There is
no validation that the drawn circuit is electrically safe, no
machine-readable component list, and no path from the diagram to PCB tools.

CircuitSmith answers four questions the current pipeline cannot:

- How does a contributor add a sensor without learning Schemdraw or electronics?
- How does a reviewer know the circuit is electrically sound without reading code?
- Where does the shopping list come from?
- How does the schematic feed a PCB tool when [IDEA-011](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-011-pcb-board-design.md) starts?

## What it produces

A single `.circuit.yml` is the source of truth. The pipeline emits:

| Artifact | Purpose |
|---|---|
| `main-circuit.svg` | Schematic, rendered via Schemdraw |
| `erc-report.md` | Electrical rule check findings, with rationale + source links |
| `bom.md` / `bom.csv` | Bill of materials |
| `main-circuit.net` | KiCad-compatible netlist |
| `meta.yml` | Layout provenance + readability rubric scores |

## Pipeline

```text
.circuit.yml
  → schema validation        (rejects unknown components / pins)
  → ERC                       (structural S1–S3 + electrical E1–E10)
  → layout kernel             (canonical-slot placement)
  → Manhattan router          (wire geometry)
  → Schemdraw render          (SVG emission)
  → rubric + meta.yml         (readability scoring + sidecar)
```

ERC runs **strictly pre-layout**: a malformed circuit never reaches the router.

## Architecture

> **Status:** the `.claude/skills/circuit/` tree below describes the
> *target* layout. None of it exists yet — Phase 1 (EPIC-001) scaffolds it.
> Today the repo holds only the design dossier and the task-system infra.

Everything ships inside `.claude/skills/circuit/` — a self-contained,
path-agnostic Claude Code skill. The same directory is the library that
the CI script imports, so there is no duplication between "the skill" and
"the project's generator".

```
.claude/skills/circuit/
├── SKILL.md             ← skill prompt + invocation spec
├── renderer.py          ← YAML → Schemdraw → SVG
├── netgraph.py          ← shared typed net graph
├── erc_engine.py        ← hardware linter (ERC)
├── bom_exporter.py      ← components → Markdown/CSV
├── netlist_exporter.py  ← net graph → KiCad .net
├── layout.py            ← CLI for /circuit layout
├── layout_engine/       ← kernel, router (+ AI placer in v1)
├── schema/              ← circuit + layout JSON schemas
├── components/          ← MCUs, passives, connectors, sensors
├── knowledge/           ← curated rule catalog (rules.json)
└── docs/                ← skill-level user docs
```

Key decoupling: `bom_exporter.py` walks `components` directly;
`netlist_exporter.py` walks `NetGraph`. They never reach into each other.

## Skill behaviour

The skill instructs Claude to act as an electronics engineer who:

1. Resolves all component types from `components/` — never invents pin names.
2. Writes and edits **YAML, not Python**.
3. Enforces layout conventions (signal left → right, VCC top, GND bottom).
4. Applies best practices grounded in the [rule catalog](docs/developers/ideas/archived/idea-001.rule-catalog.md) — every default traces back to a `source_of_truth` link; no free-form runtime generation of hardware rules.
5. Batches ambiguous-pin questions into a single message rather than looping.
6. Runs ERC before declaring a circuit done.
7. Can add new component profiles and reports which ERC checks they activate.

## Phase plan

```
Phase 0   Project bootstrap (pyproject.toml, pytest config, CI workflow)
Phase 1   Component library + schema
Phase 2a  Renderer + v0.1 deterministic kernel + cutover from legacy generator
Phase 2b  AI placer (contingent on observed kernel-failure modes)
Phase 3   ERC engine + rule catalog
Phase 4   BOM + netlist exporters
Phase 5   Markdown ``` ```circuit ``` ``` integration
Phase 6   The Claude Code skill itself
Phase 7   Extract `.claude/skills/circuit/` into a standalone repo
```

Phase 0 (EPIC-007) is a hard prerequisite of Phase 1 — the prose-only
dependency declaration in the skill-packaging dossier becomes
machine-readable, the test runner gets configured, and CI gets a workflow,
all before EPIC-001 produces real Python code. Phases 1–7 then follow the
staging described above.

Phase 2b is gated on real failure data, not a calendar — the v0.1 kernel
ships first and stays in production until concrete escalations justify the
AI placer. See the [phase plan](docs/developers/ideas/archived/idea-001-circuit-skill.md#phase-plan)
for prerequisites and acceptance criteria.

## Deep-dive docs

Each module has its own companion specification:

| Companion | Covers |
|---|---|
| [Skill packaging](docs/developers/ideas/archived/idea-001.skill-packaging.md) | SKILL.md frontmatter, dependencies, layout, install paths, acceptance tests |
| [YAML format](docs/developers/ideas/archived/idea-001.yaml-format.md) | `pins` / `path` / `bus` connection forms, schema validation |
| [Layout engine](docs/developers/ideas/archived/idea-001.layout-engine-concept.md) | Slot vocabulary, kernel, incremental placer, rubric, sidecar, CI contract |
| [ERC engine](docs/developers/ideas/archived/idea-001.erc-engine.md) | Three-level config, structural + electrical checks, report format |
| [Rule catalog](docs/developers/ideas/archived/idea-001.rule-catalog.md) | Format, licensing, 30–50-rule scope, authoring workflow |
| [Components](docs/developers/ideas/archived/idea-001.components.md) | Profile format, pin aliasing, adding a component |
| [Exporters](docs/developers/ideas/archived/idea-001.exporters.md) | BOM markdown/CSV, KiCad `.net` flattening rules |

## Related projects

| Project | Relationship |
|---|---|
| [PartsLedger](https://github.com/tgd1975/PartsLedger) | Parts inventory; CircuitSmith reads from it |
| [AwesomeStudioPedal — `IDEA-027`](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-027-circuit-skill.md) | Spiritual predecessor; CircuitSmith generalises that idea |
| [IDEA-011 (PCB design)](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-011-pcb-board-design.md) | Consumes CircuitSmith's `.net` file as the KiCad seed |
| [IDEA-022 (MkDocs site)](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-022-mkdocs-documentation-site.md) | Renders ``` ```circuit ``` ``` blocks via `pymdownx.superfences` |

## Explicit non-goals

- Audio signal conditioning (no analog path in the current target).
- Title block / branding overlay inside the SVG.
- PNG conversion as a dedicated pipeline step.
- General-purpose auto-layout (force-directed, hierarchical, etc.).
- An in-repo electronics textbook — the rule catalog links out for theory.
- **Runtime LLM generation of hardware rules.** The catalog is authoritative;
  the LLM is only used to understand the maker's natural-language request.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the first-time-setup steps —
in particular `bash scripts/install_git_hooks.sh` to install the
pre-commit wrapper and the security-review hooks
(`pre-merge-commit`, `post-merge`, `pre-rebase`) that scan incoming
changes from pulls/merges/rebases.

## License

MIT (planned, alongside the standalone-skill repo in Phase 7).
