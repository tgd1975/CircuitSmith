# IDEA-001 dossier gap analysis vs shipped 0.1.0

Working artefact for [EPIC-015](tasks/active/epic-015-dossier-gap-analysis.md).
The eight sub-tables below walk the nine
[archived IDEA-001 dossier files](ideas/archived/) section by section
against the shipped 0.1.0 codebase. Each row carries one of four bucket
assignments:

1. **Shipped in 0.1.0 as specified** — close the loop, no follow-up.
2. **Shipped in 0.1.0 with reduced scope** — note the delta; verdict is
   either "fine as-is" or a spawned IDEA link.
3. **Deferred by design, gate not yet tripped** — record the gate
   condition + the evidence that keeps it closed.
4. **Deferred by design, gate now tripped** — spawn a follow-up IDEA-NNN.

Underscore-prefixed so the indexes skip it (mirrors TASK-102's
`_doc-audit-inventory.md`). The file archives in place when EPIC-015
closes — the analysis is the historical record of the walk, not an
evolving spec.

## Orientation notes (TASK-134)

- **Rule catalog:** `src/circuitsmith/knowledge/rules.json`. Note the
  path differs from the dossier's sketched `.claude/skills/circuit/knowledge/rules.json` —
  the catalog moved into the shipped Python package.
- **Escalations corpus:** `provenance.escalations` lives in each
  rendered circuit's `meta.yml` sidecar. Five gallery circuits ship
  with sidecars: `voltage-divider`, `common-emitter-amplifier`,
  `555-monostable`, `opamp-non-inverting-buffer`, `multi-page-split`.
  All five carry `escalations: []`. No tutorial / test fixture
  emits a `meta.yml` with a non-empty escalations list.
- **Phase 7 status snapshot:** `circuitsmith` v0.1.0 is on PyPI (per
  `pyproject.toml`); `.claude/skills/circuit/` is present in-repo
  with `SKILL.md` + `docs/` + `LICENSE` + `CHANGELOG.md` and is
  consumed by-copy elsewhere. The skill directory was not extracted.

## Phase plan (idea-001-circuit-skill.md)

