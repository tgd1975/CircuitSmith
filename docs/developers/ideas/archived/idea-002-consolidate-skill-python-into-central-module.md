---
id: IDEA-002
title: Consolidate skill-resident Python into a central module
description: Consolidate skill-resident Python into one auditable module
category: 🛠️ tooling
---

## Archive Reason

2026-05-13 — Elevated to EPIC-010.

## Motivation

The Python implementation of the circuit skill is currently distributed
across `.claude/skills/circuit/**/*.py` — `netgraph.py`, the new
`layout_engine/kernel.py`, the schema validators, the ERC engine, etc.
Each skill folder owns its own slice of code, and there is no single
place to read the project from end-to-end.

The user reports this as actively painful and wants it addressed
**before starting EPIC-003** (EPIC-002 proceeds on the current layout):
"no oversight possible … i am lost". The problem will get worse as the
renderer/layout/export stack grows — every subsequent epic adds more
modules that would otherwise land inside skill folders.

## Reframe

The Python code already forms a coherent package today. Imports across
the codebase use `from circuit.netgraph import …`,
`from circuit.layout_engine import …`, `from circuit.schema import …`,
and [`tests/conftest.py`](../../../../tests/conftest.py) splices
`.claude/skills/` onto `sys.path` so the skill folder is importable as
`circuit`. There is **one package** already — it is just called
`circuit` and lives buried inside `.claude/skills/`, which makes it
feel like skill-config rather than first-class code.

The work this idea proposes is therefore **rename + relocate**, not
"consolidate scattered code":

- `circuit` → `circuitsmith` (the package name the repo has been
  reserving in [pyproject.toml](../../../../pyproject.toml) all along).
- `.claude/skills/circuit/` → `src/circuitsmith/`.

Naming the work accurately matters because it tells us what is
mechanical (the rename) and what is not (the ADR-0007 reckoning —
see below).

## Decisions (2026-05-12)

The open questions below have been resolved with the user; the
preferred shape is fixed.

- **Package name.** `circuitsmith`. PyPI returns 404 for
  `pypi.org/pypi/circuitsmith/json` (name is available), and
  [pyproject.toml](../../../../pyproject.toml) already reserves it
  internally — the file explicitly notes "No importable Python
  package yet" pending exactly this work.
- **Layout.** **Src layout** — `src/circuitsmith/...`. Avoids the
  "tests accidentally import the working copy" footgun; modern
  Python default.
- **Skill shim convention.** Start with the **simpler** option:
  skills do `from circuitsmith.foo import …`. Keep the CLI entry
  point (`python -m circuitsmith.foo …`) as a future option if a
  Bash-only or prompt-only skill ever needs to call in without a
  Python interpreter handle.
- **Migration sequencing.** **Big-bang.** One branch, move
  everything, land it before EPIC-003 opens.
- **Code ownership.** The `co-netgraph` / `co-erc-engine`
  code-owner reminder skills stay valid — the module file names
  carry over (`netgraph.py`, `erc_engine.py`), so the reminders
  only need their path targets updated from `.claude/skills/circuit/…`
  to `src/circuitsmith/…`.
- **Delivery packaging.** Two artefacts: the Python package
  (`circuitsmith`) and the skill files (`.claude/skills/**`).
  Skills consume the package; the package does not know about
  skills. No third "loose lib/" surface.
- **Per-skill packages.** Rejected — too complicated. One
  package, many skills.

## Proposed module layout

```text
src/circuitsmith/
├── __init__.py                # version, top-level re-exports
├── netgraph.py                # was .claude/skills/circuit/netgraph.py
├── erc_engine.py              # planned (co-erc-engine reminder targets this)
├── components/
│   ├── __init__.py
│   ├── connectors.py
│   ├── mcus.py
│   ├── passives.py
│   └── sensors.py
├── schema/
│   ├── __init__.py
│   ├── registry.py
│   ├── validator.py           # circuit-schema validation
│   ├── layout_validator.py
│   ├── circuit.schema.json    # co-located with validators (today's shape)
│   └── layout.schema.json
├── layout/
│   ├── __init__.py
│   ├── kernel.py
│   ├── router.py
│   └── rubric.py
├── render/                    # schemdraw rendering (EPIC-002 lands here)
│   └── __init__.py
└── export/                    # BOM, KiCad netlist (later epics)
    └── __init__.py

tests/                         # already exists at repo root
├── conftest.py
├── test_netgraph.py
├── test_kernel.py
├── test_router.py
├── test_rubric.py
├── test_layout_schema.py
├── test_schema_validation.py
├── test_components.py
└── test_generator_byte_identity.py

.claude/skills/circuit/        # skill tree shrinks to shims + agent prompts
├── SKILL.md                   # agent-facing prompt; unchanged in spirit
├── render.py                  # thin shim: from circuitsmith.render import …
├── validate.py                # thin shim: from circuitsmith.schema import …
└── …                          # one shim per agent-callable surface
```

