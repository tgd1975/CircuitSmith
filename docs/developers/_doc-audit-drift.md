# Doc-audit drift catalogue (TASK-103)

> Working document for **EPIC-013 — Post-EPIC-006 Documentation Audit**.
> Underscore-prefixed, not indexed. Catalogues drift only — **fixes happen
> in TASK-104 (voice rewrite) and TASK-105/106/107/109**, not here.
> Produced 2026-06-21. Input: `_doc-audit-inventory.md`.

## Method

Walked the prose-doc universe from `_doc-audit-inventory.md` in freshness
order. Technique: (1) `grep` for the known retired scripts and renamed
paths (`generate-schematic.py`, `data/config.json`, `from circuit.`,
`.claude/skills/circuit/*.py`, "concept stage", "exists yet"); (2) read
each prose file against the shipped reality; (3) fan-out read via three
sub-agents; (4) **every concrete item below was `grep`/`Glob`-verified** —
agent-reported line numbers that proved wrong were corrected (e.g. the
`circuit-yaml.md` moved-filepath items were mis-attributed to
`components.md` by the sub-agent; verification put them right).

**Ground truth.** CircuitSmith is a shipped `circuitsmith` package (PyPI
v0.1.0). Python lives in `src/circuitsmith/`, relocated from
`.claude/skills/circuit/` (ADR-0012, TASK-077); imports are
`from circuitsmith.*`. Predecessors `generate-schematic.py` /
`data/config.json` live in AwesomeStudioPedal, **not** here.

Status legend: `open` = catalogued, unfixed. Resolving tasks strike the row
through and add the commit ref (per TASK-104 AC).

## Drift items

