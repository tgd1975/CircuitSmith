# Test surface inventory (working artefact)

*Working document for EPIC-011 (TASK-084).* A flat list of every test
file in the repo, tagged by subsystem, layer, and cadence — the raw
material for the per-subsystem chapters (TASK-085..088) and the
top-level matrix (TASK-089). The underscore prefix keeps it out of the
chapter index in [`README.md`](README.md). Safe to delete once the
matrix is authoritative; kept around because re-running the audit is
cheap with it present.

**Method.** Every `test_*.py` under the two `pyproject.toml` test roots
(`tests/`, `scripts/tests/`) was read at the module-docstring level;
subsystem and layer tags are derived from the docstring + imports, not
guessed from filenames. Summaries quote the docstring's first line.

**Layers** (per IDEA-003): `unit` (pure helpers, synthetic inputs),
`integration` (subsystem + immediate neighbours), `golden` (snapshot /
hash contract), `property` (randomised / fuzz), `e2e` (full pipeline).

**Cadence.** Every automated test currently runs at **PR-time** — the
CI workflow ([`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml))
runs `pytest` plus the gate scripts on every push/PR. There is no
nightly or release-only automated tier yet (see *Observations*).

## `tests/` — product-code tests (46 files)

| Test file | Subsystem(s) | Layer | Cadence | Pins down |
|---|---|---|---|---|
| `test_schema_validation.py` | schema | unit, integration | PR | Schema + S4/S5 post-schema validation (TASK-005) |
| `test_layout_schema.py` | schema | unit | PR | `.layout.yml` schema validation (TASK-013) |
| `test_validate_catalog.py` | schema | unit | PR | Rule-catalog validator well-formedness (TASK-025) |
| `test_components.py` | schema | unit | PR | Connector-factory edge cases (EPIC-001 review) |
| `schema/test_sub_blocks_schema.py` | schema | unit | PR | Sub-blocks + instances schema (TASK-115) |
| `schema/test_pages_schema.py` | schema | unit | PR | `pages:` partition schema (TASK-124) |
| `components/test_bjt_profiles.py` | schema, layout-kernel | unit | PR | BJT npn/pnp profile + BJT canonical rule (TASK-120) |
| `components/test_555_profile.py` | schema | unit | PR | `ic/555` profile auto-discovery + keying (TASK-121) |
| `components/test_opamp_profile.py` | schema | unit | PR | `ic/opamp_dual_supply` profile (TASK-122) |
| `test_netgraph.py` | netgraph | unit | PR | NetGraph construction + connection forms (TASK-008) |
| `test_netgraph_golden.py` | netgraph | golden | PR | `NetGraph.canonical_hash` golden contract (TASK-053) |
| `netgraph/test_sub_block_flattener.py` | netgraph | unit | PR | Sub-block flattener (TASK-116) |
| `test_kernel.py` | layout-kernel | unit, golden | PR | Deterministic kernel placement + escalations (TASK-009) |
| `test_rubric.py` | layout-kernel | unit | PR | v0.1 structural rubric (TASK-011) |
| `test_rubric_v1.py` | layout-kernel | unit | PR | v1 numeric rubric checks (TASK-019) |
| `test_ai_placer.py` | layout-kernel | unit, integration | PR | AI-placer convergence + reason codes (TASK-017) |
| `test_no_ai_flag.py` | layout-kernel | unit, integration | PR | `--no-ai` fallback flag (TASK-018) |
| `layout/test_rc_low_pass_rule.py` | layout-kernel | unit, golden | PR | RC low-pass canonical rule (TASK-111) |
| `layout/test_rc_high_pass_rule.py` | layout-kernel | unit, golden | PR | RC high-pass canonical rule (TASK-112) |
| `layout/test_cc_decoupling_rule.py` | layout-kernel | unit, golden | PR | C+C decoupling pair rule (TASK-113) |
| `layout/test_rr_divider_rule.py` | layout-kernel | unit, golden | PR | R+R voltage-divider rule (TASK-114) |
| `layout/test_bjt_load_degeneration_rules.py` | layout-kernel | unit, golden | PR | BJT load + emitter-degeneration rules (TASK-129) |
| `layout/test_pullup_ic_anchor.py` | layout-kernel | unit | PR | Pull-up anchor widened to IC inputs (TASK-130) |
| `layout/test_page_propagation.py` | layout-kernel | unit, integration | PR | `Placement.page` carried end-to-end (TASK-124) |
| `test_router.py` | router | unit | PR | Manhattan router geometry (TASK-010) |
| `test_renderer.py` | renderer | unit, integration | PR | YAML→SVG renderer (TASK-012) |
| `test_full_pedal_fixture.py` | renderer | integration, e2e | PR | Full-pedal fixture end-to-end (TASK-014) |
| `render/test_multi_page_driver.py` | renderer | integration | PR | Multi-page render driver (TASK-125) |
| `render/test_cross_page_labels.py` | renderer | integration | PR | Cross-page net label rendering (TASK-126) |
| `test_meta_yml_provenance.py` | renderer, layout-kernel | integration | PR | meta.yml provenance + AI invocations (TASK-020) |
| `test_meta_yml_escalations.py` | renderer, layout-kernel | integration | PR | Kernel fail-loud escalations to meta.yml (TASK-057) |
| `test_erc_engine.py` | erc-engine | unit | PR | Structural + electrical ERC checks (TASK-022) |
| `test_erc_report_enrichment.py` | erc-engine | unit | PR | ERC report writer + catalog enrichment (TASK-027) |
| `test_renderer_erc.py` | erc-engine, renderer | integration | PR | ERC integrated into renderer pipeline (TASK-023) |
| `erc/test_sub_block_rules.py` | erc-engine | unit | PR | Sub-block ERC rules E11–E15 (TASK-117) |
| `erc/test_active_device_rules.py` | erc-engine | unit | PR | Active-device ERC rules E16–E18 (TASK-123) |
| `erc/test_cross_page_rules.py` | erc-engine | unit | PR | Cross-page ERC rules E19–E22 (TASK-127) |
| `test_bom_exporter.py` | exporters | unit | PR | BOM exporter Markdown + CSV (TASK-031) |
| `test_netlist_exporter.py` | exporters | unit | PR | KiCad netlist exporter (TASK-033) |
| `test_netlist_structure.py` | exporters | golden | PR | KiCad netlist S-expression grammar (TASK-049) |
| `test_markdown_block.py` | skill-orchestration | unit | PR | Markdown circuit-block rewriter (TASK-036) |
| `test_module_boundaries.py` | ci-gates | contract | PR | Module-boundary import contract (TASK-050) |
| `test_check_gallery_regression.py` | ci-gates | unit, integration | PR | Gallery regression script behaviour (TASK-101) |
| `test_precommit_hook.py` | ci-gates | integration | PR | Circuit-artefact regenerator (TASK-038) |
| `test_renderer_staleness.py` | ci-gates, renderer | integration | PR | Renderer staleness guard (TASK-015) |
| `test_schema_pre_commit.py` | ci-gates, schema | integration | PR | `check_circuit_schema.py` gate (TASK-052) |

> Layer note: `contract` (used by `test_module_boundaries.py` and
> `test_version_lockstep.py`) is the "cross-cutting invariant" tier from
> [`../TESTING.md`](../TESTING.md); the matrix folds it under `golden`
> unless a chapter argues for keeping it distinct.

## `scripts/tests/` — project-tooling tests (13 files)

These exercise the task-system installation and CI/release tooling, not
the `circuitsmith` product package. They map to the **ci-gates** chapter
where they test a CI gate; the pure task-system tooling tests are tagged
`task-system` (a tooling pseudo-subsystem, not one of the nine product
chapters — TASK-088 decides how much of this to cover vs declare
out-of-product-scope).

| Test file | Subsystem(s) | Layer | Cadence | Pins down |
|---|---|---|---|---|
| `test_check_erc_reports.py` | ci-gates | unit, integration | PR | ERC-report staleness gate (TASK-029) |
| `test_phase2b_trigger.py` | ci-gates | unit | PR | Phase 2b trigger aggregator (TASK-058) |
| `test_release_phase2b_gate.py` | ci-gates | unit | PR | Phase 2b gate in release_snapshot (TASK-059) |
| `test_portability_lint.py` | ci-gates | unit | PR | Portability lint on synthetic trees (TASK-051) |
| `test_version_lockstep.py` | ci-gates | contract | PR | `__version__` == pyproject version |
| `test_security_review_personal_data.py` | ci-gates | unit | PR | Personal-data leak detection (TASK-074) |
| `test_codeowner_hook.py` | task-system | unit | PR | Code-owner hook registry + matching (TASK-055) |
| `test_housekeep.py` | task-system | unit | PR | `housekeep.py` task moves + regen |
| `test_housekeep_concurrency.py` | task-system | unit | PR | `housekeep.py` lock-guard concurrency |
| `test_task_system_config.py` | task-system | unit | PR | `task_system_config.py` |
| `test_update_idea_overview.py` | task-system | unit | PR | `update_idea_overview.py` |
| `test_release_burnup.py` | task-system | unit | PR | `release_burnup.py` |
| `test_release_snapshot.py` | task-system | unit | PR | `release_snapshot.py` |

## Support files (not tests)

| File | Role |
|---|---|
| `tests/_sexp.py` | S-expression tokeniser/parser used by `test_netlist_structure.py` |
| `tests/fixtures/bad_boundary/bom_exporter_violator.py` | Deliberate-violation fixture for `test_module_boundaries.py` |

Both are imported by a test rather than collected directly; they carry
no `test_*` functions and the matrix lists them under the consuming
test's row.

## Observations (feed TASK-089 matrix + TASK-090 gap triage)

- **No nightly or release-only automated tier.** All 59 test files run
  at PR-time. The rule-catalog *online* URL check is designated nightly
  in `ci.yml` comments but no nightly workflow exists; the KiCad-import
  spot-check (TASK-034) is a manual/release step, not an automated test.
  The matrix's nightly/release columns will be empty until this lands —
  a candidate gap for TASK-090.
- **Thin product subsystems.** `router` (1 file) and
  `skill-orchestration` (1 file) have the least direct coverage. The
  router's docstring does not advertise property tests; TASK-086 should
  confirm whether `test_router.py` exercises the randomised-netlist
  invariants IDEA-003 expects, or flag the absence as a gap.
- **Cross-cutting tests.** `test_full_pedal_fixture.py` (renderer e2e),
  `test_renderer_staleness.py`, and `test_check_gallery_regression.py`
  span multiple subsystems; the matrix lists them once with a
  comma-separated subsystem set and the chapters forward-reference them.
- **`task-system` is not a product chapter.** Seven `scripts/tests/`
  files test the installed task-system tooling. They are inventoried for
  completeness; TASK-088 decides whether the ci-gates chapter covers
  them or declares them out-of-product-scope.
