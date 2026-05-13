# Tasks Overview

<!-- HEADER -->

<!-- markdownlint-disable-file MD033 -->

⚪ **Open: 2** | 🔵 **Active: 0** | 🟡 **Paused: 0** | 🟢 **Closed: 80** | **Total: 82** | ██████████ 98%

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
| [TASK-041](open/task-041-run-five-acceptance-tests.md) | Run the five Phase 6 acceptance tests | Large (8-24h) | Senior | ⚪ open |
| [TASK-080](open/task-080-publish-circuitsmith-to-pypi.md) | Publish circuitsmith package to PyPI (first real 0.1.0) | Medium (2-8h) | Senior | ⚪ open |

## Closed Tasks

| ID | Title | Effort |
|----|-------|--------|
| [TASK-001](closed/task-001-extract-mcu-board-profiles.md) | Extract ESP32 and nRF52840 board profiles into components/mcus.py | Medium (2-8h) |
| [TASK-002](closed/task-002-write-passives-component-library.md) | Write components/passives.py | Medium (2-8h) |
| [TASK-003](closed/task-003-write-connectors-component-library.md) | Write components/connectors.py | Medium (2-8h) |
| [TASK-004](closed/task-004-write-sensors-component-library.md) | Write components/sensors.py | Small (&lt;2h) |
| [TASK-005](closed/task-005-write-circuit-json-schema.md) | Write schema/circuit.schema.json | Medium (2-8h) |
| [TASK-006](closed/task-006-refactor-generate-schematic-to-use-library.md) | Refactor scripts/generate-schematic.py to import from components/ | Medium (2-8h) |
| [TASK-007](closed/task-007-skill-scaffold-license-changelog-docs.md) | Skill scaffolding — LICENSE, CHANGELOG, docs/index, docs/components | Small (&lt;2h) |
| [TASK-008](closed/task-008-implement-netgraph-data-model.md) | Implement netgraph.py — shared NetGraph data model | Medium (2-8h) |
| [TASK-009](closed/task-009-implement-layout-kernel-canonical-slots.md) | Implement layout_engine/kernel.py — deterministic placer | Large (8-24h) |
| [TASK-010](closed/task-010-implement-manhattan-router.md) | Implement layout_engine/router.py — Manhattan router | Medium (2-8h) |
| [TASK-011](closed/task-011-implement-v01-structural-rubric.md) | Implement v0.1 structural rubric (overlaps, labels_fit, wire_crossings) | Medium (2-8h) |
| [TASK-012](closed/task-012-implement-renderer.md) | Implement renderer.py — YAML to SVG via Schemdraw | Large (8-24h) |
| [TASK-013](closed/task-013-write-layout-json-schema.md) | Write schema/layout.schema.json | Small (&lt;2h) |
| [TASK-014](closed/task-014-author-circuit-yml-and-layout-yml-pairs.md) | Author esp32 and nrf52840 .circuit.yml + .layout.yml pairs | Medium (2-8h) |
| [TASK-015](closed/task-015-cutover-pr-retire-old-generator.md) | Cutover PR — commit full-pedal fixture, retire old generator, retarget CI | Medium (2-8h) |
| [TASK-016](closed/task-016-write-renderer-and-layout-docs.md) | Write docs/circuit-yaml.md and docs/layout.md | Medium (2-8h) |
| [TASK-017](closed/task-017-implement-ai-placer-convergence-loop.md) | Implement layout_engine/ai_placer.py — convergence loop and reason codes | Large (8-24h) |
| [TASK-018](closed/task-018-add-no-ai-fallback-flag.md) | Add --no-ai fallback flag to layout.py | Small (&lt;2h) |
| [TASK-019](closed/task-019-extend-rubric-with-numeric-checks.md) | Extend rubric with numeric checks promoted from advisory | Medium (2-8h) |
| [TASK-020](closed/task-020-extend-meta-yml-provenance.md) | Extend meta.yml.provenance with ai_invoked and escalations | Small (&lt;2h) |
| [TASK-021](closed/task-021-update-layout-docs-for-ai-placer.md) | Update docs/layout.md with AI-placer invocation and cost notes | Small (&lt;2h) |
| [TASK-022](closed/task-022-implement-erc-engine.md) | Implement erc_engine.py with structural S1–S3 and electrical E1–E10 | Large (8-24h) |
| [TASK-023](closed/task-023-integrate-erc-into-renderer-pipeline.md) | Integrate ERC into renderer pipeline (post-schema, pre-drawing) | Small (&lt;2h) |
| [TASK-024](closed/task-024-seed-rule-catalog-rules-json.md) | Seed knowledge/rules.json with 15 entries (S1–S5 + E1–E10) | Medium (2-8h) |
| [TASK-025](closed/task-025-write-validate-catalog-script.md) | Write knowledge/validate_catalog.py | Small (&lt;2h) |
| [TASK-026](closed/task-026-write-knowledge-backlog.md) | Write knowledge/BACKLOG.md — remaining educational rules | Small (&lt;2h) |
| [TASK-027](closed/task-027-wire-catalog-into-erc-report.md) | Wire catalog into ERC report writer | Medium (2-8h) |
| [TASK-028](closed/task-028-write-erc-report-and-document-e9.md) | Write erc-report.md for each target; document E9 WARNING rationale | Small (&lt;2h) |
| [TASK-029](closed/task-029-extend-ci-staleness-and-erc-gate.md) | Extend CI — staleness guard for erc-report; ERROR-level gate; catalog validation | Small (&lt;2h) |
| [TASK-030](closed/task-030-write-erc-checks-reference-doc.md) | Write docs/erc-checks.md | Medium (2-8h) |
| [TASK-031](closed/task-031-implement-bom-exporter.md) | Implement bom_exporter.py — Markdown and CSV | Medium (2-8h) |
| [TASK-032](closed/task-032-embed-bom-table-in-build-guide.md) | Embed BOM table in build guide | Small (&lt;2h) |
| [TASK-033](closed/task-033-implement-netlist-exporter.md) | Implement netlist_exporter.py — flatten NetGraph to KiCad .net | Medium (2-8h) |
| [TASK-034](closed/task-034-kicad-netlist-import-spot-check.md) | Spot-check main-circuit.net imports into KiCad without errors | XS (&lt;30m) |
| [TASK-035](closed/task-035-extend-ci-and-docs-for-exporters.md) | Extend CI staleness guard for bom + netlist; update docs/index.md | Small (&lt;2h) |
| [TASK-036](closed/task-036-implement-markdown-block-rewrite.md) | Implement Markdown ```circuit block rewrite (workflow or superfences formatter) | Medium (2-8h) |
| [TASK-037](closed/task-037-implement-show-source-flag.md) | Implement show_source flag for Markdown blocks | Small (&lt;2h) |
| [TASK-038](closed/task-038-update-pre-commit-hook-for-circuit-yml.md) | Update pre-commit hook to trigger on .circuit.yml changes | Small (&lt;2h) |
| [TASK-039](closed/task-039-write-skill-md-system-prompt.md) | Write .claude/skills/circuit/SKILL.md with full system prompt | Medium (2-8h) |
| [TASK-040](closed/task-040-register-skill-in-vibe-config.md) | Register circuit skill in .vibe/config.toml enabled_skills | XS (&lt;30m) |
| [TASK-042](closed/task-042-finalise-skill-docs.md) | Finalise all .claude/skills/circuit/docs/ files | Medium (2-8h) |
| [TASK-043](closed/task-043-create-standalone-circuit-skill-repo.md) | Create circuit-skill standalone GitHub repository | Small (&lt;2h) |
| [TASK-044](closed/task-044-extract-skill-commit-history.md) | Extract skill commit history via git subtree split; push as main | Medium (2-8h) |
| [TASK-045](closed/task-045-replace-skill-dir-with-pinned-copy.md) | Replace skill dir with pinned copy; update doc links; write RELEASING.md and README | Medium (2-8h) |
| [TASK-046](closed/task-046-add-pyproject-and-dev-requirements.md) | Add pyproject.toml and requirements-dev.txt | Small (&lt;2h) |
| [TASK-047](closed/task-047-configure-pytest.md) | Configure pytest (testpaths, discovery, coverage thresholds) | XS (&lt;30m) |
| [TASK-048](closed/task-048-add-minimal-ci-workflow.md) | Add minimal GitHub Actions CI workflow | Small (&lt;2h) |
| [TASK-049](closed/task-049-kicad-netlist-structural-test.md) | Structural test for KiCad netlist output (S-expression grammar) | Medium (2-8h) |
| [TASK-050](closed/task-050-boundary-import-contract-test.md) | Boundary-import contract test for circuit-skill modules | Small (&lt;2h) |
| [TASK-051](closed/task-051-portability-lint.md) | Portability lint for .claude/skills/circuit/ | Small (&lt;2h) |
| [TASK-052](closed/task-052-schema-validation-pre-commit.md) | Schema-validation pre-commit hook for .circuit.yml | Small (&lt;2h) |
| [TASK-053](closed/task-053-netgraph-golden-hash-contract-test.md) | NetGraph golden-hash CI contract test | Small (&lt;2h) |
| [TASK-054](closed/task-054-seed-adr-folder.md) | Seed docs/developers/adr/ with foundational decisions from the IDEA-001 dossier | Medium (2-8h) |
| [TASK-055](closed/task-055-code-owner-skills-hook.md) | Code-owner skills registry and PreToolUse hook | Medium (2-8h) |
| [TASK-056](closed/task-056-author-initial-code-owner-skills.md) | Author the first three code-owner skills (co-netgraph, co-schema, co-erc-engine) | Medium (2-8h) |
| [TASK-057](closed/task-057-emit-v01-escalations-to-meta-yml.md) | Emit v0.1 kernel fail-loud events to meta.yml.provenance.escalations | Small (&lt;2h) |
| [TASK-058](closed/task-058-implement-check-phase2b-trigger.md) | Implement scripts/check_phase2b_trigger.py | Small (&lt;2h) |
| [TASK-059](closed/task-059-wire-phase2b-gate-into-release-script.md) | Wire Phase 2b gate into release_snapshot.py with CS_PHASE2B_BYPASS | Small (&lt;2h) |
| [TASK-060](closed/task-060-autonomous-implementation-mode.md) | Set up autonomous-implementation mode (AUTONOMY.md, /epic-run, HIL sweep, branch hygiene) | Large (8-24h) |
| [TASK-061](closed/task-061-adopt-python-linter-formatter.md) | Adopt a Python linter/formatter and wire it into /commit + pre-commit hook | Medium (2-8h) |
| [TASK-062](closed/task-062-author-development-setup-doc.md) | Author docs/developers/DEVELOPMENT_SETUP.md as the canonical first-time-setup entry point | Small (&lt;2h) |
| [TASK-063](closed/task-063-author-testing-doc.md) | Author docs/developers/TESTING.md describing test layers, conventions, and fixture layout | Medium (2-8h) |
| [TASK-064](closed/task-064-author-coding-standards-doc.md) | Author docs/developers/CODING_STANDARDS.md (naming, formatting, comment policy, type hints) | Small (&lt;2h) |
| [TASK-065](closed/task-065-author-ci-pipeline-doc.md) | Author docs/developers/CI_PIPELINE.md inventorying CI jobs and gate semantics | Small (&lt;2h) |
| [TASK-066](closed/task-066-author-task-system-doc.md) | Author docs/developers/TASK_SYSTEM.md describing the IDEA/EPIC/TASK workflow and /ts-* skills | Small (&lt;2h) |
| [TASK-067](closed/task-067-author-code-of-conduct.md) | Adopt and commit docs/developers/CODE_OF_CONDUCT.md (short custom CoC mirroring AwesomeStudioPedal) | Small (&lt;2h) |
| [TASK-068](closed/task-068-author-architecture-doc.md) | Author docs/developers/ARCHITECTURE.md as the explicit top-down architecture page | Medium (2-8h) |
| [TASK-069](closed/task-069-author-mermaid-style-guide.md) | Author docs/developers/MERMAID_STYLE_GUIDE.md (diagram types, palette, edge conventions) | Small (&lt;2h) |
| [TASK-070](closed/task-070-author-security-review-doc.md) | Author docs/developers/SECURITY_REVIEW.md (script usage + reviewer checklist) | Medium (2-8h) |
| [TASK-071](closed/task-071-author-commit-policy-doc.md) | Author docs/developers/COMMIT_POLICY.md (pathspec rationale, race story, bypass policy) | Medium (2-8h) |
| [TASK-072](closed/task-072-author-branch-protection-doc.md) | Author docs/developers/BRANCH_PROTECTION_CONCEPT.md documenting the protection ruleset | Small (&lt;2h) |
| [TASK-073](closed/task-073-apply-branch-protection.md) | Apply GitHub branch protection on main per BRANCH_PROTECTION_CONCEPT.md | Small (&lt;2h) |
| [TASK-074](closed/task-074-personal-data-leak-check-in-security-review-hook.md) | Extend security-review hook to detect personal-contact-info leaks | Small (&lt;2h) |
| [TASK-075](closed/task-075-fix-idea-skill-template-markdownlint.md) | Fix /ts-idea-new template so generated files pass markdownlint on first run | Small (&lt;2h) |
| [TASK-076](closed/task-076-write-adr-0012-supersede-adr-0007.md) | Write ADR-0012 (library as installable package) superseding ADR-0007 | Medium (2-8h) |
| [TASK-077](closed/task-077-atomic-relocation-to-src-circuitsmith.md) | Atomic relocation of circuit package to src/circuitsmith/ | Large (8-24h) |
| [TASK-078](closed/task-078-update-agent-facing-surface.md) | Update agent-facing surface for circuitsmith package rename | Small (&lt;2h) |
| [TASK-079](closed/task-079-repo-docs-sweep-and-changelog.md) | Repo docs sweep and CHANGELOG bullet for circuitsmith refactor | Small (&lt;2h) |
| [TASK-081](closed/task-081-author-release-workflow-scaffolding.md) | Author release workflow scaffolding (RELEASING.md + release.yml + version lockstep) | Medium (2-8h) |
| [TASK-082](closed/task-082-author-release-skill.md) | Author /release skill and register in .vibe/config.toml | Medium (2-8h) |
<!-- END GENERATED -->