| # | File:line | Class | Description | Proposed fix | Status |
|---|---|---|---|---|---|
| D1 | `README.md:5` | shipped-planned-feature | "⚠️ Concept stage. Everything below describes the *target* state" | Remove banner; lead with "CircuitSmith generates schematics from declarative YAML — shipped at v0.1.0." | open → TASK-109 |
| D2 | `README.md:6` | shipped-planned-feature | "None of the pipeline, skill, or component library exists yet" | Delete; the full pipeline ships in `src/circuitsmith/`. | open → TASK-109 |
| D3 | `README.md:18` | shipped-planned-feature | "**Status:** concept stage." | Replace with current version/scope line. | open → TASK-109 |
| D4 | `README.md:~71` | shipped-planned-feature | "None of the product code exists yet — Phase 1 (EPIC-001) starts the…" | Retense to shipped; describe the v0.1.0 module set. | open → TASK-109 |
| D5 | `README.md:~71–75` | moved-filepath | Prose implying the product "ships inside `.claude/skills/circuit/`" | Code is `src/circuitsmith/`; the skill is the agent-facing wrapper that delegates to it. | open → TASK-109 |
| D6 | `CONTRIBUTING.md:3` | shipped-planned-feature | "CircuitSmith is at concept stage." | "CircuitSmith is shipped at v0.1.0; the work breakdown lives in…" | open → TASK-109 |
| D7 | `CLAUDE.md:11` | shipped-planned-feature | "The repo is currently at concept stage —" | Retense the opening clause only; the rest of the sentence (dossier location, predecessor artefacts in ASP) is accurate. **Meta file — minimal touch.** | open → TASK-104 |
| D8 | `RELEASING.md:37` | broken-internal-link | "S/E IDs are stable per `docs/erc-checks.md`" — no such file | Point at `.claude/skills/circuit/docs/erc-checks.md` (canonical reference) or `src/circuitsmith/knowledge/rules.json`. | open → TASK-105 |
| D9 | `ARCHITECTURE.md:8–9` | shipped-planned-feature | Status block: "None of the product code exists yet — implementation begins with EPIC-001" | Delete the status block; the modules it describes all ship. Body below is largely accurate — voice/tense pass only. | open → TASK-104 |
| D10 | `TESTING.md:43` | shipped-planned-feature | "`tests/` … does not yet exist at concept stage" | `tests/` is populated; retense. | open → TASK-107 |
| D11 | `TESTING.md:54` | stale-import | `from circuit.netgraph import NetGraph` | `from circuitsmith.netgraph import NetGraph` | open → TASK-107 |
| D12 | `TESTING.md:96` | stale-import | `from circuit.schema import is_known_component` | `from circuitsmith.schema import is_known_component` | open → TASK-107 |
| D13 | `TESTING.md:113` | stale-import | `from circuit.pipeline import run` | `from circuitsmith.*` — **verify the module**; there may be no `pipeline` (likely the renderer/CLI entrypoint). | open → TASK-107 |
| D14 | `TESTING.md:147` | shipped-planned-feature | "At concept stage there is no product code to measure" | Retense; describe current coverage posture (cross-ref `testing/README.md`). | open → TASK-107 |
| D15 | `TESTING.md` (whole) | duplicate-coverage | Predates and overlaps `docs/developers/testing/` (EPIC-011) | Reconcile: trim to an intro pointing at `testing/README.md` as canonical, or fold unique content in. | open → TASK-107 |
| D16 | `.claude/skills/circuit/docs/circuit-yaml.md:9` | broken-internal-link | `[renderer.py](../renderer.py)` → `.claude/skills/circuit/renderer.py` does not exist | Link to `src/circuitsmith/renderer.py` (or drop the file link; it's a module). | open → TASK-105 |
| D17 | `.claude/skills/circuit/docs/circuit-yaml.md:58` | moved-filepath | "code change in `.claude/skills/circuit/components/*.py`" | `src/circuitsmith/components/*.py` | open → TASK-105 |
| D18 | `.claude/skills/circuit/docs/circuit-yaml.md:290` | broken-internal-link | `[circuit.schema.json](../schema/circuit.schema.json)` → `.claude/skills/circuit/schema/` does not exist | Link to `src/circuitsmith/schema/circuit.schema.json`. | open → TASK-105 |
| D19 | `docs/users/README.md:16–18` | shipped-planned-feature | "expect the tutorial and gallery directories to fill in incrementally" | EPIC-012 closed; remove the status note. | open → TASK-106 |
| D20 | `docs/users/tutorial/README.md:36` | broken-internal-link | `[circuit-yaml.md](../../developers/circuit-yaml.md)` — target absent | Repoint to `.claude/skills/circuit/docs/circuit-yaml.md` (correct relative depth). | open → TASK-105 |
| D21 | `docs/users/tutorial/README.md:40` | broken-internal-link | `[erc-checks.md](../../developers/erc-checks.md)` — target absent | Repoint to `.claude/skills/circuit/docs/erc-checks.md`. | open → TASK-105 |
| D22 | `docs/users/tutorial/README.md:43–48` | shipped-planned-feature | "step files are placeholders … until [TASK-094/095] land" | Both closed; steps complete. Remove the status block. | open → TASK-106 |
| D23 | `docs/users/tutorial/README.md:28,44,46` | broken-internal-link | Task links labelled `tasks/open/` but files now in `tasks/closed/` | Update the paths to `closed/`. | open → TASK-105 |
| D24 | `docs/users/examples/README.md:53` | broken-internal-link | `[circuit-yaml.md](../../developers/circuit-yaml.md)` — target absent | Repoint to the skill doc. | open → TASK-105 |
| D25 | `docs/users/tutorial/05-bom-export.md:110` | broken-internal-link | `[IDEA-005](../../developers/ideas/open/idea-005-…)` — file is in `archived/` | Change `open/` → `archived/`. | open → TASK-105 |

## Scanned — no drift

Every prose file in `_doc-audit-inventory.md` not appearing above was read
and is clean (no silent omissions, per AC):

- **Root:** `CHANGELOG.md`.
- **`docs/developers/`:** `CI_PIPELINE.md`, `DEVELOPMENT_SETUP.md`,
  `CODING_STANDARDS.md`, `COMMIT_POLICY.md`, `TASK_SYSTEM.md`,
  `AUTONOMY.md`, `SECURITY_REVIEW.md`, `MERMAID_STYLE_GUIDE.md`,
  `CODE_OWNERS.md`, `BRANCH_PROTECTION_CONCEPT.md`, `adr/README.md`.
- **`docs/developers/testing/` (EPIC-011):** all 11 files
  (`README`, `_inventory`, `schema`, `netgraph`, `layout-kernel`, `router`,
  `renderer`, `erc-engine`, `exporters`, `skill-orchestration`,
  `ci-gates`).
- **`docs/users/`:** `tutorial/01`, `02`, `03`, `04`, `06`; all five
  `examples/*/README.md`.
- **`docs/builders/wiring/`:** `esp32/README.md`, `nrf52840/README.md`.
- **Circuit skill:** `SKILL.md`, `docs/index.md`, `docs/components.md`,
  `docs/layout.md`, `docs/erc-checks.md`, `CHANGELOG.md` (frozen).
- **Knowledge:** `src/circuitsmith/knowledge/BACKLOG.md` (a stale "27 rule"
  count exists but the file tracks *educational* rules, not enforced ERC
  checks — out of audit scope, noted not catalogued).

## Intentional — explicitly NOT drift

So the rewrite does not "fix" these by mistake:

- **`README.md:23–24`, `CLAUDE.md:15`** — links/mentions of
  `generate-schematic.py` and `data/config.json` pointing at the
  **AwesomeStudioPedal** repo. Correct: they are predecessor artefacts that
  genuinely live there. Leave as external attributions.
- **All `generate-schematic.py` / `data/config.json` references inside
  `ideas/archived/idea-001.*`, closed task files, and ADRs** — legitimate
  historical record (TASK-103 note re: retired tasks). Out of scope.
- **ERC-check doc layering** (`erc-checks.md` ↔ `testing/erc-engine.md` ↔
  `rules.json` ↔ dossier) — intentional, audience-specific; `rules.json` is
  authoritative. Do not collapse.

## Summary

- **25 drift items** across **11 files**.
- By class: shipped-planned-feature ×10, broken-internal-link ×9,
  stale-import ×3, moved-filepath ×2, duplicate-coverage ×1.
- **Concentration:** the "concept stage / nothing exists yet" cluster
  (`README`, `ARCHITECTURE`, `CONTRIBUTING`, `CLAUDE`, `TESTING`,
  `users/*`) is the single biggest theme — the docs froze at concept stage
  while the package shipped through v0.1.0. The other cluster is the
  `src/circuitsmith/` relocation aftermath (stale `from circuit.*` imports +
  `.claude/skills/circuit/` paths) that never reached `TESTING.md` and
  `circuit-yaml.md`.
- **Hand-off:** D1–D5 → TASK-109 (README, Main-HIL). D7, D9 → TASK-104
  (voice). D10–D15 → TASK-107 (test-plan alignment). D19, D22 → TASK-106
  (tutorial alignment). D8, D16–D18, D20–D21, D23–D25 → TASK-105 (cross-ref
  audit + `check_doc_references.py`).

## Resolution log

- **2026-06-21 — TASK-104** (this commit). Resolved **D6** (CONTRIBUTING
  opener), **D7** (CLAUDE opener), **D9** (ARCHITECTURE status block), and
  **D1–D5** (README concept-stage banners, status paragraph, and the
  `.claude/skills/circuit` "ships everything" claim — *interim* de-lying so
  the front page is truthful; the full blank-page README rewrite is
  TASK-109). Fixed in passing: ARCHITECTURE's stale ERC ranges
  `S1–S3 + E1–E10` → `S1–S7 + E1–E22` (**D26**, newly found). Canonical
  voice note added to `CODING_STANDARDS.md` (§ Documentation voice).
- **Newly found, still open:** **D27** — `README.md` `## Phase plan` section
  is still framed as unbuilt ("before EPIC-001 produces real Python code");
  **D28** — `README.md:179` license reads "MIT (planned)". Both fold into
  TASK-109's full rewrite.
- **2026-06-21 — TASK-105** (this commit). Shipped
  `scripts/check_doc_references.py` (class-1 relative-link gate, wired into
  CI as `check-docs-refs`; the ID / code-path / external-URL classes are
  behind flags) + its `tests/` suite. Resolved the broken links it found:
  **D8** (RELEASING erc-checks path), **D16/D17/D18** (circuit-yaml.md →
  `src/circuitsmith/`), **D20/D21/D24** (user-doc links → skill docs),
  **D25** (idea-005 open→archived), plus a previously-uncatalogued cluster
  of relocation-broken links in `circuit-yaml.md` / `layout.md`. **D23**
  (tutorial task-folder labels) is accepted by the gate's lifecycle-folder
  normalisation — housekeep moves task files without rewriting inbound
  links, so the file existing by ID is what's enforced.
- **2026-06-21 — TASK-106** (this commit). Resolved **D19** (users/README
  status note) and **D22** (tutorial/README placeholder block) — both
  EPIC-012 statuses are now closed. Added tutorial/gallery "See also"
  pointers to `circuit-yaml.md`, `layout.md`, `erc-checks.md`, and a
  canonical-term glossary to `ARCHITECTURE.md`. No terminology
  disagreements found (the tutorial steps scanned clean against the
  reference docs).
- **Still open:** D10–D15 → TASK-107 (TESTING reconcile + stale imports);
  D27, D28 → TASK-109 (README full rewrite).