Notes on the layout:

- **File names preserved.** `netgraph.py`, `kernel.py`,
  `router.py`, etc. keep their current names so `git mv` is the
  bulk of the diff and the code-owner reminder skills only need
  their path targets updated.
- **JSON Schemas stay co-located with their validators.** No
  `data/` subdirectory — the schemas already live next to
  `validator.py` and `layout_validator.py` today and the
  validators read them with `Path(__file__).parent / "...json"`,
  which keeps working unchanged. `pyproject.toml` only needs a
  `package-data` entry so the `.json` files ship inside the wheel:

  ```toml
  [tool.setuptools.package-data]
  "circuitsmith.schema" = ["*.json"]
  ```

- **`render/` and `export/` are placeholders.** Created empty as
  part of the refactor so EPIC-002 (render) and the later
  BOM/netlist epics open against an existing namespace instead
  of having to invent one.
- **`erc_engine.py` is a *planned* slot, not a file the refactor
  creates.** Listed here so the target architecture is legible
  end-to-end; the file itself lands when the ERC epic begins. The
  [`co-erc-engine`](../../../../.claude/skills/co-erc-engine/)
  reminder skill already points at this name and only needs its
  path target updated when the refactor lands.
- **`pyproject.toml` flips.** [pyproject.toml:62-63](../../../../pyproject.toml#L62-L63)
  currently has `[tool.setuptools] py-modules = []` to stop
  setuptools from guessing. The refactor replaces that with a
  src-layout discovery block plus the `package-data` entry above:

  ```toml
  [tool.setuptools.packages.find]
  where = ["src"]
  ```

- **`tests/conftest.py` becomes a deletion, not an edit.** Once
  `pip install -e .` lands the src-layout, the `sys.path` splice
  at [conftest.py:14-16](../../../../tests/conftest.py#L14-L16)
  is obsolete and should be removed rather than retargeted.

## ADR-0007 reckoning

ADR-0007 currently encodes the delivery contract that
[`tests/conftest.py:4`](../../../../tests/conftest.py#L4) repeats
verbatim — *"The skill directory is the library"*. That is, the
deliverable to a consuming repo is the skill folder itself. The
contract is surfaced as an invariant in
[`.claude/skills/circuit/netgraph.py:23`](../../../../.claude/skills/circuit/netgraph.py#L23)
(*"No host-project imports (ADR-0007 portability)"*) and enforced
on every commit by
[`scripts/portability_lint.py`](../../../../scripts/portability_lint.py)
via the pre-commit hook at
[`scripts/pre-commit:155-163`](../../../../scripts/pre-commit#L155-L163).

The refactor changes the **delivery shape**, not the **portability
spirit**. A new ADR (working title: ADR-0012, *"Library as installable
package"*) supersedes ADR-0007 and records:

- **New delivery model.** A consuming repo installs `circuitsmith`
  as an additional Python dependency (PyPI or git URL) and copies
  `.claude/skills/circuit/` for the agent-facing prompts and shims.
  Two artefacts, one additional dependency — no contradiction with
  the existing portability goal, just a cleaner split between
  "agent contract" and "library code".
- **Invariant survives.** The no-host-project-imports rule is *kept*
  for the package interior — `circuitsmith.*` modules must remain
  free of consuming-repo coupling. The `co-netgraph` invariant
  comment moves with the file.
- **Lint retargets.** `scripts/portability_lint.py` and the
  pre-commit hook at `scripts/pre-commit:155-163` retarget from
  `.claude/skills/circuit/` to `src/circuitsmith/`. The rule set
  itself is unchanged.
- **`tests/conftest.py` docstring updates.** The reference to
  ADR-0007 changes to the superseding ADR, but the file itself is
  deleted (see notes above on the editable install).

Writing this ADR is the **first task** of the resulting EPIC and the
only step that is not mechanical. The rename + relocate work that
follows depends on the new delivery contract being on paper.

## Alternatives considered

- **Leave it as-is.** Rejected — user has explicitly flagged the
  current shape as untenable.
- **One big `lib/` folder of loose modules (no package).**
  Rejected by the user: delivery packaging should be skill files
  *and* a Python package, not loose modules.
- **Per-skill packages.** Rejected by the user as too complicated.

## Suggested next step

Convert this idea into a new EPIC (next free ID) that gates
EPIC-003. The detailed execution plan is in the next section.

## Execution plan

The work is a single feature branch
`refactor/circuitsmith-package`, landing as one squash commit on
`main` per [CLAUDE.md § Branch merges](../../../../CLAUDE.md). The
branch carries ~5 internal commits for reviewability; they squash
on merge.

There is exactly one stop-line in the EPIC, at the end of Phase 1.
Phase 2 onward is mechanical.

### Phase 0 — Preconditions

- **0.1** Branch from `main`:
  `git checkout -b refactor/circuitsmith-package`.
- **0.2** Capture green baseline. `pytest` and
  `python scripts/portability_lint.py` both pass *before* any code
  moves. Record the SHA so deviations are attributable.
- **0.3** Inventory the rewrite surface. Save the output of:
  - `rg -n "from circuit\." -t py`
  - `rg -n "import circuit$|import circuit\." -t py`
  - `rg -n "\.claude/skills/circuit/" -t py -t md -t toml -t sh`

  These three lists are the rewrite target set for Phase 2.

### Phase 1 — ADR-0012 supersedes ADR-0007

The only non-mechanical phase. No code changes.

- **1.1** Write
  `docs/developers/adr/0012-library-as-installable-package.md`
  from the
  [template](../../../../docs/developers/adr/0000-template.md).
  Status: Accepted, supersedes ADR-0007. Decision: the library is
  `pip install circuitsmith`; the skill folder ships agent-facing
  prompts (and optional thin shims) only. The
  no-host-project-imports invariant survives, now scoped to
  `circuitsmith/*` rather than `.claude/skills/circuit/`.
- **1.2** Mark
  [ADR-0007](../../../../docs/developers/adr/0007-skill-directory-is-the-library.md)
  status `Superseded by ADR-0012`. Add a `## Supersession`
  section forward-linking to ADR-0012. Do not delete — ADR
  provenance matters.
- **1.3** Reckon with **EPIC-006**. ADR-0007 was the foundation
  [EPIC-006 (`Circuit Skill — Skill Packaging and Standalone
  Extraction`)](../../../../docs/developers/tasks/open/epic-006-circuit-skill-packaging.md)
  stood on: its Phase 7 plan was `cp -r .claude/skills/circuit
  /elsewhere/`. With ADR-0012, the extraction path is "publish the
  package to PyPI", a different shape.

  **Rewrite EPIC-006 in place** rather than retiring it — the
  epic's name and intent ("ship the library so other projects can
  use it without depending on CircuitSmith") still apply, only the
  *mechanism* changes from folder-copy to package-publish. The
  rewrite:
  - Replaces the Phase 7 body with the PyPI publication path:
    write `RELEASING.md`, configure `python -m build`, set up
    trusted publishing (or token-based as a fallback), publish
    `0.1.0` as the first real release. The standalone-skill-repo
    extraction goes away — under ADR-0012 the skill folder stays
    in this repo as the agent-facing surface; only the library
    leaves.
  - Adds a new task `TASK-NNN (publish-circuitsmith-to-pypi)`
    covering the actual publication mechanics, scoped to land
    after this refactor's squash-merge.
  - Drops the Phase 6 → Phase 7 prerequisite chain inherited from
    ADR-0007 (use-the-skill-in-anger-before-extracting); under
    ADR-0012 publication is decoupled from real-circuit usage,
    though "first publish a `0.1.0` rather than `0.1.0.dev0`" is
    still gated on the skill being used at least once.

  `TASK-045 (replace-skill-dir-with-pinned-copy)` retires —
  pinned folder copies are obsolete under ADR-0012.
- **1.4** Update [TASK-050](../../../../docs/developers/tasks/open/task-050-boundary-import-contract-test.md)
  scope: the "boundary" is now `src/circuitsmith/`, not
  `.claude/skills/circuit/`. The contract itself is unchanged.

**Stop-line.** User signs off on ADR-0012 + the EPIC-006 decision
before Phase 2. Everything downstream depends on the paper trail
being settled.

### Phase 2 — Atomic relocation

One branch commit. Splitting this across multiple commits leaves
intermediate states where the pre-commit hook points at a moved
path; doing it atomically avoids that.

- **2.1 Tree move.** Each `git mv` preserves blame.
  - `git mv .claude/skills/circuit/netgraph.py src/circuitsmith/netgraph.py`
  - `git mv .claude/skills/circuit/renderer.py src/circuitsmith/renderer.py`
  - `git mv .claude/skills/circuit/components src/circuitsmith/components`
  - `git mv .claude/skills/circuit/schema src/circuitsmith/schema`
  - `git mv .claude/skills/circuit/layout_engine src/circuitsmith/layout`
    (directory rename — `_engine` suffix made sense inside a
    skill folder, not as a top-level package surface).
- **2.2 Package skeleton.** Create:
  - `src/circuitsmith/__init__.py` with `__version__ = "0.1.0.dev0"`
    mirrored from `pyproject.toml`.
  - `src/circuitsmith/render/__init__.py` (empty placeholder for
    EPIC-002 rendering work).
  - `src/circuitsmith/export/__init__.py` (empty placeholder for
    BOM / netlist).
  - What stays in `.claude/skills/circuit/`: `SKILL.md` and `docs/`.
    Shim `.py` files are deferred to Phase 3.
- **2.3 Import rewrites** across all `*.py` in `src/` and `tests/`.
  Find-replace, in this order (longer first to avoid partial
  matches):
  - `from circuit.layout_engine.` → `from circuitsmith.layout.`
  - `from circuit.layout_engine import` → `from circuitsmith.layout import`
  - `from circuit.netgraph` → `from circuitsmith.netgraph`
  - `from circuit.schema` → `from circuitsmith.schema`
  - `from circuit.components` → `from circuitsmith.components`
  - `from circuit.renderer` → `from circuitsmith.renderer`
  - `import circuit.` → `import circuitsmith.`
- **2.4 Docstring path references** in:
  - [schema/registry.py:3,50](../../../../.claude/skills/circuit/schema/registry.py#L3)
  - [schema/validator.py:46](../../../../.claude/skills/circuit/schema/validator.py#L46)
  - [schema/**init**.py:10](../../../../.claude/skills/circuit/schema/__init__.py#L10)
  - [netgraph.py:18,23](../../../../.claude/skills/circuit/netgraph.py#L18)
    (ADR-0007 reference → ADR-0012)
  - [layout_engine/**init**.py:15](../../../../.claude/skills/circuit/layout_engine/__init__.py#L15)
    (ADR-0001 reference unchanged; verify no others)
- **2.5 `pyproject.toml` flip.**
  - Remove [pyproject.toml:62-63](../../../../pyproject.toml#L62-L63)
    (`[tool.setuptools] py-modules = []`).
  - Add `[tool.setuptools.packages.find] where = ["src"]`.
  - Add `[tool.setuptools.package-data] "circuitsmith.schema" = ["*.json"]`.
- **2.6 `tests/conftest.py` delete.** The `sys.path` splice at
  [conftest.py:14-16](../../../../tests/conftest.py#L14-L16) is
  obsolete under editable install; remove the file.
- **2.7 Portability lint retarget.** Edit
  [scripts/portability_lint.py:2,149](../../../../scripts/portability_lint.py#L2)
  to scan `src/circuitsmith/` rather than `.claude/skills/circuit/`.
  Rule set unchanged.
- **2.8 Pre-commit hook retarget.** Edit
  [scripts/pre-commit:159](../../../../scripts/pre-commit#L159):
  `^\.claude/skills/circuit/` → `^src/circuitsmith/`. Update the
  comments at lines 15 and 155.
- **2.9 `scripts/generate-schematic.py`.** Either:
  - Replace the dynamic-import-by-path at
    [generate-schematic.py:34,52](../../../../scripts/generate-schematic.py#L34)
    with `from circuitsmith.components import mcus`.
  - Or delete the script — CLAUDE.md notes it as a predecessor-repo
    artefact. The decision goes in the branch-commit message.

**Verification of Phase 2.** In a clean venv:
`pip install -e .[dev]` succeeds; `pytest` is green;
`python scripts/portability_lint.py` is green;
`git commit` on a no-op edit inside `src/circuitsmith/` triggers
the hook against the new path.

### Phase 3 — Agent-facing surface

- **3.1** Update code samples in
  [.claude/skills/circuit/docs/index.md:77](../../../../.claude/skills/circuit/docs/index.md#L77)
  and
  [.claude/skills/circuit/docs/components.md:135](../../../../.claude/skills/circuit/docs/components.md#L135):
  `from circuit.schema import …` → `from circuitsmith.schema import …`.
- **3.2** Retarget code-owner reminder skills.
  `.claude/skills/co-netgraph/SKILL.md`,
  `.claude/skills/co-erc-engine/SKILL.md`,
  `.claude/skills/co-schema/SKILL.md` — update `path:` (or
  equivalent trigger) targets from `.claude/skills/circuit/…` to
  `src/circuitsmith/…`. Reminder content (the invariants surfaced)
  is unchanged.
- **3.3** *(Optional in this refactor)* Add skill shim `.py` files
  next to `SKILL.md` for any agent-callable surface that benefits
  from one. Pattern: `from circuitsmith.X import main; main()`.
  Defer to follow-up tasks if no concrete need exists today.

### Phase 4 — Repo docs and CHANGELOG

- **4.1** Grep repo-internal docs for `.claude/skills/circuit/`:
  [CLAUDE.md](../../../../CLAUDE.md),
  [docs/developers/ARCHITECTURE.md](../../../../docs/developers/ARCHITECTURE.md),
  [docs/developers/TESTING.md](../../../../docs/developers/TESTING.md),
  [docs/developers/CI_PIPELINE.md](../../../../docs/developers/CI_PIPELINE.md),
  [docs/developers/CODE_OWNERS.md](../../../../docs/developers/CODE_OWNERS.md),
  [docs/developers/AUTONOMY.md](../../../../docs/developers/AUTONOMY.md).
  Update references that point at *library code* to
  `src/circuitsmith/`; leave references that point at the
  *agent-facing skill* (SKILL.md, docs/) alone.
- **4.2** [`scripts/README.md`](../../../../scripts/README.md) lines
  13 and 51 — path descriptions.
- **4.3** [`CHANGELOG.md`](../../../../CHANGELOG.md) `[Unreleased] ###
  Changed`, one bullet: *"Relocate library code from
  `.claude/skills/circuit/` to `src/circuitsmith/` and rename the
  importable package from `circuit` to `circuitsmith` (supersedes
  ADR-0007 via ADR-0012)."*
- **4.4** [`.vibe/config.toml`](../../../../.vibe/config.toml) — no
  change. The `circuit` skill still exists at
  `.claude/skills/circuit/`, just with less code.

### Phase 5 — Verification gates and merge

- **5.1** Zero matches for:
  - `rg -n "from circuit\." -t py`
  - `rg -n "^import circuit$" -t py`

  Matches in `docs/developers/ideas/archived/`, in ADR-0007's
  `## Supersession` link, and in this idea file are expected and
  fine.
- **5.2** `rg -n "\.claude/skills/circuit/" -t py` returns zero.
  Matches in `.md` / `.toml` are fine if they point at the
  agent-facing skill folder (SKILL.md, docs/), not at library code.
- **5.3** Full `pytest` green.
- **5.4** `python scripts/portability_lint.py` green.
- **5.5** `python -m build` produces a wheel containing
  `circuitsmith/schema/*.json`.
- **5.6** Squash-merge to `main` per CLAUDE.md. Commit subject:
  `refactor(circuitsmith): relocate library to src/, supersede ADR-0007`.
  Body enumerates the five phases.

### Rollback

The refactor is one branch. Before merge: `git checkout main` and
drop the branch. After merge:
`git revert <squash-sha>` on `main` — the squash is self-contained,
revert is clean. The two cross-branch dependencies (ADR-0012 file
existence, EPIC-006 rewrite/retirement decision) are inside the
same squash and revert with it.

### Out of scope

Things this refactor explicitly does **not** do:

- No new `circuitsmith.erc_engine` implementation. The slot in the
  proposed tree is a *planned* file; the ERC engine lands with its
  own epic.
- No EPIC-002 rendering reshuffle. `circuitsmith.renderer` stays
  as a top-level module; EPIC-002 may move it into the
  `circuitsmith.render` subpackage as part of its own work.
- No PyPI publication. ADR-0012 documents publication as the new
  distribution channel, but actually pushing the wheel is a task
  inside the rewritten EPIC-006, not inside this refactor.
- No skill-shim rollout. Phase 3.3 is optional and deferred unless
  a concrete agent-callable surface needs one today.
