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

<!-- TASK-135 extends this sub-table. -->

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