| Phase | Bucket | Verdict / evidence / spawned IDEA |
|---|---|---|
| Phase 1 — Component library + Schema | 1 | Shipped per EPIC-001. `src/circuitsmith/components/{mcus,passives,connectors,sensors,actives,ics}.py` + `src/circuitsmith/schema/circuit.schema.json`. Note that `actives.py` and `ics.py` are post-dossier additions from EPIC-014 — the dossier's day-one library was {mcus, passives, connectors, sensors}. |
| Phase 2a — Renderer + v0.1 kernel | 1 | Shipped per EPIC-002. Renderer at `src/circuitsmith/renderer.py`, kernel + router under `src/circuitsmith/layout/`, `layout.schema.json` shipped, full-pedal cutover deliverable retired (see EPIC-002 closeout — the cutover concept landed differently in CircuitSmith because the predecessor `generate-schematic.py` lived in AwesomeStudioPedal, not here). |
| Phase 2b — AI placer (contingent) | 2 | **Correction to first-pass walk.** AI placer code shipped as scaffolded module: `src/circuitsmith/layout/ai_placer.py` (582 lines: `converge()` loop, `AnthropicClient` seam, full §7 reason-code taxonomy `converged`/`ai-cap-exceeded`/`ai-output-invalid`/`ai-frozen-violation`/`ai-unknown-region`/`ai-missing-component`/`ai-token-cap-exceeded`). Renderer wires it behind a `--use-ai-placer` CLI flag with default `False` (`src/circuitsmith/renderer.py:104,953,963`). The dossier's "ships on evidence" framing is faithfully implemented as **scaffold present, default off, gate trips flip the default** — recorded in ADR-0008 (Phase 2b on evidence) and operationalised by `scripts/check_phase2b_trigger.py` (TASK-058) + the release script's gate check (TASK-059). Default-off state is the corpus evidence: `escalations: []` in all 5 shipped gallery `meta.yml` sidecars. EPIC-014's 9 new kernel rules (IDs 11–19) absorbed every kernel-failure mode that surfaced during the gallery work — confirms the dossier's "extend §5.3 rather than promote to AI" routing in practice. Fine as-is. |
| Phase 3 — ERC + Rule catalog | 1 | Shipped per EPIC-003 (15 codes: S1–S5 + E1–E10). EPIC-014 extended catalog to 27 codes (S1–S7 + E1–E22) — out of dossier scope but worth noting for context. Rule catalog at `src/circuitsmith/knowledge/rules.json`; `validate_catalog.py` runs in CI per `.github/workflows/ci.yml` line 97. E9 still WARN — gates on TASK-135's diode-category verdict (handled in the components walk). |
| Phase 4 — BOM + Netlist exporters | 1 | Shipped per EPIC-004. `src/circuitsmith/export/` carries the BOM + netlist exporters; outputs committed for shipped circuits. Three-column PartsLedger BOM is dossier's "out-of-scope-for-now" extension and now lives in open IDEA-011 — handled in TASK-139's exporters walk row, not here. |
| Phase 5 — Markdown integration | 2 | Shipped per EPIC-005 via the CI-rewrite path (`src/circuitsmith/markdown.py` + `.github/workflows/generate-circuits.yml`). The dossier's "ordering with IDEA-022" branch (drop the workflow, ship as `pymdownx.superfences` formatter) never applied because IDEA-022 (MkDocs site) lived in AwesomeStudioPedal and did not migrate to CircuitSmith on the repo split. The CI-rewrite path is the steady state; the alternative formatter path is dead. Reduced scope = the dossier's two-path branch collapses to one path. Fine as-is, no follow-up. |
| Phase 6 — Circuit skill | 1 | Shipped per EPIC-006. `.claude/skills/circuit/SKILL.md` + the five acceptance tests landed (TASK-041 ran them). |
| Phase 7 — Standalone repo extraction | 3 | Deferred-by-default, **not** redundant. The PyPI ship (TASK-080) packaged the `circuitsmith` Python module v0.1.0, not the `.claude/skills/circuit/` skill directory. The skill is still in-repo, consumed by-copy elsewhere. The dossier's prerequisite ("Phase 6 acceptance test passes and the skill has been used on at least one real circuit addition in this project") is satisfied by EPIC-014's gallery work (multiple new circuits authored via the skill). The gate is now reframed: "extract when the skill stabilises and developers feel friction maintaining the by-copy pattern" — that friction has not surfaced yet. Cross-link to TASK-141's skill-packaging row. |

## Components (idea-001.components.md)

