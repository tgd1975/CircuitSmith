# Skill Packaging and Documentation

> Sub-note of [IDEA-001](idea-001-circuit-skill.md). Predecessor references
> (e.g. IDEA-011/018/019/022) resolve via the
> [Provenance anchor map](idea-001-circuit-skill.md#provenance).

## Skill Packaging

Community conventions from the Claude Code skills ecosystem, applied to this skill.

### SKILL.md frontmatter

```yaml
---
name: circuit
description: >
  Generates circuit schematics from a declarative YAML description, runs electrical
  rule checks (ERC), produces a bill of materials, exports a KiCad netlist, and
  computes deterministic schematic layouts. Use when creating or editing
  .circuit.yml files, adding components to the library, regenerating a schematic
  after a topology edit, or validating a circuit for a maker project.
allowed-tools:
  - Bash(python .claude/skills/circuit/renderer.py *)
  - Bash(python .claude/skills/circuit/erc_engine.py *)
  - Bash(python .claude/skills/circuit/bom_exporter.py *)
  - Bash(python .claude/skills/circuit/netlist_exporter.py *)
  - Bash(python .claude/skills/circuit/layout.py *)
  - Read
  - Edit
  - Write
---
```

The layout entry covers every `/circuit layout <name>` invocation — including
`--no-ai` and `--reflow` — because the glob `layout.py *` matches any argument
tail. See the script-packaging decision below for why the layout engine ships as
a single entrypoint rather than three.

`allowed-tools` pre-approves the specific Bash invocations the skill needs so the user
is not prompted on every run. The glob patterns are intentionally narrow — only the
bundled scripts at their known paths are whitelisted, not arbitrary Python execution.

The `description` front-loads the use case in the first sentence and includes trigger
keywords (`circuit`, `ERC`, `BOM`, `netlist`, `.circuit.yml`) so Claude matches it
reliably from natural-language requests.

### Dependencies

Dependencies are declared in `SKILL.md` itself — not in a `requirements.txt` — because
the skill is distributed as a directory copy, not via a package manager. The README also
lists them for installers.

```markdown
## Requirements

Python packages (install once):
    pip install schemdraw matplotlib jsonschema "ruamel.yaml>=0.17"

No other CLI tools required.
```

`ruamel.yaml` is pinned (not `pyyaml`) because the layout engine's slot-resolution
rules depend on map-insertion-order preservation — see
[yaml-format §1 loader pin](idea-001.yaml-format.md#1-yaml-loader-ruamelyaml-pinned)
and [layout-engine §5.3](idea-001.layout-engine-concept.md) / §15 (loader
requirement). `ruamel.yaml` preserves order by default; PyYAML ≥ 5.1 preserves
order only when explicitly configured and silently regresses if any caller
forgets. One pinned loader, one behaviour everywhere.

Each bundled script guards its own imports with a clear error message:

```python
try:
    import schemdraw
except ImportError:
    sys.exit("circuit skill requires schemdraw: pip install schemdraw matplotlib")
```

### Scripts execute, they do not get read into context

The skill prompt instructs Claude to **run** the bundled scripts, not read them.
Running a script keeps its implementation out of the context window — saves tokens,
guarantees consistency, and avoids Claude regenerating logic it should just delegate.

```markdown
# In SKILL.md instructions
To render a circuit:
  python .claude/skills/circuit/renderer.py --input circuit.yml --output out.svg

To run ERC:
  python .claude/skills/circuit/erc_engine.py --input circuit.yml

To generate the BOM:
  python .claude/skills/circuit/bom_exporter.py --input circuit.yml --output bom.csv

To export a KiCad netlist:
  python .claude/skills/circuit/netlist_exporter.py --input circuit.yml --output circuit.net

To compute a layout (kernel + router, deterministic):
  python .claude/skills/circuit/layout.py <name>
  python .claude/skills/circuit/layout.py <name> --reflow
  python .claude/skills/circuit/layout.py <name> --no-ai   # load-bearing in v1; accepted-but-redundant in v0.1
```

The paths are relative to the project root (resolved via `git rev-parse --show-toplevel`).
`${CLAUDE_SKILL_DIR}` does not exist as a runtime variable in Claude Code — each script
derives its own directory from `pathlib.Path(__file__).parent` when it needs to reference
sibling files (e.g. the component library or schema). The SKILL.md instructions use the
project-relative path, which works from any working directory inside the repo.

The CLI must be invoked as `python .claude/skills/circuit/<script>.py ...` from the
project root: the `allowed-tools` glob matches the literal command string, so cwd-relative
(`python renderer.py ...` after `cd`) or absolute-path forms fall outside the glob and
trigger a permission prompt on every run.

### File layout conventions

See the full skill directory tree in [Architecture](idea-001-circuit-skill.md#architecture).
Only `SKILL.md` is loaded on every invocation. All other files (`docs/*`, `components/*`,
`knowledge/*`) are read on demand when the task requires them — component authoring
consults `docs/components.md`, ERC triage consults `docs/erc-checks.md`, and so on.
This keeps the default context lean without needing a separate "lazy-loaded" directory.

`README.md` is for humans installing the skill, not for Claude. It covers:

- copy-paste installation (`cp -r .claude/skills/circuit ~/.claude/skills/`)
- pip install line
- how to register in `.vibe/config.toml` / `enabled_skills`
- quick example invocation

### Portability contract

All scripts are path-agnostic and detect the project root via
`git rev-parse --show-toplevel` rather than hardcoded paths. Two input
conventions exist:

- **`renderer.py`, `erc_engine.py`, `bom_exporter.py`, `netlist_exporter.py`**
  take explicit `--input <path>` and (where relevant) `--output <path>`.
- **`layout.py`** takes a circuit `<name>` and derives `data/<name>.circuit.yml`,
  `data/<name>.layout.yml`, and the SVG output path from the project root. This
  matches the §13 contributor workflow (`/circuit layout <name>`) — the name is
  the stable handle a contributor edits the `.circuit.yml` under, so threading
  `--input` / `--output` through would just restate it.

```python
import subprocess, pathlib

def project_root() -> pathlib.Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True
    )
    return pathlib.Path(result.stdout.strip())
```

A consumer project running the skill gets the same behaviour as this project's CI
pipeline — same scripts, different project root.

### Installation for external projects

```bash
# Copy the skill to personal skills (available in all projects)
cp -r .claude/skills/circuit ~/.claude/skills/

# Or copy to a specific project
cp -r .claude/skills/circuit /path/to/other-project/.claude/skills/

# Install Python dependencies
pip install schemdraw matplotlib jsonschema "ruamel.yaml>=0.17"

# Register (if project uses .vibe/config.toml)
# Add "circuit" to enabled_skills
# (not yet present in this repo's config — will be added when Phase 6 lands)
```

### Evaluations (acceptance tests)

Five test cases ship in `tests/` at the skill root and serve as the acceptance criterion for Phase 6:

| Case | Input | Expected |
|---|---|---|
| Happy path | Valid ESP32 `.circuit.yml` with 5 LEDs and 4 buttons | SVG rendered, ERC 0 errors, BOM correct |
| ERC error | LED with no series resistor | ERC reports ERROR, renderer exits non-zero |
| New component | "Add a BME280 sensor" | Profile written, schema validates, I2C pull-up warning emitted |
| Controller swap — RPi gotcha | "Port the ESP32 build to a Raspberry Pi and add an analog light sensor on GPIO4" | Skill surfaces HW-RPI-01 from the catalog ("no built-in ADC"), suggests MCP3008 over SPI, and refuses to wire the sensor directly to a GPIO pin |
| Incremental layout stability | Happy-path circuit; then re-run after adding a sixth LED to the existing LED column | `layout.yml` diff is one added line (new LED slot); kept components' slots are byte-identical; SVG diff is localised to the LED column. Asserts the core §8 incremental-placer guarantee. Runs unchanged on v0.1 (kernel-only) and v1 (kernel + AI): the kept-component path never touches the AI placer per §7, so the assertion holds identically in both. |

---

## Documentation

### Structure

All user-facing documentation lives inside `.claude/skills/circuit/docs/`. This is the
single source of truth — it ships with the skill and is readable on GitHub, in a cloned
repo, or via any Markdown viewer.

| File | Contents |
|---|---|
| `docs/index.md` | Overview, quick-start (install + first circuit), feature summary |
| `docs/circuit-yaml.md` | Full `.circuit.yml` format reference — all three connection forms, every key, annotated examples |
| `docs/erc-checks.md` | Per-check reference: what triggers it, what it means, severity, suppression examples |
| `docs/components.md` | Component library reference (all built-in profiles) + step-by-step guide for adding a new profile |
| `docs/layout.md` | Layout engine user guide: how to invoke `/circuit layout`, output files (`layout.yml`, `meta.yml`, SVG), rubric interpretation, kernel-failure reports, `--reflow` / `--no-ai` semantics, known limitations. Design rationale links out to [idea-001.layout-engine-concept.md](idea-001.layout-engine-concept.md) — see item 4 below. |

`README.md` at the skill root is deliberately short: install instructions, pip line, and
a link to `docs/index.md`. It is what GitHub shows on the skill's repository page.

### Makers section integration

The makers section (`docs/builders/`) links to the skill docs rather than duplicating them.
Duplication would create two sources of truth that drift apart.

**Before IDEA-022 (MkDocs):** a symlink `docs/builders/circuit/ → .claude/skills/circuit/docs/`
is created in the repo. The existing static site generator (or raw GitHub rendering) follows
the symlink. A brief prose section in the build guide (`docs/builders/wiring/`) links to
`../circuit/index.md`.

**After IDEA-022 (MkDocs):** `mkdocs.yml` maps the skill docs into the nav directly:

```yaml
nav:
  - Builders:
    - Wiring: builders/wiring/index.md
    - Circuit reference: '!import .claude/skills/circuit/docs/'
```

MkDocs resolves the import at build time; the docs appear under the builders section with no
copy or symlink needed. If the `!import` plugin is unavailable, the fallback is an explicit
nav entry per file — still one source of truth, just enumerated. Either way, the skill docs
directory is never duplicated.

### What is documented in Phase 1

`LICENSE`, `CHANGELOG.md`, and a skeleton `docs/index.md` (overview + install) are written
in Phase 1 alongside the component library. The remaining `docs/` files are written in the
phase where their subject is implemented:

| Phase | Doc deliverable |
|---|---|
| 1 | `LICENSE`, `CHANGELOG.md`, `docs/index.md` (skeleton), `docs/components.md` (initial library reference + how-to-add-a-profile guide) |
| 2 | `docs/circuit-yaml.md`, `docs/layout.md` (authored fresh inside the skill — see ownership note below) |
| 3 | `docs/erc-checks.md` |
| 4–6 | Updates to existing files as features land |
| 7 | `README.md` finalised for standalone repo; `docs/index.md` updated with standalone install path |

---

## Packaging decisions for the layout engine

The six items below resolve the packaging deltas introduced by the layout
engine concept and the v0.1/v1 staging split
([idea-001.layout-engine-concept.md §17.1](idea-001.layout-engine-concept.md)).
They are settled and feed directly into Phase 2 implementation.

### 1. Layout entrypoint script name

The layout engine ships as **`layout.py`** at the skill root, exposed as
`/circuit layout <name>` per
[§13 contributor workflow](idea-001.layout-engine-concept.md). Argument parsing
covers `<name>`, `--reflow`, and `--no-ai`. The `allowed-tools` glob
`Bash(python .claude/skills/circuit/layout.py *)` pre-approves every form.

Rejected names: `layout_kernel.py` over-specifies the internal structure
(kernel vs. router vs. placer is an implementation detail); `placer.py` is
misleading in v0.1 where the AI placer is absent.

### 2. Script packaging — one binary, internal modules

The layout engine ships as **one entrypoint** (`layout.py`) that imports three
internal modules:

```text
.claude/skills/circuit/
├── layout.py              # CLI entrypoint — argument parsing + orchestration
└── layout_engine/
    ├── __init__.py
    ├── kernel.py          # deterministic placer (§5)
    ├── router.py          # Manhattan router (§9)
    └── ai_placer.py       # v1 only; absent in v0.1 (see item 5)
```

The package is named `layout_engine/`, not `layout/`, on purpose: a sibling
file and package sharing the stem `layout` creates import ambiguity in Python
depending on how the CLI is launched (`python layout.py` vs `python -m
circuit.layout`). Concretely, if `layout.py` and `layout/` coexist, `import
layout` resolves to whichever entry appears first on `sys.path` and that
ordering differs between direct invocation and `-m`, producing behaviour that
varies with the launch form. Keeping the stems distinct sidesteps the problem
entirely.

Rationale for a single CLI: the three responsibilities share inputs (topology,
layout.yml, rubric state) and the orchestration order is fixed by §5.
Splitting into three CLIs forces the caller — Claude, CI, or the acceptance
harness — to re-derive that order and serialise intermediate state to disk. A
single entrypoint keeps the §5 pipeline internal and gives `allowed-tools` one
glob to pre-approve.

Sub-commands (`layout.py kernel`, `layout.py router`) are not exposed: the
contract in §13 is a single `/circuit layout <name>` invocation, and the
acceptance harness drives that same surface.

The [Architecture tree in idea-001-circuit-skill.md](idea-001-circuit-skill.md#architecture)
is kept in sync: it lists `layout.py` and the `layout_engine/` package, marks
`ai_placer.py` as v1-only, and uses the settled `docs/layout.md` scope.

### 3. Incremental-stability acceptance case

Added to the table above as the fifth case. It exercises the §8 incremental
placer guarantee directly: adding one component to a shipped circuit must
produce a one-line `layout.yml` diff and a localised SVG diff, with kept
components' slots byte-identical. Without this case, the acceptance gate does
not test the property the engine is built around.

### 4. `docs/layout.md` ownership

`docs/layout.md` is **authored fresh inside the skill** as user-facing
reference documentation: how to invoke `/circuit layout`, what the output
files mean, how to read a rubric, how to handle kernel-failure reports.
Audience: skill users (human builders and Claude).

[idea-001.layout-engine-concept.md](idea-001.layout-engine-concept.md)
stays in `docs/developers/ideas/` as the **design record**. It is archived
under `docs/developers/ideas/archived/` at the moment the skill goes 1.0.
Audience: maintainers reasoning about why the engine is shaped the way it is.

The two documents do not fold into each other. The concept doc is written for
a reader who wants to change the engine; `docs/layout.md` is written for a
reader who wants to use it. Cross-linking is one-directional: `docs/layout.md`
links back to the concept doc under a "Design rationale" footer, not vice
versa.

### 5. v0.1 vs v1 packaging — AI genuinely absent

v0.1 ships with `layout_engine/ai_placer.py` **genuinely absent** from disk.
The `--no-ai` flag is accepted by `layout.py` but is redundant in v0.1 —
kernel-only is already the only mode — so it is effectively a no-op. The flag
is parsed rather than rejected so that scripts and docs written against v1 do
not break when run against v0.1. When `--no-ai` is passed in v0.1, `layout.py`
prints a one-line notice (`note: --no-ai is a no-op in v0.1 (kernel-only)`) so
contributors reading logs do not assume the flag had any effect.

Kernel ambiguity / overflow in v0.1 follows the §7.3 failure-mode path
directly — a non-zero exit and a human-readable report naming the unplaced
components — which is also the mechanism that accumulates the calibration
corpus referenced in §17.1. v1 intercepts the same branch and dispatches to
`ai_placer.py` before falling through to §7.3.

The v0.1 → v1 transition is a follow-up packaging PR that (a) adds
`layout_engine/ai_placer.py`, (b) wires it into the kernel-ambiguity branch
per §7, and (c) makes `--no-ai` a load-bearing flag (skip AI, force §7.3 on
ambiguity) rather than a no-op. `SKILL.md` frontmatter does not change — the
existing `layout.py *` glob already covers both versions.

Rejected alternatives: shipping v0.1 with AI hooks stubbed out leaves dead
code in the tree and confuses readers; gating on a runtime flag requires a
config surface we do not otherwise need.

### 6. Loader dependency pin

Resolved in `Requirements` above: `ruamel.yaml >= 0.17`. The pin is load-bearing
the moment layout ships because §5.3 slot resolution and any future
first-declared-wins rule depend on map-insertion-order preservation. See
the loader-library item in [yaml-format pending discussion](idea-001.yaml-format.md)
for the PyYAML-vs-ruamel comparison, and
[layout-engine §15](idea-001.layout-engine-concept.md) for the loader
requirement statement.

A schema-level test asserting `load → dump → load` preserves order lives in
the skill's `tests/` directory alongside the acceptance cases, not in the
host unit-test tree — it tests the skill's dependency contract, not the
pedal firmware.

---
