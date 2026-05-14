# Changelog

All notable changes to CircuitSmith are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) at
a relaxed cadence — bullet lists per release, no per-PR enumeration. The
project version follows [Semantic Versioning](https://semver.org/) once the
first tag is cut.

## [Unreleased]

### Added

- **EPIC-012 — tutorial and example gallery** closed (10 tasks).
  User-docs home at `docs/users/` (ADR-0014); six tutorial steps
  with committed `.circuit.yml` + rendered SVG sidecars (TASK-092..095);
  five gallery entries scaffolded with blocked-on notes pointing at
  EPIC-014 (TASK-096..100); regression-diff CI gate via
  `scripts/check_gallery_regression.py` with `--rebaseline` support
  (TASK-101).
- **EPIC-014 Phase 0 — frozen decisions** (TASK-110). IDEA-008/009
  open-question defaults accepted verbatim into the epic body's
  *Frozen decisions* table; bundle-vs-split overridden to bundled.
- **EPIC-014 Phase 1 — non-LED kernel rules** (TASK-111..114).
  `RULE_RC_LOW_PASS`, `RULE_RC_HIGH_PASS`, `RULE_CC_DECOUPLING`,
  `RULE_RR_VOLTAGE_DIVIDER` in the layout kernel. Voltage-divider
  rule gated on `/^(V?REF|SENSE|ADC|DIV|TAP)/i` tap-net regex or
  `role: divider` annotation.
- **EPIC-014 Phase 2 — sub-block authoring end-to-end** (TASK-115..118).
  Schema gains `sub-blocks:` + `instances:` with named-port maps;
  validator gains S6/S7. `NetGraph.from_yaml_dict` auto-flattens via
  `flatten_sub_blocks()`. ERC adds E11..E15. Renderer writes
  un-flattened instance grouping into meta sidecar. CHECK_TABLE
  grew 15 → 20.
- **EPIC-014 Phase 2 docs — tutorial step 3 rewritten + skill docs
  updated** (TASK-119). Tutorial step 3 ([`docs/users/tutorial/03-sub-blocks.md`](docs/users/tutorial/03-sub-blocks.md))
  swaps the "repeated R+LED workaround" prose for a first-class
  `led_indicator` sub-block instantiated three times.
  `circuit-yaml.md` gains a *Sub-blocks and instances* section
  with the frozen-decisions contract; `layout.md` gains an
  *inline-box mode* section. Fixed a counting regression in the
  renderer's meta sidecar: `layout.total` now reports flat-
  component count instead of pre-flatten top-level entries.
- **EPIC-014 Phase 4 — BJT NPN/PNP profiles + canonical kernel
  rule** (TASK-120, ADR-0015). New
  [`actives.py`](src/circuitsmith/components/actives.py) ships
  `actives/bjt_npn` and `actives/bjt_pnp` with `B`/`C`/`E` pin
  keys and per-pin `role:` annotations. Kernel gains
  `RULE_BJT_TO_GND` (id 15) and `RULE_RESISTOR_WITH_BJT` (id 16)
  — only the base-drive resistor attaches to the BJT.
- **EPIC-014 Phase 4 — `ic/555` profile + generic-IC kernel rule**
  (TASK-121). New [`ics.py`](src/circuitsmith/components/ics.py)
  ships `ic/555` with silkscreen-pin keys `"1".."8"` per ADR-0010
  and silicon names in `pins.X.alt:`. Registry gains a
  `metadata.type:` override mechanism so `ics.py:ic_555`
  registers as `ic/555` (singular). Validator's S5 check accepts
  pin-name aliases. Kernel gains `RULE_GENERIC_IC` (id 17) for
  multi-pin ICs.
- **EPIC-014 Phase 4 — `ic/opamp_dual_supply` profile** (TASK-122).
  Extends `ics.py` with the dual-supply op-amp. Symbolic pin keys
  (`IN+`, `IN-`, `OUT`, `V+`, `V-`) per the EPIC-014 frozen-decisions
  table — ADR-0010 doesn't apply because the triangle symbol shows
  no pin numbers. Shares `RULE_GENERIC_IC` with the 555.
- **EPIC-014 Phase 4 — active-device ERC rules** (TASK-123). Three
  new ERC rules: E16 (BJT pin role unset — error), E17 (op-amp
  power pin floating — error), E18 (555 pin-naming drift —
  warning). Catalogue entries in `rules.json`; CHECK_TABLE grew
  20 → 23. The op-amp / 555 profiles' `metadata.kind` was refined
  to `"opamp"` / `"timer"` so ERC checks discriminate via `kind:`
  per the project's category-lint contract.
- **EPIC-014 Phase 5 — `pages:` partition schema** (TASK-124).
  `.layout.yml` gains an opt-in top-level `pages:` array and a
  per-placement `page:` field; cross-validation as
  `layout-pages-duplicate-name` / `layout-page-undeclared`.
  `Placement.page` round-trips through the kernel; attached-to
  components inherit the anchor's page so RWL/RWB pairs never
  split across pages. v0.1 layouts (no `pages:` block) render
  byte-identical. Foundation for TASK-125..127.
- **EPIC-014 Phase 5 — multi-page render driver** (TASK-125).
  `.layout.yml` with ≥ 2 declared pages now emits one SVG per
  page (`<stem>-p1.svg`, `<stem>-p2.svg`, …) via
  `_emit_pages_or_single` + `_filter_to_page`. Single-page
  output keeps `<stem>.svg`. `.layout.yml`/`.meta.yml` stay
  singletons. Cross-page wires are dropped per-page; TASK-126
  adds the boundary label rendering.
- **EPIC-014 Phase 5 — cross-page net labels** (TASK-126). Each
  per-page SVG now annotates the cut wires with a `▶`/`◀`
  arrow glyph + `<net> ▶ <other_page>` text label, paired at
  both ends of every cross-page wire. Detection from
  `Placement.page` per IDEA-009's frozen-decisions table — no
  user-authored `cross-page-nets:` block.
- **EPIC-014 Phase 5 — cross-page ERC rules** (TASK-127). Four
  new rules: E19 (page declared but empty — warning), E20 (page
  referenced but undeclared — error), E21 (cross-page net
  invisible on one side — error), E22 (excessive cross-page
  net count, threshold-tunable via `meta.erc.cross-page-threshold`
  — warning). ERC `run()` grows a `layout=` kwarg; CHECK_TABLE
  grew 23 → 27.
- **EPIC-014 Phase 6 — voltage-divider gallery rendered**
  (TASK-128). `docs/users/examples/voltage-divider/` now ships
  the rendered SVG, layout sidecar, meta sidecar, and ERC
  report unblocked by TASK-114's R+R canonical rule. Layout
  schema broadened: `placement.label` enum → free-form string;
  `regionName` gains patterns for `rc-(low|high)-pass-*`,
  `cc-decoupling-*`, and `divider-*` synthetic regions.
- **EPIC-014 Phase 6 — common-emitter amplifier gallery rendered**
  (TASK-129, ADR-0016). First analog-signal-flow gallery entry.
  Two new kernel rules — `RULE_BJT_LOAD` (id 18) and
  `RULE_BJT_DEGENERATION` (id 19) — close the ADR-0015 coverage
  gap on the collector load and emitter degeneration resistors,
  landing them in synthetic per-BJT regions
  (`bjt-load-<ref>`, `bjt-degen-<ref>`).
- **EPIC-014 Phase 6 — 555 monostable gallery rendered**
  (TASK-130, ADR-0017). First multi-pin IC gallery entry. Pull-up
  rule widened to accept IC `SIGNAL_INPUT` pins (in addition to
  MCU GPIO/INPUT_ONLY), with rail-skip so the anchor picks the
  resistor's signal-side terminal rather than an unrelated
  coincident pin on VCC.
- **EPIC-014 Phase 6 — op-amp non-inverting buffer gallery
  rendered** (TASK-131). First dual-rail-supply gallery entry.
  Unity-gain feedback (`A1.OUT ↔ A1.IN-`) on a single
  `BUF_OUT` net keeps E10 (multi-net-pin) quiet; one decoupling
  cap per rail satisfies E17 (power-pin floating) without
  pairing into C+C. All 8 components placed on existing rules
  — no kernel diff needed.
- **EPIC-014 Phase 6 — multi-page split gallery rendered**
  (TASK-132). Reuses the CE-amp topology, partitions across
  two pages via `layout.yml`'s `pages:` block. Two SVGs
  (`-p1.svg`, `-p2.svg`) from one `circuit.yml`; `GND` cross-page
  label glyph (`GND ▶ p2` / `p1 ◀ GND`) renders on both pages.
  Three nets span the boundary — under the E22 six-net
  threshold. Gallery regression script
  (`scripts/check_gallery_regression.py`) extended to compare
  per-page SVGs (`<base>-p<N>.svg`) in addition to the
  single-SVG path.
- **EPIC-014 Phase 6 — component-skill docs final pass**
  (TASK-133). Layout skill docs' canonical-slot table extended
  with rule IDs 11–19 (RC low-pass, RC high-pass, CC decoupling,
  R+R divider, BJT, RWB, generic IC, BJT load, BJT degeneration);
  pull-up row updated to note ADR-0017's IC SIGNAL_INPUT
  widening. `index.md` ERC count corrected from 15 to 27.
  `erc-checks.md` gains an S6/S7 section (sub-block schema
  validation, TASK-117). Gallery README index updated: all five
  entries now ship with committed SVGs; source links point at
  the closed EPIC-014 tasks (TASK-128..132) instead of the
  superseded TASK-096..100.
- **EPIC-014 closed** (24/24 tasks, 4 ADRs filed: ADR-0015,
  ADR-0016, ADR-0017, plus EPIC-006's ADR-0014 referenced).
  Delivered: sub-blocks + instances grammar (Phase 2), four
  passive-shape kernel rules (RC LP, RC HP, CC pair, R+R
  divider, Phase 1), active-device profiles (BJT NPN/PNP,
  ic/555, ic/opamp_dual_supply, Phase 3), active-device ERC
  rules (E16/E17/E18, Phase 4), multi-page layout schema +
  renderer driver + cross-page label glyphs + cross-page ERC
  (E19–E22, Phase 5), all five gallery entries rendered
  (Phase 6), and a docs-only proofreading pass.

### Tooling

- Elevated IDEA-003/004/007 to EPIC-011 (test plan, 9 tasks),
  EPIC-012 (tutorial + gallery, 10 tasks), EPIC-013 (docs audit,
  8 tasks).
- Filed IDEA-008/009 as EPIC-012 unblockers; groomed both to full
  implementation-plan depth, then elevated into EPIC-014 (24 tasks).
  Source ideas archived at epic open.
- Merged IDEA-005 + IDEA-010 draft into IDEA-011 (PartsLedger
  inventory-adapter dossier).
- Opened IDEA-012 — gap analysis of archived IDEA-001 dossier vs
  shipped v0.1.0.

### Removed

- Relocated IDEA-006 (resistor color-band detector) to PartsLedger
  as their IDEA-011.

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