| Dossier §5.3 row | Bucket | Verdict / evidence / spawned IDEA |
|---|---|---|
| **Day-one library** (15 profiles: ESP32, nRF52840, RESISTOR, CAPACITOR, LED, PUSHBUTTON, PIEZO, USB_C, DC_BARREL, MONO_JACK, STEREO_JACK, PIN_HEADER_{2,3,4,6,8}, SCREW_TERMINAL_{2,3}, BME280, SSD1306) | 1 | Shipped per EPIC-001. `passives.py` + `mcus.py` + `connectors.py` + `sensors.py` cover all 15 day-one profiles with the dossier-specified category keys. EPIC-014 added two further category families on top (`actives.py` for transistors, `ics.py` for 555 + op-amp) — out of dossier day-one scope, noted for context. |
| Generic diode / Schottky (backlog row 1) | 3 | Gate not tripped. `actives.py` ships only `bjt_npn` + `bjt_pnp` (EPIC-014 TASK-120) — no diode profile, no `category: diode` row in `§5.3` / `layout.schema.json`. E9 catalog entry exists (`src/circuitsmith/knowledge/rules.json`) but `erc_engine.py:103` records the v0.1 WARNING-not-ERROR gate inline, and line 936 emits "(WARNING at v0.1 pending the `diode` category.)" — gate still wired. The dossier's "promote E9 to ERROR once diode lands" condition holds. |
| 3-pin linear regulator (AMS1117-3.3, LM7805) (backlog row 2) | 3 | Gate not tripped. No `regulator` category in any `components/*.py`; no `category: regulator` in `layout.schema.json`. Dossier-stated priority "High — ubiquitous on maker boards" still pending. Re-evaluate when a gallery or builder-doc circuit needs a regulated supply. |
| Potentiometer / trimpot (backlog row 3) | 3 | Gate not tripped. No `pot` row, no profile. Dossier-stated priority "High — maker-UI workhorse" still pending. |
| DHT22 / DHT11 — 1-wire digital sensor (backlog row 4) | 3 | Gate not tripped. No `digital-sensor` row added and `i2c-sensor` not renamed to `i2c-peripheral`. Priority "Medium" in the dossier; status unchanged. |
| N-MOSFET / NPN BJT as a switch (backlog row 5) | 2 | Reduced scope: **BJT half shipped, MOSFET half not**. EPIC-014 TASK-120 + ADR-0015 added `bjt_npn` + `bjt_pnp` with per-pin `role:` annotation (`base`/`collector`/`emitter`) — the dossier's "gate-drain-source / base-collector-emitter roles" landed for BJTs only. Kernel rules `RULE_BJT_TO_GND` (id 15) and `RULE_RESISTOR_WITH_BJT` (id 16) handle base-drive resistors; TASK-129 added `RULE_BJT_LOAD` (id 18) and `RULE_BJT_DEGENERATION` (id 19) for collector/emitter resistors. N-MOSFET parts not shipped — the dossier's "switch" semantic is BJT-only in 0.1. Fine as-is; MOSFETs can land on the same pin-role pattern when a circuit needs them. No follow-up. |
| Rotary encoder (backlog row 6) | 3 | Gate not tripped. No `encoder` row, no profile. Priority "Medium"; status unchanged. |
| WS2812 / addressable LED chain (backlog row 7) | 3 | Gate not tripped — and the dossier itself flagged this as "likely out of scope per layout §2 non-goals" (chained data-bus topology rather than a net). Layout §2 still excludes chained-data topologies. Bucket 3 with the verdict that the gate is "would require a layout topology generalisation we don't intend to ship". |
| Servo / motor header (backlog row 8) | 3 | Gate not tripped. Could ride on `PIN_HEADER_3` (already shipped) once a user authors a specific profile, or could spawn a `servo-header` row. No real demand surfaced; priority "Low"; status unchanged. |

Cross-reference: archived [IDEA-009](../developers/ideas/archived/idea-009-active-device-profiles-and-multi-page-renderer.md)
already covered the BJT / op-amp / 555 active-device space and was elevated
into EPIC-014 — the rows above reflect that closure. The diode-category
row is **not** in IDEA-009's scope (IDEA-009 focused on active devices
that EPIC-012's gallery needed, not on the polarity-protection passive
backlog), so the diode gate remains independently open.

## YAML format (idea-001.yaml-format.md)

