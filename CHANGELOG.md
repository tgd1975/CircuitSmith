# Changelog

All notable changes to CircuitSmith are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) at
a relaxed cadence — bullet lists per release, no per-PR enumeration. The
project version follows [Semantic Versioning](https://semver.org/) once the
first tag is cut.

## [Unreleased]

### Added

- **EPIC-012 — tutorial and example gallery (scaffold).** User-docs
  home at `docs/users/` chosen via ADR-0014 and pointed at from the
  repo `README.md` (TASK-092). Tutorial scaffold under
  `docs/users/tutorial/` (six-step index + six placeholder step
  files) and gallery scaffold under `docs/users/examples/` (five
  placeholder example subdirectories with the index table) landed
  empty, ready for TASK-094..101 to fill (TASK-093).
- **Tutorial steps 1-3** (TASK-094) — minimal circuit, fan-out
  branch, and repeated R+LED sub-blocks. Each step's `.circuit.yml`
  is committed alongside its rendered SVG + sidecars. Prose
  references the committed YAML, never pastes it.
- **Tutorial steps 4-6** (TASK-095) — ERC E1 round-trip
  (deliberate floating input, broken/fixed pair committed), BOM
  export via the library API (no dedicated CLI yet) with the
  PartsLedger round-trip documented as manual, and layout
  iteration via `--layout` override on top of the kernel's output.
- **Gallery scaffolding** — five gallery entries land with the
  six-section README template (TASK-096..100). Only the voltage
  divider's `circuit.yml` is committed; all five rendered artefact
  sets are deferred until the v0.1 kernel and component-library
  follow-ups land. Each README carries an honest "blocked-on" note
  pointing at IDEA-008 / IDEA-009.
- **Tutorial + gallery regression-diff CI gate** (TASK-101).
  `scripts/check_gallery_regression.py` re-renders every committed
  `.circuit.yml` under `docs/users/{tutorial,examples}/`, diffs
  against committed artefacts, supports `--rebaseline`. Wired into
  `ci.yml`, allow-listed in `.claude/settings.json`, tests in
  `tests/test_check_gallery_regression.py`.
- **EPIC-012 closed** — all 10 tasks closed in one branch; see the
  [epic file](docs/developers/tasks/closed/epic-012-tutorial-and-examples.md).

### Tooling

- Elevated IDEA-003, IDEA-004, IDEA-007 to EPIC-011 (test plan + coverage
  matrix, 9 tasks), EPIC-012 (tutorial + example gallery, 10 tasks), and
  EPIC-013 (post-EPIC-006 documentation audit, 8 tasks).
- Filed IDEA-008 (first-class sub-block authoring + kernel
  canonical rules for non-LED passive groupings) and IDEA-009
  (active-device component profiles + multi-page renderer support)
  as the unblocking follow-ups for the EPIC-012 gallery's deferred
  rendered artefacts.

## [v0.1.0] — 2026-05-13

First public release. CircuitSmith generates documentation-quality
schematics from declarative `.circuit.yml`, validates them against a
15-rule ERC catalog, exports KiCad-compatible BOM + netlist, and ships
the agent-facing `/circuit` skill that drives all of it. The
`circuitsmith` Python package is the unit of distribution per ADR-0012.

### Added

- **EPIC-001 — component library + schema.** ESP32 / nRF52840 MCU
  profiles (TASK-001), unified passives with colour-indexed LED
  (TASK-002), connectors (TASK-003), I²C sensors (TASK-004), JSON
  schema + S4/S5 post-schema validator (TASK-005, TASK-006), skill
  scaffolding (TASK-007).
- **EPIC-002 — renderer + layout engine.** `NetGraph` shared contract
  (TASK-008), deterministic kernel placer (TASK-009), Manhattan
  router (TASK-010), v0.1 structural rubric (TASK-011), renderer
  CLI (TASK-012), layout schema + validator (TASK-013), full-pedal
  fixtures (TASK-014, TASK-015), AI placer with `--no-ai` opt-out
  (TASK-017, TASK-018), v1 numeric rubric checks promoted (TASK-019),
  `meta.yml` provenance + AI invocations (TASK-020, TASK-057),
  Phase 2b trigger gate (TASK-058, TASK-059).
- **EPIC-003 — ERC engine + rule catalog.** Topology-only ERC with
  S1–S3 + E1–E10 (TASK-022), renderer integration (TASK-023),
  `rules.json` catalog seeded with 15 entries (TASK-024), catalog
  validator (TASK-025), educational rule backlog (TASK-026),
  catalog-enriched reports (TASK-027, TASK-028), CI gates and
  per-check reference (TASK-029, TASK-030).
- **EPIC-004 — BOM + netlist exporters.** `bom_exporter.py`
  (TASK-031), KiCad netlist exporter (TASK-033), staleness gate
  (TASK-035), parser-level grammar test (TASK-049). KiCad import
  spot-check (TASK-034). Build-guide BOM include per ADR-0013
  (TASK-032).
- **EPIC-005 — Markdown ` ```circuit ` blocks.** Block-rewrite
  scanner (TASK-036), `show_source` flag (TASK-037), artefact
  regeneration orchestrator (TASK-038).
- **EPIC-006 Phase 6 + 7a — `/circuit` skill + release workflow.**
  `SKILL.md` with the seven behavioural rules and post-ADR-0012
  `allowed-tools` allowlist (TASK-039, TASK-040), skill docs
  finalised (TASK-042), `RELEASING.md` + `release.yml` + version
  lockstep test (TASK-081), `/release` skill (TASK-082).
- **EPIC-007 — Python project bootstrap.** `pyproject.toml` +
  dev requirements (TASK-046), pytest config (TASK-047), CI
  workflow (TASK-048), ruff lint (TASK-061).
- **EPIC-008 — architecture fitness functions.** ADR seed
  (TASK-054), portability lint (TASK-051), code-owner skills
  mechanism + first three skills (TASK-055, TASK-056),
  boundary-import contract test (TASK-050), `.circuit.yml` schema
  pre-commit (TASK-052), NetGraph golden-hash CI contract
  (TASK-053), personal-data leak detection (TASK-074),
  idea/task-template lint fix (TASK-075).
- **EPIC-009 — first-day developer docs.** `DEVELOPMENT_SETUP.md`,
  `TESTING.md`, `CODING_STANDARDS.md`, `CI_PIPELINE.md`,
  `TASK_SYSTEM.md`, `CODE_OF_CONDUCT.md`, `ARCHITECTURE.md`,
  `MERMAID_STYLE_GUIDE.md`, `SECURITY_REVIEW.md`, `COMMIT_POLICY.md`,
  `BRANCH_PROTECTION_CONCEPT.md`, GitHub branch protection on `main`
  (TASK-062 through TASK-073).
- **EPIC-010 — `circuitsmith` package relocation.** Library moved
  from `.claude/skills/circuit/` to `src/circuitsmith/` (TASK-077);
  agent surface aligned (TASK-078); repo docs sweep (TASK-079).
  Decided in [ADR-0012](docs/developers/adr/0012-library-as-installable-package.md),
  superseding ADR-0007 (TASK-076).
- TASK-060 — autonomous-implementation mode (`AUTONOMY.md`,
  `/epic-run` driver, `human-in-loop:` operational contract).
- ADRs 0001–0013 covering layout slots, AI-at-authoring-time,
  NetGraph as shared contract, exporter decoupling, ERC pre-layout,
  rule catalog authoritative, library-as-package, build-guide
  link-not-include.

### Tooling

- Pre-commit hook + `/commit` pathspec wrapper for atomic commits
  with provenance tokens; pre-commit chains markdownlint, ruff,
  schema, ERC, exporter, and circuit-artefact regen.
- Security-review git hooks (pre-merge-commit, post-merge,
  pre-rebase) ported from AwesomeStudioPedal.
- `uv` adopted for venv lifecycle; `.venv/bin/python|pytest|ruff`
  allow-listed.
- `ruff` adopted as Python linter (minimal ruleset: E4/E7/E9/F).

### Documentation

- Skill docs: `circuit-yaml.md`, `components.md`, `erc-checks.md`,
  `layout.md`, `index.md` with worked `/circuit` invocation examples.
- `RELEASING.md` documents the release procedure; the `/release`
  skill is the operational driver.
- `CHANGELOG.md` follows Keep a Changelog 1.1.0.

### Policy

- Branch merges to `main` are squash-merged; CHANGELOG `[Unreleased]`
  is updated in the same commit.
- CHANGELOG release-promotion (`[Unreleased]` → `[vX.Y.Z]`) rides
  with the release commit, not a follow-up.
- No LLM-attribution trailers in commits or PR bodies.
- No personal contact info in committed files — route through GitHub.
- `git push` and `gh pr create`/`gh pr merge` require explicit
  per-invocation user approval.
