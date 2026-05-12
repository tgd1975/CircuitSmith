# Tasks Overview

<!-- HEADER -->

<!-- markdownlint-disable-file MD033 -->

⚪ **Open: 57** | 🔵 **Active: 0** | 🟡 **Paused: 0** | 🟢 **Closed: 4** | **Total: 61** | █░░░░░░░░░ 7%

**Jump to:** [Burn-up](#burn-up) · [Active Tasks](#active-tasks) · [Paused Tasks](#paused-tasks) · [Open Tasks](#open-tasks) · [Closed Tasks](#closed-tasks)

<!-- END HEADER -->

<!-- BURNUP:START -->
<a id="burn-up"></a>

_No git tag found yet — burn-up chart needs a release tag to anchor on._
<!-- BURNUP:END -->

<!-- GENERATED -->

## Active Tasks

_No active tasks._

## Paused Tasks

_No paused tasks._

## Open Tasks

| ID | Title | Effort | Complexity | Status |
|----|-------|--------|------------|--------|
| [TASK-001](open/task-001-extract-mcu-board-profiles.md) | Extract ESP32 and nRF52840 board profiles into components/mcus.py | Medium (2-8h) | Medium | ⚪ open |
| [TASK-002](open/task-002-write-passives-component-library.md) | Write components/passives.py | Medium (2-8h) | Junior | ⚪ open |
| [TASK-003](open/task-003-write-connectors-component-library.md) | Write components/connectors.py | Medium (2-8h) | Junior | ⚪ open |
| [TASK-004](open/task-004-write-sensors-component-library.md) | Write components/sensors.py | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-005](open/task-005-write-circuit-json-schema.md) | Write schema/circuit.schema.json | Medium (2-8h) | Medium | ⚪ open |
| [TASK-006](open/task-006-refactor-generate-schematic-to-use-library.md) | Refactor scripts/generate-schematic.py to import from components/ | Medium (2-8h) | Medium | ⚪ open |
| [TASK-007](open/task-007-skill-scaffold-license-changelog-docs.md) | Skill scaffolding — LICENSE, CHANGELOG, docs/index, docs/components | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-008](open/task-008-implement-netgraph-data-model.md) | Implement netgraph.py — shared NetGraph data model | Medium (2-8h) | Senior | ⚪ open |
| [TASK-009](open/task-009-implement-layout-kernel-canonical-slots.md) | Implement layout_engine/kernel.py — deterministic placer | Large (8-24h) | Senior | ⚪ open |
| [TASK-010](open/task-010-implement-manhattan-router.md) | Implement layout_engine/router.py — Manhattan router | Medium (2-8h) | Senior | ⚪ open |
| [TASK-011](open/task-011-implement-v01-structural-rubric.md) | Implement v0.1 structural rubric (overlaps, labels_fit, wire_crossings) | Medium (2-8h) | Medium | ⚪ open |
| [TASK-012](open/task-012-implement-renderer.md) | Implement renderer.py — YAML to SVG via Schemdraw | Large (8-24h) | Senior | ⚪ open |
| [TASK-013](open/task-013-write-layout-json-schema.md) | Write schema/layout.schema.json | Small (&lt;2h) | Medium | ⚪ open |
| [TASK-014](open/task-014-author-circuit-yml-and-layout-yml-pairs.md) | Author esp32 and nrf52840 .circuit.yml + .layout.yml pairs | Medium (2-8h) | Medium | ⚪ open |
| [TASK-015](open/task-015-cutover-pr-retire-old-generator.md) | Cutover PR — commit full-pedal fixture, retire old generator, retarget CI | Medium (2-8h) | Senior | ⚪ open |
| [TASK-016](open/task-016-write-renderer-and-layout-docs.md) | Write docs/circuit-yaml.md and docs/layout.md | Medium (2-8h) | Medium | ⚪ open |
| [TASK-017](open/task-017-implement-ai-placer-convergence-loop.md) | Implement layout_engine/ai_placer.py — convergence loop and reason codes | Large (8-24h) | Senior | ⚪ open |
| [TASK-018](open/task-018-add-no-ai-fallback-flag.md) | Add --no-ai fallback flag to layout.py | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-019](open/task-019-extend-rubric-with-numeric-checks.md) | Extend rubric with numeric checks promoted from advisory | Medium (2-8h) | Medium | ⚪ open |
| [TASK-020](open/task-020-extend-meta-yml-provenance.md) | Extend meta.yml.provenance with ai_invoked and escalations | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-021](open/task-021-update-layout-docs-for-ai-placer.md) | Update docs/layout.md with AI-placer invocation and cost notes | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-022](open/task-022-implement-erc-engine.md) | Implement erc_engine.py with structural S1–S3 and electrical E1–E10 | Large (8-24h) | Senior | ⚪ open |
| [TASK-023](open/task-023-integrate-erc-into-renderer-pipeline.md) | Integrate ERC into renderer pipeline (post-schema, pre-drawing) | Small (&lt;2h) | Medium | ⚪ open |
| [TASK-024](open/task-024-seed-rule-catalog-rules-json.md) | Seed knowledge/rules.json with 15 entries (S1–S5 + E1–E10) | Medium (2-8h) | Medium | ⚪ open |
| [TASK-025](open/task-025-write-validate-catalog-script.md) | Write knowledge/validate_catalog.py | Small (&lt;2h) | Medium | ⚪ open |
| [TASK-026](open/task-026-write-knowledge-backlog.md) | Write knowledge/BACKLOG.md — remaining educational rules | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-027](open/task-027-wire-catalog-into-erc-report.md) | Wire catalog into ERC report writer | Medium (2-8h) | Medium | ⚪ open |
| [TASK-028](open/task-028-write-erc-report-and-document-e9.md) | Write erc-report.md for each target; document E9 WARNING rationale | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-029](open/task-029-extend-ci-staleness-and-erc-gate.md) | Extend CI — staleness guard for erc-report; ERROR-level gate; catalog validation | Small (&lt;2h) | Medium | ⚪ open |
| [TASK-030](open/task-030-write-erc-checks-reference-doc.md) | Write docs/erc-checks.md | Medium (2-8h) | Medium | ⚪ open |
| [TASK-031](open/task-031-implement-bom-exporter.md) | Implement bom_exporter.py — Markdown and CSV | Medium (2-8h) | Medium | ⚪ open |
| [TASK-032](open/task-032-embed-bom-table-in-build-guide.md) | Embed BOM table in build guide | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-033](open/task-033-implement-netlist-exporter.md) | Implement netlist_exporter.py — flatten NetGraph to KiCad .net | Medium (2-8h) | Senior | ⚪ open |
| [TASK-034](open/task-034-kicad-netlist-import-spot-check.md) | Spot-check main-circuit.net imports into KiCad without errors | XS (&lt;30m) | Medium | ⚪ open |
| [TASK-035](open/task-035-extend-ci-and-docs-for-exporters.md) | Extend CI staleness guard for bom + netlist; update docs/index.md | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-036](open/task-036-implement-markdown-block-rewrite.md) | Implement Markdown ```circuit block rewrite (workflow or superfences formatter) | Medium (2-8h) | Senior | ⚪ open |
| [TASK-037](open/task-037-implement-show-source-flag.md) | Implement show_source flag for Markdown blocks | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-038](open/task-038-update-pre-commit-hook-for-circuit-yml.md) | Update pre-commit hook to trigger on .circuit.yml changes | Small (&lt;2h) | Medium | ⚪ open |
| [TASK-039](open/task-039-write-skill-md-system-prompt.md) | Write .claude/skills/circuit/SKILL.md with full system prompt | Medium (2-8h) | Senior | ⚪ open |
| [TASK-040](open/task-040-register-skill-in-vibe-config.md) | Register circuit skill in .vibe/config.toml enabled_skills | XS (&lt;30m) | Junior | ⚪ open |
| [TASK-041](open/task-041-run-five-acceptance-tests.md) | Run the five Phase 6 acceptance tests | Large (8-24h) | Senior | ⚪ open |
| [TASK-042](open/task-042-finalise-skill-docs.md) | Finalise all .claude/skills/circuit/docs/ files | Medium (2-8h) | Medium | ⚪ open |
| [TASK-043](open/task-043-create-standalone-circuit-skill-repo.md) | Create circuit-skill standalone GitHub repository | Small (&lt;2h) | Medium | ⚪ open |
| [TASK-044](open/task-044-extract-skill-commit-history.md) | Extract skill commit history via git subtree split; push as main | Medium (2-8h) | Senior | ⚪ open |
| [TASK-045](open/task-045-replace-skill-dir-with-pinned-copy.md) | Replace skill dir with pinned copy; update doc links; write RELEASING.md and README | Medium (2-8h) | Medium | ⚪ open |
| [TASK-049](open/task-049-kicad-netlist-structural-test.md) | Structural test for KiCad netlist output (S-expression grammar) | Medium (2-8h) | Medium | ⚪ open |
| [TASK-050](open/task-050-boundary-import-contract-test.md) | Boundary-import contract test for circuit-skill modules | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-051](open/task-051-portability-lint.md) | Portability lint for .claude/skills/circuit/ | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-052](open/task-052-schema-validation-pre-commit.md) | Schema-validation pre-commit hook for .circuit.yml | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-053](open/task-053-netgraph-golden-hash-contract-test.md) | NetGraph golden-hash CI contract test | Small (&lt;2h) | Medium | ⚪ open |
| [TASK-054](open/task-054-seed-adr-folder.md) | Seed docs/developers/adr/ with foundational decisions from the IDEA-001 dossier | Medium (2-8h) | Medium | ⚪ open |
| [TASK-055](open/task-055-code-owner-skills-hook.md) | Code-owner skills registry and PreToolUse hook | Medium (2-8h) | Medium | ⚪ open |
| [TASK-056](open/task-056-author-initial-code-owner-skills.md) | Author the first three code-owner skills (co-netgraph, co-schema, co-erc-engine) | Medium (2-8h) | Medium | ⚪ open |
| [TASK-057](open/task-057-emit-v01-escalations-to-meta-yml.md) | Emit v0.1 kernel fail-loud events to meta.yml.provenance.escalations | Small (&lt;2h) | Medium | ⚪ open |
| [TASK-058](open/task-058-implement-check-phase2b-trigger.md) | Implement scripts/check_phase2b_trigger.py | Small (&lt;2h) | Junior | ⚪ open |
| [TASK-059](open/task-059-wire-phase2b-gate-into-release-script.md) | Wire Phase 2b gate into release_snapshot.py with CS_PHASE2B_BYPASS | Small (&lt;2h) | Medium | ⚪ open |
| [TASK-060](open/task-060-autonomous-implementation-mode.md) | Set up autonomous-implementation mode (AUTONOMY.md, /epic-run, HIL sweep, branch hygiene) | Large (8-24h) | Senior | ⚪ open |

## Closed Tasks

| ID | Title | Effort |
|----|-------|--------|
| [TASK-046](closed/task-046-add-pyproject-and-dev-requirements.md) | Add pyproject.toml and requirements-dev.txt | Small (&lt;2h) |
| [TASK-047](closed/task-047-configure-pytest.md) | Configure pytest (testpaths, discovery, coverage thresholds) | XS (&lt;30m) |
| [TASK-048](closed/task-048-add-minimal-ci-workflow.md) | Add minimal GitHub Actions CI workflow | Small (&lt;2h) |
| [TASK-061](closed/task-061-adopt-python-linter-formatter.md) | Adopt a Python linter/formatter and wire it into /commit + pre-commit hook | Medium (2-8h) |
<!-- END GENERATED -->