| Schema construct | Bucket | Verdict / evidence / spawned IDEA |
|---|---|---|
| Top-level `meta` block | 1 | Shipped per EPIC-001. `circuit.schema.json` `$defs.meta` requires `title` + `target`; permits `config`, `aliases`, `erc` plus open extension via `additionalProperties: true`. |
| `meta.erc` per-check severity map | 1 | Shipped. Schema constrains keys to `^[ES][0-9]+$` and values to `off`/`warn`/`error` (`additionalProperties: false`). Note: the EPIC-014 TASK-127 cross-page-threshold knob does **not** ride under `meta.erc` (would fail the pattern); it lives elsewhere — out of dossier scope, no row. |
| `meta.aliases` map (GPIO label propagation) | 1 | Shipped per dossier shape. Pre-pin-alias lookups through the ERC / BOM / renderer use it transparently. KiCad netlist deliberately ignores it per dossier §Net naming. |
| `meta.config` external alias file | 1 | Shipped. The "file resolves" check runs in the post-schema validator (JSON Schema can't express filesystem existence) — matches the dossier's validation-boundary note. |
| Top-level `components` map | 1 | Shipped. Schema enforces ref pattern `^[A-Za-z_][A-Za-z0-9_]*$` and `type:` pattern `^[a-z][a-z0-9_]*/[a-z0-9_]+$`. The dossier's broader "any pattern" framing tightened to a single literal form ("`category-namespace/profile-name`") — verdict captured implicitly in EPIC-001, not a reduction. |
| Per-component `type` / `label` / `value` / `color` keys | 1 | Shipped. `$defs.component` lists exactly these four, plus `additionalProperties: true` for forward-compatibility (carries the per-component `meta:` block authors can attach for ERC overrides). |
| Top-level `connections` array (oneOf the three forms) | 1 | Shipped. Schema enforces "exactly one of `pins`, `path`, or `(bus + backbone)`" via `oneOf` with mutual-exclusion `not` clauses (lines 88–117). Matches the dossier's "no fourth form needed" stance. |
| Form 1 — `pins:` unordered set | 1 | Shipped. The dossier's "shortest path drawn by renderer" rendering contract is in `src/circuitsmith/renderer.py` and the router. |
| Form 2 — `path:` ordered sequence + segment counting rule | 1 | Shipped. The flattener implements "group consecutive same-component tokens into one node; segments = nodes − 1" verbatim (`src/circuitsmith/netgraph.py:flatten` for the algorithm). Content-addressed segment names use the `<net>__<RefA>_<pinA>__<RefB>_<pinB>` convention from the dossier. |
| Form 2 — net-merge at `path:` endpoints | 1 | Shipped per dossier (symmetric leading/trailing net-name token merging). Standard idiom on all five gallery circuits. |
| Form 3 — `bus:` backbone + taps | 1 | Shipped. Schema's third `oneOf` branch requires `bus: true` and a non-empty `backbone`. `taps` are pin strings (the long-form `{ ref, layout: { position } }` per-tap entry the dossier explicitly retired never landed). |
| Net-level `pull:` (`firmware` / `hardware_up` / `hardware_down`) | 1 | Shipped. Schema enum `["firmware", "hardware_up", "hardware_down"]` (line 81). ERC E1 reads this as its source of truth per the dossier. |
| Net-level `role:` (scalar or `REF.PIN`-keyed map) | 1 | Shipped. Schema's `$defs.role` is a `oneOf` between scalar enum (`in`/`out`/`bidir`) and a pattern-keyed map. Schema cannot enforce "scalar form invalid when net has 2+ GPIO pins" or "key must be GPIO-typed" — both run in the post-schema validator, matching the dossier's validation-boundary note. |
| `segment_names` length-equals-flattened-segments check | 1 | Shipped per dossier. JSON Schema permits any-length array; post-schema validator enforces the `nodes − 1` count with a citation of expected vs actual count. |
| Net-name syntax (`^[A-Za-z0-9_+\-]+$` plus "at least one letter") | 1 | Shipped. Schema pattern enforces the character class; the "at least one letter" constraint runs in the post-schema validator per the dossier's note that JSON Schema draft 2020-12 lookaround isn't universally supported. |
| Component-ref syntax (stricter form `^[A-Za-z_][A-Za-z0-9_]*$`) | 1 | Shipped. Same syntax used for sub-block and instance names too — see post-dossier note below. |
| Markdown ` ```circuit ` integration (CI rewrite + `show_source` flag + hash-based staleness) | 1 | Shipped per EPIC-005. `src/circuitsmith/markdown.py` carries the `find_blocks`/`compute_hash`/rewrite pipeline; `.github/workflows/generate-circuits.yml` runs it on push. The dossier's MkDocs+`pymdownx.superfences` alternative is dead in this repo (IDEA-022 didn't migrate from AwesomeStudioPedal) — confirmed in TASK-134's Phase 5 row. |
| YAML loader pinned to `ruamel.yaml` | 1 | Shipped. `pyproject.toml` carries the dependency; the round-trip regression test referenced in the dossier exists in `tests/`. |
| `inputs:` / `outputs:` pin-alias form (sub-block port naming) | n/a | **Not in dossier scope.** The dossier proposes `meta.aliases` (component-pin → label rename), which shipped as documented. The `inputs:`/`outputs:` pin-alias form named in TASK-136's acceptance criterion is a misattribution — it is the IDEA-008 frozen-decisions table item from EPIC-014, where it lost to the `ports: { name: REF.PIN }` named-port map. Out of dossier scope; no row to bucket. |

**Post-dossier additions (out of scope, noted for context).** The shipped
schema also carries `sub-blocks` (`$defs.subBlocks` / `$defs.subBlock` /
`$defs.ports`) and `instances` (`$defs.instances` / `$defs.instance`) plus
the S6/S7 post-schema checks for nested-sub-block rejection and
undeclared-instance reference. These are EPIC-014 (IDEA-008) additions on
top of the dossier shape — see archived
[IDEA-008](../developers/ideas/archived/idea-008-first-class-sub-blocks-and-non-led-kernel-rules.md)
for the contract. No row above because the dossier didn't sketch this
surface; cross-link rather than re-derive.

## Layout engine (idea-001.layout-engine-concept.md)

| Subsystem | Bucket | Verdict / evidence / spawned IDEA |
|---|---|---|
| Slot vocabulary (§4: anchor, column/row regions, path-of, bus-, pin-symbol-, attached-to, free) | 1 | Shipped per EPIC-002. The nine canonical slots from the dossier all appear in `layout.schema.json` and `src/circuitsmith/layout/kernel.py`. EPIC-014 (TASK-115) extended the schema with sub-block-aware semantics on top of this vocabulary — out of dossier scope, noted for context only. |
| Kernel canonical-slot table (§5.3) | 1 | Shipped per EPIC-002. `src/circuitsmith/layout/kernel.py` (1452 lines) carries the rule-table dispatch. Dossier seeded ~10 rules; EPIC-014 added 9 more (IDs 11–19: `RULE_RC_LOW_PASS`/`RC_HIGH_PASS`/`CC_DECOUPLING`/`RR_VOLTAGE_DIVIDER`/`BJT_TO_GND`/`RESISTOR_WITH_BJT`/`GENERIC_IC`/`BJT_LOAD`/`BJT_DEGENERATION` per the EPIC-014 implementation log). Current count is **19 user-writable rules** — see TASK-140's rule-catalog row for the ceiling discussion. |
| Manhattan router (§9 — orthogonal routing only) | 1 | Shipped per EPIC-002. `src/circuitsmith/layout/router.py` (302 lines). Diagonal routing remains an explicit non-goal per dossier §2. |
| Readability rubric (§10 — overlaps, labels_fit, wire_crossings) | 1 | Shipped per EPIC-002. `src/circuitsmith/layout/rubric.py` (318 lines). The "structural rubric only at v0.1; signal-flow rubric deferred to v1" framing from dossier §10 is faithful — the per-pin `direction` infrastructure is present (TASK-136's `role:` walk) and would feed the signal-flow rubric without a schema break if it ever ships. No follow-up — the deferred check earns its keep via schema-enforced direction implications even without the rubric. |
| AI placer (§7) | n/a | Already bucketed in Phase plan row above (Phase 2b: bucket 2, shipped as scaffolded opt-in `--use-ai-placer` flag, default off, gate per ADR-0008 controls the default flip). Cross-reference, not double-counted here. |
| Topology fingerprint (§8.4 — rule-ID hashing into layout.yml) | 1 | Shipped per EPIC-002. Each `layout.yml` carries the topology fingerprint; layout-validator's "fingerprint mismatch" path forces a kernel re-run on rule-ID bumps. EPIC-014's TASK-124 confirmed page partition survives fingerprint mismatches because page is user-authored rendering metadata, not topology-fingerprint input. |
| `meta.yml` sidecar (§11 — rubric verdict, provenance, escalations) | 1 | Shipped per EPIC-002 (renderer emits it after layout). All 5 shipped gallery sidecars conform to the dossier-stated shape: `rubric:`, `provenance.escalations:`, `layout.total:` (now flat-component count post-EPIC-014 TASK-119), `placements:`. EPIC-014 TASK-118 added an `instances:` block for sub-block grouping — out of dossier scope. |
| `layout.yml` schema (§4 — slot-per-component dictionary) | 1 | Shipped per EPIC-002 at `src/circuitsmith/schema/layout.schema.json`. The dossier-stated decoupling — `layout.yml` carries all geometric decisions, `circuit.yml` carries none — holds in 0.1; the schema rejects geometric fields in `circuit.yml` by construction (only the three `oneOf` connection forms allowed). |
| Cutover process (§16 — `data/config.json` → `.circuit.yml` migration) | 2 | **Shipped by elimination, not by execution.** The dossier's cutover was a one-PR migration of AwesomeStudioPedal's `generate-schematic.py` + `data/config.json` into the new YAML pipeline. CircuitSmith is a fresh greenfield repo (extracted from ASP at concept stage, per CLAUDE.md), so no `generate-schematic.py` cutover ever happened *in this repo* — the dossier's predecessor artefacts live in ASP and never crossed over. Reduced scope = the migration step disappeared into the repo-split itself. Fine as-is, no follow-up. |
| Phase 2b trigger gate (§17.1 — escalation-evidence release gate) | 1 | Shipped per ADR-0008 (Phase 2b on evidence, 2026-05-12) and the operational scripts `scripts/check_phase2b_trigger.py` (TASK-058) + release-script gate check (TASK-059). The threshold is documented in the dossier and the script; release script refuses to tag a Phase 2 release if the gate trips. Current state: gate green (corpus has `escalations: []` across 5 circuits). |

**Post-dossier additions (out of scope, noted for context).** Multi-page
rendering (`pages:` partition in `layout.yml`, multi-page render driver,
cross-page label glyphs, cross-page ERC checks E19–E22) shipped via EPIC-014
TASK-124..127. The dossier explicitly lists "Multi-page schematics" as a §2
non-goal — so multi-page is a deliberate scope expansion beyond the
dossier's v1 contract, not a dossier deliverable. Cross-link to EPIC-014;
no row to bucket.

## ERC engine (idea-001.erc-engine.md)

15 rows: S1–S5 + E1–E10. Severity defaults are pulled directly from
`src/circuitsmith/erc_engine.py:CHECK_TABLE` (lines 59–110) and
cross-checked against the per-code entries in
`src/circuitsmith/knowledge/rules.json`. EPIC-014's E11–E22 are
out-of-dossier scope and listed under "Post-dossier additions"
below.

| Check | Shipped? | Severity matches dossier? | Bucket | Notes |
|---|---|---|---|---|
| **S1** — Unconnected required pin | Yes | Yes (ERROR) | 1 | Detection runs in `erc_engine.py` per spec. Per-instantiated-component evaluation. |
| **S2** — Dangling net | Yes | Yes (ERROR) | 1 | Always-on. |
| **S3** — Duplicate net name | Yes | Yes (WARNING) | 1 | Always-on. |
| **S4** — Unknown reference | Yes (via schema) | Yes (ERROR) | 1 | Schema-validator emits this code; CHECK_TABLE entry preserves the row for the ERC report and the catalog validator (ADR-0006). Matches dossier intent. |
| **S5** — Unknown pin | Yes (via schema) | Yes (ERROR) | 1 | Same shape as S4 (schema-validator surfaces it, CHECK_TABLE row for report uniformity). EPIC-014 TASK-121 widened S5 to accept `alt:`-listed pin aliases (e.g. `T1.GND` resolves to `T1.1` for the 555) — that's a strict expansion, not a regression. |
| **E1** — Floating input | Yes | Yes (ERROR) | 1 | Source of truth for input-pull verdict is `pull:` net key, per dossier §E1. Hybrid `role:` map narrows direction on GPIOs first. Missing-role on a `bidir` GPIO downgrades E1 to WARNING with an explicit note in the finding message — matches dossier §E1 notes. |
| **E2** — LED missing resistor | Yes | Yes (ERROR) | 1 | Every LED in the circuit. |
| **E3** — LED resistor out of range | Yes | Yes (WARNING) | 1 | Calculates `(VCC - v_forward) / R` using `metadata.v_forward_by_color[color]` per the dossier; falls back to `v_forward_default` when `color:` is missing or unrecognised. |
| **E4** — INPUT_ONLY pin driven | Yes | Yes (ERROR) | 1 | Reads `direction` not `category`. |
| **E5** — Strapping pin without pull | Yes | Yes (WARNING) | 1 | Strapping-pin sets are profile-declared via `is_strapping: True`; the schema's "no internal pull on strapping pin" check (TASK-136 row) is the upstream guard. |
| **E6** — Missing decoupling cap | Yes | Yes (WARNING) | 1 | Dossier flagged this as "shipped but dormant on current circuits — activates as soon as a qualifying component (non-MCU IC) appears". EPIC-014 added op-amp and 555 ICs; E6 is now active on those circuits and producing real findings on `555-monostable` and `opamp-non-inverting-buffer` gallery entries. No change to severity; activation is the expected behaviour. |
| **E7** — I2C missing pull-up | Yes | Yes (WARNING) | 1 | Activates when `func: [I2C_SDA]` or `[I2C_SCL]` is tagged on a pin. Dossier-shipped "shipped but dormant" disposition; activates on the BME280 + SSD1306 profiles. |
| **E8** — Current budget exceeded | Yes | Yes (WARNING) | 1 | Reads MCU `max_gpio_current_ma` + `max_total_current_ma` from profile metadata; sums declared LED currents. |
| **E9** — Reverse-polarity unprotected | Yes (with caveat) | **No — shipped as WARNING, not ERROR** | 2 | The dossier specifies E9 as ERROR but **explicitly gates the ERROR-promotion on the `diode` category landing in §5.3** ([erc-engine §E9 note](../developers/ideas/archived/idea-001.erc-engine.md)). The `diode` category has not landed (see TASK-135 components row), so E9 remains WARNING per `erc_engine.py:103` and `:936`. This is the dossier's own staging plan; the severity mismatch is intentional, gate-driven, and matches the dossier's stated v0.1 disposition. Bucket 2 because the *currently-shipped severity* deviates from the dossier's *terminal* severity, but the deviation is the dossier-stated v0.1 outcome. Cross-link to TASK-135 diode-category row. No follow-up. |
| **E10** — Pin conflict | Yes | Yes (ERROR) | 1 | Any pin appearing in more than one declared net. |

**Post-dossier additions (out of scope, noted for context).** EPIC-014
added 12 new codes — S6/S7 (sub-block schema validation, TASK-117),
E11–E15 (sub-block ERC + voltage-divider ambiguity, TASK-117/TASK-114),
E16–E18 (active-device ERC: BJT role, op-amp floating supply,
555 pin-naming drift, TASK-123), E19–E22 (cross-page rules,
TASK-127). Catalog now at 27 codes total; CHECK_TABLE grew from
15 → 27. Severity overrides via `meta.erc.<code>: off|warn|error`
shipped per dossier; `meta.erc.cross-page-threshold` is a separate
EPIC-014 knob outside the `meta.erc` schema (see TASK-136's YAML
walk note).

## Exporters (idea-001.exporters.md)

| Exporter row | Bucket | Verdict / evidence / spawned IDEA |
|---|---|---|

<!-- TASK-139 extends this sub-table. -->

## Rule catalog (idea-001.rule-catalog.md)

| Aspect | Bucket | Verdict |
|---|---|---|

<!-- TASK-140 extends this sub-table. 3 rows expected (one per interpretation of the 30–50 ceiling). -->

## Skill packaging (idea-001.skill-packaging.md)

| Acceptance test / row | Bucket | Verdict / evidence / spawned IDEA |
|---|---|---|

<!-- TASK-141 extends this sub-table. -->

## Cross-repo references (TASK-142)

ASP IDEA-011 / IDEA-018 / IDEA-019 / IDEA-022 verdicts land here on close-out.

| Dossier ASP reference | Verdict | Notes |
|---|---|---|

<!-- TASK-142 fills this sub-table after the per-file walks. -->
