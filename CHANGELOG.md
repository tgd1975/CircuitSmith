# Changelog

All notable changes to CircuitSmith are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) at
a relaxed cadence — bullet lists per release, no per-PR enumeration. The
project version follows [Semantic Versioning](https://semver.org/) once the
first tag is cut; until then the `[Unreleased]` section is the only entry.

## [Unreleased]

### Bootstrap

- Repository initialised from the IDEA-027 dossier in
  [AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal).
- Task system installed (45 → 49 open tasks across 7 epics).
- Pre-commit hook + `/commit` wrapper for atomicity and message-policy
  enforcement.
- Security-review git hooks (`pre-merge-commit`, `post-merge`, `pre-rebase`)
  ported from AwesomeStudioPedal; install via `bash scripts/install_git_hooks.sh`.

### Tooling

- TASK-046 closed: `pyproject.toml` (`requires-python = ">=3.11"`) and
  `requirements-dev.txt` landed — first Phase 0 prerequisite for EPIC-001
  cleared.
- TASK-047 closed: pytest configured (`testpaths = ["scripts/tests"]`,
  `python_files = "test_*.py"`, `addopts = "-ra"`, `strict_markers = true`).
  Pytest 9.0.2 silently drops `--strict-markers` from `addopts`, so the
  flag is set as a proper ini option. 114 tests discovered and green.
- TASK-048 closed: GitHub Actions CI workflow at
  `.github/workflows/ci.yml` — runs on `ubuntu-latest` and
  `windows-latest`, mirroring the pre-commit hook (markdownlint + pytest)
  so a `CS_COMMIT_BYPASS` cannot land broken code.
- TASK-061 closed: `ruff` adopted as the Python linter — minimal initial
  ruleset (`select = ["E4", "E7", "E9", "F"]`). Wired symmetrically into
  `pyproject.toml`, `scripts/pre-commit`, the `/commit` fixer registry
  (`*.py → ruff check --fix <files>`), and the `.claude/settings.json`
  allowlist. Baseline cleanup of `scripts/` — 10 findings fixed (4
  auto-fixed unused imports + 1 multi-import line; 6 `E741` ambiguous
  `l` in `test_housekeep.py` renamed to `ln`).
- **EPIC-007 (Project Bootstrap) closed** — all attributed tasks done.
- `uv` adopted for the Python venv lifecycle (`uv venv .venv`,
  `uv pip install -e ".[dev]"`). Mirrors AwesomeStudioPedal's `.venv`
  pattern and bypasses PEP 668's externally-managed system Python
  cleanly. `.claude/settings.json` allow-list extended with
  `Bash(uv venv|pip install|pip sync|sync|run:*)`,
  `.venv/bin/python|pytest|ruff`, and
  `scripts/generate-schematic.py` + `scripts/portability_lint.py`.
- `scripts/pre-commit` markdown lint exclude list extended with
  `.venv` so third-party `LICENSE.md` files inside the uv-managed
  venv don't fail the hook.
- Pre-commit hook: exclude `.claude/security-review-latest.md` from the
  markdownlint glob. The file is gitignored runtime state written by
  the security-review hook on every merge; markdownlint-cli2 doesn't
  consult `.gitignore`, so the exclude is set explicitly.

### Planning

- EPIC-008 (Architecture Fitness Functions and Governance) scaffolded
  with the Phase 2b trigger-gate tasks (TASK-049..059) — structural
  KiCad netlist test, portability lint, schema-validation pre-commit,
  netgraph golden-hash contract, ADR seed, and the
  `check-phase2b-trigger` release gate.
- TASK-060 scaffolded — seed for autonomous-implementation mode
  (AUTONOMY.md protocol, `/epic-run` driver, branch hygiene, HIL sweep)
  to drive EPIC-007 end-to-end as the first pilot.
- TASK-060 body extended with the planned `sed/awk/head/tail` deny
  entries for `.claude/settings.json` (observed during the EPIC-007
  pilot run) and a note that the existing allowlist is non-empty
  contrary to the original description.

### Policy

- `CLAUDE.md`: forbid diagnostic suffixes (`; echo "EXIT=$?"`,
  `&& echo OK`) on Bash invocations — the permission-allowlist matcher
  checks the whole command string, so the suffix would force a prompt
  even when the primary command is allowed.
- `CLAUDE.md`: forbid end-of-turn "continue?" checkpoints. The agent
  keeps going until the requested scope is done or a real stop-line is
  hit; the user suspends via laptop lid, not via question.
- `CLAUDE.md`: branch merges to `main` are **squash-merged** (one
  commit per branch, named for the branch's primary purpose) — never
  plain fast-forward.
- `CLAUDE.md`: `CHANGELOG.md` `[Unreleased]` is updated **as part of
  the same squash commit** that lands the work, not in a follow-up.
- `scripts/security_review_changes.py`: `ruff` added to the
  CRITICAL → HIGH demotion list for `permissions-allow-added` findings
  (alongside `git/grep/ls/python3/jq/...`). The demotion list is now
  annotated with a paragraph explaining the single-developer
  assumption and an explicit re-audit trigger for whenever an
  additional developer joins the project.

### Developer experience

- VSCode workspace: subtle copper window accent for visual identification
  of CircuitSmith windows (`titleBar.activeBackground` etc. in
  `.vscode/settings.json`).

### Governance (EPIC-008 unblocked slice)

- TASK-054 closed: `docs/developers/adr/` seeded with eight foundational
  ADRs (slots-not-coordinates, AI-at-authoring-time-only, NetGraph as
  shared contract, exporter decoupling, ERC pre-layout, rule catalog
  authoritative, skill directory is the library, Phase 2b on evidence)
  plus a README documenting the format, the add/supersede procedure,
  and the index.
- TASK-051 closed: `scripts/portability_lint.py` enforces the
  portability contract for `.claude/skills/circuit/` — no host-project
  paths, no project-module imports, no host-project name references.
  `.portability-allow.txt` carries auditable exceptions. Wired into
  the pre-commit hook (only fires on staged changes inside the skill
  dir) and the GitHub Actions workflow (unconditional). 18
  fixture-based tests cover each forbidden pattern, the `docs/`
  exception for sibling-project names, the allow-list resolver, and
  the empty/missing-dir no-op.
- TASK-055 closed: code-owner skills mechanism. `.claude/codeowners.yaml`
  registry binds file globs to `co-<name>` skills;
  `scripts/codeowner_hook.py` (registered under `hooks.PreToolUse` in
  `.claude/settings.json` with `matcher: "Edit|Write"`) prints the
  matched skill's body as an informational reminder. Glob syntax is
  gitignore-flavoured (`**`/`*`/`?` segment-aware); stdlib-only YAML
  parser keeps the per-edit overhead minimal. 26 tests cover the
  parser, matcher, body extractor, and the full `run()` flow.
  Documentation in `docs/developers/CODE_OWNERS.md`.
- TASK-056 closed: first three code-owner skills authored —
  `co-netgraph`, `co-schema`, `co-erc-engine` — each binding to its
  high-blast-radius module via the registry and declaring invariants
  as a checklist (hash determinism, schema-version bump on break,
  stable check IDs, etc.). Registered in `.vibe/config.toml`.
  Subsequent code-owner skills (`bom_exporter`, `netlist_exporter`,
  `knowledge/rules.json`, `layout_engine/kernel.py`) land alongside
  the modules they bind, not upfront.

EPIC-008 is partially closed: the four unblocked tasks above are done;
TASK-050 / TASK-052 / TASK-053 remain open until their respective
feature-epic deliverables land.

### Autonomy

- TASK-060 closed: autonomous-implementation mode wired up.
  - `docs/developers/AUTONOMY.md` codifies the four HIL values
    (`No` / `Clarification` / `Support` / `Main`) with defined agent
    behaviours, the epic-driver loop, the definition-of-done
    checklist, the review-packet format, the ADR-on-ambiguity rule,
    and the deny-vs-prompt split for published-effect actions.
  - `docs/developers/adr/0000-template.md` seeds a maintained blank
    ADR for future records.
  - `docs/developers/adr/0009-autonomous-implementation-mode.md`
    records the protocol's own decision.
  - `CLAUDE.md` gains a `## Autonomy` section pointing at
    AUTONOMY.md and stating that `human-in-loop:` is the
    operational contract.
  - `.claude/skills/epic-run/SKILL.md` is the protocol-scaffold
    driver skill the agent follows (composer over `/ts-task-active`,
    `/commit`, `/housekeep`, `/ts-task-done`, `/check-branch`).
  - `.claude/settings.json` `permissions.deny` extended with
    `Bash(sed:*)`, `Bash(awk:*)`, `Bash(head:*)`, `Bash(tail:*)`,
    `Bash(git push:*)`. `gh pr create` / `gh pr merge` are
    deliberately **not** in deny — they go through the
    prompt-by-default path so the user can approve per-invocation.
  - HIL sweep applied across 15 open tasks: 7 `Clarification` → `No`
    (TASK-001/009/012/014/019/022/036), 2 `Main` → `Support`
    (TASK-024 rule catalog, TASK-039 SKILL.md prompt), 6 `Main`
    kept (TASK-015/034/041/043/044/045). Each task gains a one-line
    `## Autonomy` rationale.
  - Open epic files (EPIC-001..006, EPIC-008) carry a
    `release/epic-NNN-<slug>` `branch:` field — `/ts-task-active`
    nags on mismatch with the `[c]ontinue` rewrite path.

### Documentation (EPIC-009 — Developer Docs and Governance Scaffolding)

- TASK-062 closed: `docs/developers/DEVELOPMENT_SETUP.md` — canonical
  first-time-setup walk-through. Tool prerequisites, Ubuntu / Windows 11
  install procedure, smoke-test, common-setup-problems appendix.
  `CONTRIBUTING.md` redirects to this doc.
- TASK-063 closed: `docs/developers/TESTING.md` — three conceptual test
  layers (unit / integration / contract / golden), pytest convention,
  `pyproject.toml` `testpaths` updated to `["tests", "scripts/tests"]`.
  Coverage tooling deferred until product code lands.
- TASK-064 closed: `docs/developers/CODING_STANDARDS.md` — naming,
  formatting (ruff), comment-WHY policy, public-function type-hint
  requirement.
- TASK-065 closed: `docs/developers/CI_PIPELINE.md` — inventory of the
  `ci.yml` workflow, gate semantics (all jobs blocking), local pre-commit
  hook mirror, red-build response sequence, known gap (ruff not yet in CI).
- TASK-066 closed: `docs/developers/TASK_SYSTEM.md` — human-facing
  counterpart to `AUTONOMY.md`. IDEA/EPIC/TASK artefacts, lifecycle
  states, every `/ts-*` skill catalogued, `/housekeep` role.
- TASK-067 closed: `docs/developers/CODE_OF_CONDUCT.md` — short custom
  CoC mirroring AwesomeStudioPedal's shape (not verbatim Contributor
  Covenant 2.1 — user override at activation). Enforcement contact is
  GitHub-routed ("contact the owner of the repository via GitHub"), no
  personal email anywhere in committed files. `pyproject.toml`
  `authors` field stripped of email.
- TASK-068 closed: `docs/developers/ARCHITECTURE.md` — top-down view.
  Mermaid pipeline (`flowchart LR`) and module-boundary graph
  (`graph TD`) with the three forbidden edges marked red dashed. Module
  table linking each module to its ADR(s) and code-owner skill.
  README's architecture section summarised down with link.
- TASK-069 closed: `docs/developers/MERMAID_STYLE_GUIDE.md` —
  diagram-type selector, palette, edge conventions, node-label rules,
  mandatory prose summary alongside every mermaid block for
  accessibility.
- TASK-070 closed: `docs/developers/SECURITY_REVIEW.md` — usage of
  `scripts/security_review_changes.py` and the three security-review
  hooks, reviewer checklist (secrets / shell-exec / path-traversal /
  dependency / permissions-allow / gh-PUT / skills / CI), bypass
  policy, escalation path.
- TASK-071 closed: `docs/developers/COMMIT_POLICY.md` — pathspec
  rationale with the concrete two-session race story, provenance-token
  mechanics, three-check hook-failure protocol, `CS_COMMIT_BYPASS`
  policy, squash-merge + CHANGELOG-rides-along rule, LLM-attribution
  trailer ban.
- TASK-072 closed: `docs/developers/BRANCH_PROTECTION_CONCEPT.md` —
  ruleset and rationale for GitHub server-side branch protection on
  `main` (status checks required, linear history, no force-push, no
  deletion; PR review off for solo posture with contributor-#2 flip
  trigger documented; admin enforcement off).
- TASK-073 closed: GitHub branch protection applied on
  `tgd1975/CircuitSmith/main` via `gh api --method PUT
  /repos/.../branches/main/protection --input <body>`. As-applied
  configuration matches `BRANCH_PROTECTION_CONCEPT.md` 1:1.
- TASK-074 scaffolded under EPIC-008 (architecture fitness functions):
  extend the security-review hook to mechanically detect personal-
  contact-info leaks (email / phone / real name beyond the GitHub
  handle). Surfaced from the TASK-067 user override; `feedback-no-
  personal-contact-in-docs` memory rule recorded.
- **Skill updates:** `/status` rewritten to four parallel Bash calls
  (printf-chained compound defeated the allowlist); `/housekeep` no
  longer runs `git add` (staging rides with the next `/commit`
  pathspec); `/epic-run` protocol gains a **Hand-off phase**
  (bundles the HIL stop-line task with the commit phase into one
  user-interaction block) and a **CHANGELOG-delta phase** (appends
  the run's missing entries to `[Unreleased]`, never edits or
  removes).
- **VS Code workspace palette refreshed** to dark orange
  (`titleBar.activeBackground: #4A2810`) — replaces the prior
  copper-toned palette while keeping the per-project visual
  identification pattern.
- **EPIC-009 closed** — all 12 tasks done. The first-day-junior
  documentation set + server-side branch protection are in place
  before EPIC-001 implementation work begins.

### Circuit skill (EPIC-001 — Component Library and Schema)

- TASK-001 closed: `.claude/skills/circuit/components/mcus.py` —
  `esp32` (Joy-IT NodeMCU-32S, 30-pin) and `nrf52840` (Adafruit
  Feather, 28-pin) dev-board profiles with chip-level electrical
  metadata (Vcc range, per-GPIO and total current budgets,
  strapping flags, default I²C `func` tags). Predecessor fixtures
  `data/config.json` and the two reference SVGs under
  `docs/builders/wiring/<target>/` brought in from
  AwesomeStudioPedal.
- TASK-002 closed: `.claude/skills/circuit/components/passives.py`
  — resistor, capacitor, unified `LED` profile with colour-indexed
  `v_forward_by_color` (red / green / amber / yellow / blue /
  white) and `v_forward_default`, pushbutton, piezo (rides on
  `category: resistor` per the layout-keys-not-semantics
  invariant).
- TASK-003 closed: `.claude/skills/circuit/components/connectors.py`
  — `usb_c`, `dc_jack_2_1mm`, mono / stereo 6.35 mm audio jacks.
  `make_header(n)` and `make_screw_terminal(n)` factories
  materialise sizes 2 / 3 / 4 / 6 / 8 at module import.
- TASK-004 closed: `.claude/skills/circuit/components/sensors.py`
  — `bme280` (default I²C address 0x76) and `ssd1306` (0x3C).
  Data-line pins use `type: I2C` plus
  `func: ["I2C_SDA" | "I2C_SCL"]` per the dossier's i2c-sensor
  rule.
- TASK-005 closed: `.claude/skills/circuit/schema/circuit.schema.json`
  plus the two-phase post-schema validator
  (`schema/validator.py`, `schema/registry.py`). JSON Schema
  enforces the three top-level sections (`meta`, `components`,
  `connections`) and the three connection forms (`pins`, `path`,
  `bus`) via `oneOf`. Dynamic `type:` validation walks
  `components/*.py` at validation time — adding a profile needs
  no schema regen. Findings carry `S4` (unknown component type)
  or `S5` (unknown pin reference) check codes.
  `tests/test_schema_validation.py` covers the four required
  fixtures plus mixed-form rejection and parametric
  three-top-level-section requirement.
- TASK-006 closed: `scripts/generate-schematic.py` refactored to
  import board pin tables from `components/mcus.py` via
  `importlib`; circuit-role assignment (which silicon pin drives
  which LED / button) stays in the script as firmware/config
  concern. `tests/test_generator_byte_identity.py` runs the
  refactored generator and compares to the on-disk references
  with matplotlib non-determinism normalised (`<dc:date>`, random
  clip-path IDs, mpl version in `<dc:title>`) — both ESP32 and
  nRF52840 targets pass.
- TASK-007 closed: skill scaffolding ships from day one —
  `.claude/skills/circuit/LICENSE` (MIT mirroring the host
  copyright), `.claude/skills/circuit/CHANGELOG.md` with the
  v0.1 stub, `docs/index.md` (install + "Hello, circuit"
  walk-through), `docs/components.md` (Phase 1 library reference
  and profile-authoring guide).
- ADR-0010 filed: MCU profiles describe the dev-board pinout
  with silicon metadata at the chip level — the dossier example
  used silicon pin names, but the dev-board shape is what the
  byte-identity gate needed.
- ADR-0011 filed: SVG regression test uses content-identity with
  matplotlib non-determinism normalised, not literal
  byte-identity — three mpl-injected fields prevent byte-equality
  even across two consecutive runs of the unchanged script.
- **EPIC-001 closed** — all 7 tasks done. Component library +
  schema delivered; Phase 1 of the dossier roadmap complete.

### Circuit skill (EPIC-002 — Renderer and Layout Engine)

- TASK-008 closed: `.claude/skills/circuit/netgraph.py` — typed
  `NetGraph` / `PinRef` / `NetMeta` data model derived from a
  validated `.circuit.yml`. Single shared contract between the YAML
  source and the three downstream consumers (ERC engine, layout
  kernel, netlist exporter) per ADR-0003. The three connection
  forms (`pins`, `path`, `bus`) flatten into one canonical
  representation; segment-naming for path nets is content-addressed
  for stable PCB-side names. `canonical_hash()` gives the
  hash-determinism gate that TASK-053's golden-hash CI contract will
  read.
- TASK-009 closed: `.claude/skills/circuit/layout_engine/kernel.py`
  — v0.1 deterministic placer. Canonical-slot table covers MCU /
  LED / resistor (LED-paired + pull-up) / button / decoupling cap /
  I²C sensor / header-jack. Incremental stability:
  topology-fingerprint per placement (SHA-1 of `(rule ID, canonical
  shape form)`) auto-invalidates on drift; `kept` placements freeze
  across runs. Adding one component produces a one-line diff in
  `layout.yml`. `EscalationError` carries the `no-canonical-rule`
  reason code for the Phase 2b trigger to count.
- TASK-010 closed: `.claude/skills/circuit/layout_engine/router.py`
  — Manhattan router. Orthogonal-only segments, L-shape (H→V)
  routing per consecutive pin pair, deterministic across runs.
  Crossings and intra-component-body intersections are *reported*
  (`RouterResult.crossings`, `intra_component_intersections`) for
  the rubric to consume — not avoided. Z-shape break enumeration
  deferred post-v0.1.
- TASK-011 closed:
  `.claude/skills/circuit/layout_engine/rubric.py` — v0.1
  structural rubric. Three blocking checks (`overlaps`,
  `labels_fit`, `wire_crossings`) plus two advisory metrics
  (`min_label_distance`, `density`). Each `Finding` names the
  failing check, severity, message, and the refs/nets involved so
  the diagnostic is actionable. Default wire-crossing threshold is
  0; configurable per-run for waiver paths.
- TASK-012 closed: `.claude/skills/circuit/renderer.py` — top-level
  pipeline orchestrator. CLI `--circuit / --layout / --out` with
  path-agnostic args. Halts on circuit-schema / kernel-escalation /
  rubric-failure with structured `RenderError` and non-zero exit;
  meta.yml is written on every path (success and failure) so the
  Phase 2b trigger has a corpus to read. v0.1 SVG is structural
  (every component has a `data-ref`, every wire is a polyline) so
  CI's structural-equality test from idea-001 §12 has stable
  inputs; rich Schemdraw glyphs are a follow-up.
- TASK-013 closed:
  `.claude/skills/circuit/schema/layout.schema.json` +
  `schema/layout_validator.py`. Enforces the slot vocabulary,
  `attach-index-redundant` invariant, `free`-slot `gx`/`gy`
  requirement, and the `topology-fingerprint` required field.
  Findings carry the same shape as the circuit-side validator
  (`check`, `severity`, `message`, `location`).
- TASK-014 closed: `data/{esp32,nrf52840}.{circuit,layout}.yml`.
  Both pairs translate the AwesomeStudioPedal pedal config
  faithfully (5 status LEDs, 5 buttons, USB-C power input);
  `.layout.yml` files are kernel-generated and validate against
  `layout.schema.json`.
- TASK-015 closed: cutover landed. `scripts/generate-schematic.py`
  and `tests/test_generator_byte_identity.py` deleted; the
  `full-pedal` fixture under `tests/fixtures/full-pedal/{esp32,nrf52840}/`
  carries the renderer's `expected.svg` + `expected.meta.yml`;
  `tests/test_renderer_staleness.py` is the structural-equality
  guard (idea-001 §12 cross-platform caveat — byte-identity is not
  safe across OSes); `docs/builders/wiring/<target>/main-circuit.svg`
  files re-rendered. The task body assumed a pre-existing CI
  staleness step targeting the old generator; none existed in this
  repo's lineage, so the cutover added a `pytest` test that runs in
  the existing CI step rather than fabricating a "retarget".
- TASK-016 closed: `.claude/skills/circuit/docs/circuit-yaml.md`
  and `.claude/skills/circuit/docs/layout.md` — skill-internal
  reference docs. `circuit-yaml.md` covers the three connection
  forms with worked examples, schema validation, and the Markdown
  `circuit` block preview. `layout.md` covers the slot vocabulary,
  the §5.3 dispatch table, the rubric (blocking + advisory), the
  meta.yml escalations enum (cross-linked to `meta.schema.json`),
  the overflow ladder, and the v0.1 known limitations.
- TASK-057 closed: `meta.yml.provenance.escalations` is the corpus
  the Phase 2b trigger reads. Renderer emits one entry per
  kernel-`EscalationError` (with `category` / `component` /
  `circuit` / `detail`) and one entry per blocking-rubric failure
  (`rubric-fail-{check}`); empty array on clean runs, never absent.
  Schema lives at `.claude/skills/circuit/schema/meta.schema.json`.
- TASK-058 closed: `scripts/check_phase2b_trigger.py` — aggregates
  `provenance.escalations` across every committed `*.meta.yml` via
  `git ls-files` and emits a JSON report on stdout + Markdown
  summary on stderr. Exits 0 unconditionally (observer, not gate).
  CI uploads the report as a `phase2b-trigger.json` build artifact
  on every PR.
- TASK-059 closed: `scripts/release_snapshot.py` consults the
  trigger and refuses to cut when `non_addressable_count > 0` AND
  every Phase 2b task (TASK-017..021) is still `open`. The
  refusal message is actionable (lists each Phase 2b task's
  current state + the exact `/ts-task-active TASK-017` command).
  `CS_PHASE2B_BYPASS="<reason>"` proceeds and appends to
  `.git/cs-phase2b-bypass.log`, mirroring the `CS_COMMIT_BYPASS`
  envelope.

### Tooling (EPIC-002 ride-alongs)

- `.claude/skills/circuit/schema/registry.py` `Profile` dataclass
  gained `category` / `pins_detail` / `metadata` fields so the
  layout kernel can dispatch on category without re-reading the
  source dicts.
- `.claude/skills/circuit/layout_engine/rubric.py`
  `DEFAULT_LABEL_BUDGET` raised from 4 to 8 grid units — typical
  ref names (`D_PWR`, `SW_SEL`, `R_SEL0`) outgrow the original
  budget without indicating a real readability problem.
- `.github/workflows/ci.yml` runs
  `scripts/check_phase2b_trigger.py` on ubuntu-latest and uploads
  the report via `actions/upload-artifact@v4`.
- `.claude/settings.json`: added
  `Bash(python scripts/check_phase2b_trigger.py:*)` to the
  allowlist; removed the now-stale `generate-schematic.py` entry.

### Circuit skill (EPIC-002 — Phase 2b AI placer)

Phase 2b landed in the same epic-run after a maintainer override of
ADR-0008's evidence-driven default — the design was already
specified in `idea-001.layout-engine-concept.md §7`, the
implementation cost was bounded by `--no-ai`'s opt-in shape, and the
context-switch cost of resuming Phase 2b months from now was deemed
higher than implementing while still mid-EPIC. The five tasks below
deliver the full v1 layout engine.

- TASK-017 closed:
  `.claude/skills/circuit/layout_engine/ai_placer.py` — the §7
  convergence loop. `converge()` runs a bounded loop (default 5
  iterations / 50k token cap) over an injected `LLMClient`
  Protocol; tests inject a `_FakeLLM` so the CI path never reaches
  the network per ADR-0002. The production `AnthropicClient`
  adapter is a thin SDK wrapper, lazy-imported. Reason codes:
  `converged`, `ai-cap-exceeded`, `ai-output-invalid`,
  `ai-frozen-violation`, `ai-unknown-region`,
  `ai-missing-component`, `ai-token-cap-exceeded`.
- TASK-018 closed: `--no-ai` (the default, ADR-0002-aligned) and
  `--ai` (explicit opt-in) CLI flags. Kernel gained
  `collect_escalations: bool = False` so the AI placer sees the
  full ambiguity set rather than the first one. Renderer's
  `_dispatch_ai_placer()` wires the LLMClient + rubric-check
  callback (router + rubric re-run on the proposed placements);
  AI-merged placements get a `sha1:ai-converged` topology
  fingerprint so the incremental-stability check (§8.4) can
  distinguish them from kernel placements.
- TASK-019 closed: `min_label_distance` and `density` promoted
  from advisory to blocking. Thresholds calibrated against the
  Phase 2a green corpus (75th-percentile floor per §10): both
  shipped circuits report `min_label_distance = 1` and
  `density = 0.1453`. Defaults are
  `DEFAULT_MIN_LABEL_DISTANCE_THRESHOLD = 1` and
  `DEFAULT_DENSITY_THRESHOLD = 0.5`. Pass `None` to either
  parameter to suppress (matches v0.1 advisory-only behaviour for
  pre-v1 fixtures).
- TASK-020 closed: `meta.yml.provenance.ai_invocations[]` block
  added — one entry per AI dispatch with `reason`, `iterations`,
  `input_tokens`, `output_tokens`, `components`. `ai_invoked` /
  `iterations` always written. `meta.schema.json` extended with
  the `aiInvocation` / `aiReason` sub-schemas and the
  `ai-placer-*` + v1 `rubric-fail-{min-label-distance, density}`
  category enums.
- TASK-021 closed: `.claude/skills/circuit/docs/layout.md` gained
  the full AI-placer section — invocation, input/output contracts,
  convergence behaviour, cost notes (5-iteration cap, 50k token
  cap, typical 1–3k input + 200–500 output tokens per call),
  `--no-ai` opt-out narrative, and the `meta.yml.provenance`
  field table.

**EPIC-002 fully closed** — all 16 in-scope tasks done (TASK-008..016 +
057..059 + 017..021). The v1 layout engine ships the AI placer plus
the trigger-gate plumbing that scheduled it.

### Skills (EPIC-002 ride-along)

- `/commit` SKILL.md: single-track bypass ask on unrelated hook
  failures. The verbatim message no longer offers "or fix the hook
  failure first" — that framing implied editing files outside the
  pathspec was a default option, which violates the
  parallel-session-safety contract. The user may override (refuse
  bypass and direct the agent to fix the unrelated file as a
  separate action), but that override is the user's call, not a
  default the agent surfaces.

Nothing else under `.claude/skills/circuit/` is in scope yet — see
[EPIC-003..006](docs/developers/tasks/EPICS.md), the remaining
governance gates in [EPIC-008](docs/developers/tasks/EPICS.md), and
the [EPIC-010](docs/developers/tasks/EPICS.md) relocation seed below.

### Planning (EPIC-010 seeded)

- IDEA-002 archived → EPIC-010 opened (Consolidate skill-resident
  Python into a `circuitsmith` package) with four supporting tasks:
  - TASK-076 — author ADR-0012 (supersede ADR-0007 "skill directory
    is the library")
  - TASK-077 — atomic relocation of `.claude/skills/circuit/` Python
    to `src/circuitsmith/` (single PR, no transitional aliases)
  - TASK-078 — update agent-facing skill surface (prompts + thin
    re-export shims, if any)
  - TASK-079 — repo docs sweep + CHANGELOG entry on landing
  EPIC-010 supersedes ADR-0007 via ADR-0012 and rewrites EPIC-006
  Phase 1.3 to publish `circuitsmith` to PyPI instead of extracting
  a standalone folder; TASK-045 retires. EPIC-010 gates EPIC-003.
  Branch will be `release/epic-010-circuitsmith-package`. Execution
  plan lives in the seeding idea file under `ideas/archived/`.

### Circuit skill (EPIC-010 — circuitsmith package relocation)

- Relocate library code from `.claude/skills/circuit/` to
  `src/circuitsmith/` and rename the importable package from
  `circuit` to `circuitsmith` (supersedes ADR-0007 via ADR-0012).
  The agent-facing surface (SKILL.md, `docs/`) stays at
  `.claude/skills/circuit/`; only the library leaves.
- TASK-076 closed:
  [ADR-0012](docs/developers/adr/0012-library-as-installable-package.md)
  authored — *library is an installable package; skill folder is
  the agent-facing surface*. ADR-0007 status flipped to
  `Superseded by ADR-0012` with a `## Supersession` section
  forward-linking to the new ADR.
  [EPIC-006](docs/developers/tasks/active/epic-006-circuit-skill-packaging.md)
  rewritten in place: Phase 7 reframed as PyPI publication
  (`python -m build`, trusted publishing, `RELEASING.md`);
  TASK-043 / TASK-044 / TASK-045 retired with closure notes
  (standalone-skill-repo extraction is obsolete under ADR-0012);
  Phase 6 → Phase 7 hard prereq dropped (soft "real-circuit use"
  gate survives on the `0.1.0.dev0 → 0.1.0` version bump only).
  New
  [TASK-080](docs/developers/tasks/open/task-080-publish-circuitsmith-to-pypi.md)
  covers the publication mechanics.
  [TASK-050](docs/developers/tasks/open/task-050-boundary-import-contract-test.md)
  scope updated — boundary is now `src/circuitsmith/`.
- TASK-077 closed: atomic relocation. `netgraph.py`, `renderer.py`,
  `components/`, `schema/` moved into `src/circuitsmith/`;
  `layout_engine/` renamed to `layout/` (the `_engine` suffix
  made sense inside a skill folder, not as a top-level package
  surface). New `__init__.py` with `__version__ = "0.1.0.dev0"`;
  empty `render/` and `export/` placeholders for EPIC-002 / EPIC-004.
  Imports rewritten across `src/circuitsmith/**/*.py` and
  `tests/**/*.py`. `tests/conftest.py` deleted — the `sys.path`
  splice is obsolete under `pip install -e .`. `pyproject.toml`
  flipped to src-layout discovery
  (`[tool.setuptools.packages.find] where = ["src"]`) +
  `[tool.setuptools.package-data] "circuitsmith.schema" = ["*.json"]`
  so the JSON schemas ship inside the wheel. Pytest 305/305 green
  after the rewrite. `python -m build` produces
  `circuitsmith-0.1.0.dev0-py3-none-any.whl` with all three
  `schema/*.json` files included.
- TASK-078 closed: agent-facing surface aligned. `from circuit.*`
  → `from circuitsmith.*` in `.claude/skills/circuit/docs/index.md`
  and `components.md`. `.claude/codeowners.yaml` patterns retargeted
  from `.claude/skills/circuit/...` to `src/circuitsmith/...` for
  the three bound files (`netgraph.py`, `schema/*.json`,
  `erc_engine.py`). `co-netgraph`, `co-schema`, `co-erc-engine`
  SKILL.md frontmatter descriptions and invariant ADR references
  updated. Skill shim `.py` files deferred (Phase 3.3 of the
  idea-002 plan).
- TASK-079 closed: repo docs sweep. `ARCHITECTURE.md` module table
  retargeted; Section 4 (decoupling seams) renamed *Package
  portability* and points at ADR-0012. `TESTING.md` Phase 7 language
  shifted from folder extraction to PyPI publication. `CI_PIPELINE.md`
  portability_lint invocations now point at `src/circuitsmith`.
  `CODE_OWNERS.md` codeowners.yaml pattern example retargeted.
  `AUTONOMY.md` definition-of-done portability bullet retargeted.
  `scripts/README.md` regenerated to pick up the
  `portability_lint.py` docstring change. Library-code references
  to the old path are gone from the named in-scope files;
  agent-facing references (`SKILL.md`, `docs/`) stay at
  `.claude/skills/circuit/`.
- Tooling: `scripts/portability_lint.py` now lints
  `src/circuitsmith/` (rule set unchanged); `scripts/pre-commit`
  triggers the portability check on `^src/circuitsmith/` staged
  paths; `scripts/check_phase2b_trigger.py` docstring schema path
  retargeted.
- **EPIC-010 closed** — the `circuitsmith` package now lives at
  [`src/circuitsmith/`](src/circuitsmith/) as a first-class
  installable artefact, and EPIC-003 (ERC engine) is unblocked to
  open against this layout. PyPI publication itself lands later in
  EPIC-006 / TASK-080.

### Circuit skill (EPIC-003 — ERC Engine and Rule Catalog)

- TASK-022 closed: `src/circuitsmith/erc_engine.py` ships with all 13
  active predicates (S1–S3 structural, E1–E10 electrical) plus S4 / S5
  sentinel entries in `CHECK_TABLE` so schema-validation findings
  surface through the same pipeline. Engine is CLI-invokable
  (`python -m circuitsmith.erc_engine --circuit …`) and importable from
  the renderer; both code paths produce identical findings on the same
  input. Three-level severity overrides (`meta.erc`, per-component
  `erc:`, per-net `erc:`) resolved per the dossier's specificity +
  cross-component most-severe-wins rules. Side-effect: every shipped
  component profile now carries `metadata.kind` (the semantic
  discriminator ERC keys on) so predicates never read `.category` —
  the "category keys layout, not semantics" invariant is now lintable.
- TASK-023 closed: ERC integrated into `renderer.py` at the canonical
  pipeline position (post-schema, pre-kernel). ERROR-level findings
  abort with exit code 1 (distinct from schema/kernel/rubric exit 2);
  WARNING-level findings (E9 on v0.1) land in
  `RenderResult.erc_findings` for the report writer but do not abort.
- TASK-024 closed: `src/circuitsmith/knowledge/rules.json` seeded with
  15 catalog entries (one per shipped check). Each entry carries
  `rule`, `explanation`, `heuristic`, `source_of_truth`, `keywords`,
  `enforced_by`. All prose is original English reformulation from
  elektronik-kompendium.de, manufacturer datasheets, or
  allaboutcircuits.com — no copy-paste from sources. Every heuristic
  carries the precision disclaimer.
- TASK-025 closed: `src/circuitsmith/knowledge/validate_catalog.py`
  CI-runnable validator with the five checks specified in the dossier
  (format, `enforced_by` consistency, heuristic disclaimer,
  `category`-invariant lint, URL reachability). `CS_CATALOG_OFFLINE=1`
  skips URL checks for fast-CI lanes.
- TASK-026 closed: `src/circuitsmith/knowledge/BACKLOG.md` is the
  prioritised queue for the remaining 15–35 educational rules toward
  the dossier's 30–50 target, organised by category and priority with
  the authoring workflow inline.
- TASK-027 closed: `src/circuitsmith/erc_report.py` produces the
  catalog-enriched Markdown report. Every non-OK finding gets a
  Why / Senior's tip / Source block sourced from the catalog row whose
  `id` matches the check code — strict lookup, no fuzzy match, no LLM
  in the loop. A finding without a matching catalog row raises
  `CatalogLookupError`.
- TASK-028 closed: `docs/builders/wiring/{esp32,nrf52840}/erc-report.md`
  generated by the renderer and committed. Each report includes a
  "Pending promotions" block documenting E9's WARNING → ERROR transit
  once the `diode` category lands. The renderer gained an
  `--out-erc-report` CLI flag.
- TASK-029 closed: CI gains three gates — staleness guard for
  `erc-report.md`, ERROR-level ERC gate, catalog validation —
  implemented as `scripts/check_erc_reports.py` plus the
  `circuitsmith.knowledge.validate_catalog` module run with
  `CS_CATALOG_OFFLINE=1` on per-PR. The pre-commit hook mirrors both
  gates and now prefers `.venv/bin/python` over `python3` so the
  package's runtime deps (`ruamel.yaml`) are reachable.
  `Bash(python scripts/check_erc_reports.py:*)` added to the
  permission allow-list.
- TASK-030 closed: `.claude/skills/circuit/docs/erc-checks.md` is the
  per-check reference contributors read when an ERC finding surfaces
  on their PR. One section per code (S1–S5 + E1–E10) covering trigger,
  meaning, severity, suppression (with valid `.circuit.yml` snippets),
  and a cross-reference to the catalog row. The skill index points at
  the new reference.
- **EPIC-003 closed** — topology-only ERC, source-linked rule catalog,
  catalog-enriched reports for both shipped targets, CI gates, and a
  per-check contributor reference. The skill is now a "senior
  designer" mentor in the sense the dossier promised: every finding
  carries a teaching block, every block links to a curated source.
