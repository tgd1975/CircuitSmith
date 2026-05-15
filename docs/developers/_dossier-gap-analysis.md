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
| Phase 2b — AI placer (contingent) | 3 | Gate not tripped. Trigger condition per dossier §17.1: "non-zero kernel-failure count on a circuit whose category looks routine, that a §5.3 table addition cannot retire." Evidence: `escalations: []` in all 5 shipped gallery `meta.yml` sidecars (voltage-divider, common-emitter-amplifier, 555-monostable, opamp-non-inverting-buffer, multi-page-split). EPIC-014's renderer-v2 wave shipped 9 new kernel rules (IDs 11–19) absorbing every kernel-failure mode that surfaced during the gallery work — confirms the dossier's "extend §5.3 rather than promote to AI" routing. Re-evaluate at the next release-prep review. |
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

<!-- TASK-136 extends this sub-table. -->

## Layout engine (idea-001.layout-engine-concept.md)

| Subsystem | Bucket | Verdict / evidence / spawned IDEA |
|---|---|---|

<!-- TASK-137 extends this sub-table. The companion idea-001.layout-engine-discussion.md is rationale-only — no rows from it. -->

## ERC engine (idea-001.erc-engine.md)

| Check | Shipped? | Severity matches dossier? | Bucket | Notes |
|---|---|---|---|---|

<!-- TASK-138 extends this sub-table. 15 rows expected (S1–S5 + E1–E10). -->

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
