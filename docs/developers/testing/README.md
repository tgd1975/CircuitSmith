# Test plan and coverage matrix

This directory is CircuitSmith's **deliberate** test plan: one chapter
per subsystem plus a top-level coverage matrix, so a contributor can
answer *"how is the router tested? what cases are deliberately
uncovered? what is an acceptable PR-time check?"* from a single place.

It is the breadth-and-depth companion to
[`../TESTING.md`](../TESTING.md), which covers the *conventions* — test
layers, framework choice, fixture layout, how to write and run a test.
Read `TESTING.md` to learn **how** we test; read this directory to learn
**what** is tested, **where**, and **what is intentionally not**.

> **Status.** Seeded by EPIC-011. The eight subsystem chapters
> (TASK-085..088) and the coverage matrix below (TASK-089) are authored;
> the CI staleness guard that keeps this plan honest lands in TASK-091.

## How this directory is organised

- **One file per subsystem.** Multi-subsystem files balloon and attract
  drift; one file per subsystem keeps each plan independently ownable
  and reviewable.
- **Filename slug equals the subsystem identifier**, mirroring the
  Python module layout under [`../../../src/circuitsmith/`](../../../src/circuitsmith/)
  so a reader can navigate from code to plan by changing a path prefix
  (`src/circuitsmith/netgraph.py` → `testing/netgraph.md`).
- **The matrix lives here, at the index.** It is the entry point;
  chapters are referenced from it, not the other way around.

Each chapter carries a small frontmatter block declaring the subsystem
slug and the code it covers, followed by an H1 and the canonical
chapter structure:

```yaml
---
subsystem: <slug>
covers: <module path(s) the chapter pins down>
---
```

The canonical chapter structure (every chapter uses these headings,
noting "none" explicitly rather than omitting a heading):

1. Inputs / outputs the tests pin down
2. Unit tests
3. Integration tests
4. Golden / snapshot tests
5. Property / fuzz tests
6. Performance budget
7. Known uncovered cases (each with a one-sentence rationale)
8. PR-time / nightly / release cadence

## Subsystem chapters

| Subsystem | Chapter | Covers |
|---|---|---|
| Schema validation | [`schema.md`](schema.md) | `src/circuitsmith/schema/` + rule-catalog validation |
| NetGraph | [`netgraph.md`](netgraph.md) | `src/circuitsmith/netgraph.py` |
| Layout kernel | [`layout-kernel.md`](layout-kernel.md) | `src/circuitsmith/layout/{kernel,rubric,ai_placer}.py` |
| Manhattan router | [`router.md`](router.md) | `src/circuitsmith/layout/router.py` |
| Renderer | [`renderer.md`](renderer.md) | `src/circuitsmith/renderer.py` |
| ERC engine | [`erc-engine.md`](erc-engine.md) | `src/circuitsmith/erc_engine.py` + `knowledge/` |
| Exporters | [`exporters.md`](exporters.md) | `src/circuitsmith/export/` |
| Skill orchestration | [`skill-orchestration.md`](skill-orchestration.md) | `.claude/skills/circuit/` + `markdown.py` |
| CI gates | [`ci-gates.md`](ci-gates.md) | `scripts/check_*.py`, pre-commit, CI workflow |

The working inventory the chapters are built from lives at
[`_inventory.md`](_inventory.md) (underscore-prefixed so it is not a
chapter). It is a cross-cutting list of every test file tagged by
subsystem, layer, and cadence — raw material for the chapters and the
matrix, safe to delete once the matrix is authoritative.

## Coverage matrix

<!-- MATRIX:START -->

Every test file mapped to the subsystem(s) it covers, its layer, and the
cadence it runs at. **Read it for breadth** — spotting redundancy (two
rows covering one case at different layers) and gaps (a subsystem with no
row at a given layer) — then follow a row's subsystem to the chapter for
depth.

**Column conventions.** *Subsystems* is a comma-separated list of chapter
slugs (`task-system` marks tooling tests that are not a product chapter).
*Layer* is one or more of `unit` / `integration` / `golden` / `property`
/ `e2e`, plus `contract` for the cross-cutting-invariant tier from
[`../TESTING.md`](../TESTING.md). The cadence columns mark where a test
runs.

**Cadence policy.**

- **PR-time (✓ for every row today)** — runs on every push/PR and in the
  local pre-commit chain where applicable. Budget: the full `pytest`
  suite is well under the 5-minute PR ceiling (currently ~10 s for 520+
  tests).
- **Nightly** — empty today. The rule-catalog *online* URL-reachability
  check is the first candidate (it needs network and is designated
  nightly in `ci.yml`, but no nightly workflow exists yet).
- **Release** — empty for *automated tests*. The KiCad-import spot-check
  (TASK-034) is a manual release step; the Phase 2b trigger and
  version-lockstep **gates** re-run at release, though their *tests* run
  per-PR (flagged in Notes).

**Maintenance.** The matrix is **hand-maintained for v1** — the "generate
from pytest markers" option floated in TASK-083 is deferred until the
matrix grows past ~80 rows. TASK-091 adds a CI staleness check that fails
the build when a `tests/` file has no row here, so hand-maintenance
cannot silently drift.

### Product-code tests (`tests/`)

| Test file | Subsystems | Layer | PR | Nightly | Release | Notes |
|---|---|---|:--:|:--:|:--:|---|
| `tests/test_schema_validation.py` | schema | unit, integration | ✓ | | | |
| `tests/test_layout_schema.py` | schema | unit | ✓ | | | |
| `tests/test_validate_catalog.py` | schema | unit | ✓ | | | online URL check is a future nightly |
| `tests/test_components.py` | schema | unit | ✓ | | | connector-factory edge cases |
| `tests/schema/test_sub_blocks_schema.py` | schema | unit | ✓ | | | S6 has no direct trigger (gap) |
| `tests/schema/test_pages_schema.py` | schema | unit | ✓ | | | |
| `tests/components/test_bjt_profiles.py` | schema, layout-kernel | unit | ✓ | | | profile + BJT kernel rule |
| `tests/components/test_555_profile.py` | schema | unit | ✓ | | | |
| `tests/components/test_opamp_profile.py` | schema | unit | ✓ | | | |
| `tests/test_netgraph.py` | netgraph | unit | ✓ | | | |
| `tests/test_netgraph_golden.py` | netgraph | golden | ✓ | | | cross-release drift gate |
| `tests/netgraph/test_sub_block_flattener.py` | netgraph | unit | ✓ | | | |
| `tests/test_kernel.py` | layout-kernel | unit, golden | ✓ | | | determinism + incremental diff |
| `tests/test_rubric.py` | layout-kernel | unit | ✓ | | | v0.1 structural rubric |
| `tests/test_rubric_v1.py` | layout-kernel | unit | ✓ | | | thresholds from a 2-circuit corpus |
| `tests/test_ai_placer.py` | layout-kernel | unit, integration | ✓ | | | mocked LLM (ADR-0002) |
| `tests/test_no_ai_flag.py` | layout-kernel | integration | ✓ | | | mocked LLM |
| `tests/layout/test_rc_low_pass_rule.py` | layout-kernel | unit, golden | ✓ | | | |
| `tests/layout/test_rc_high_pass_rule.py` | layout-kernel | unit, golden | ✓ | | | |
| `tests/layout/test_cc_decoupling_rule.py` | layout-kernel | unit, golden | ✓ | | | |
| `tests/layout/test_rr_divider_rule.py` | layout-kernel | unit, golden | ✓ | | | |
| `tests/layout/test_bjt_load_degeneration_rules.py` | layout-kernel | unit, golden | ✓ | | | |
| `tests/layout/test_pullup_ic_anchor.py` | layout-kernel | unit | ✓ | | | |
| `tests/layout/test_page_propagation.py` | layout-kernel | unit, integration | ✓ | | | |
| `tests/test_router.py` | router | unit | ✓ | | | property suite is a gap (TASK-090) |
| `tests/test_renderer.py` | renderer | unit, integration | ✓ | | | |
| `tests/test_full_pedal_fixture.py` | renderer | integration, e2e | ✓ | | | full-pipeline e2e |
| `tests/render/test_multi_page_driver.py` | renderer | integration | ✓ | | | |
| `tests/render/test_cross_page_labels.py` | renderer | integration | ✓ | | | |
| `tests/test_meta_yml_provenance.py` | renderer, layout-kernel | integration | ✓ | | | |
| `tests/test_meta_yml_escalations.py` | renderer, layout-kernel | integration | ✓ | | | |
| `tests/test_erc_engine.py` | erc-engine | unit | ✓ | | | S1/E6/E8 untriggered (TASK-090) |
| `tests/test_erc_report_enrichment.py` | erc-engine | unit | ✓ | | | |
| `tests/test_renderer_erc.py` | erc-engine, renderer | integration | ✓ | | | pre-layout ERC contract |
| `tests/erc/test_sub_block_rules.py` | erc-engine | unit | ✓ | | | E11–E15 |
| `tests/erc/test_active_device_rules.py` | erc-engine | unit | ✓ | | | E16–E18 |
| `tests/erc/test_cross_page_rules.py` | erc-engine | unit | ✓ | | | E19–E22 |
| `tests/test_bom_exporter.py` | exporters | unit | ✓ | | | |
| `tests/test_netlist_exporter.py` | exporters | unit, integration | ✓ | | | round-trip parse |
| `tests/test_netlist_structure.py` | exporters | golden | ✓ | | | S-expression grammar |
| `tests/test_markdown_block.py` | skill-orchestration | unit | ✓ | | | agent prompt out of scope |
| `tests/test_module_boundaries.py` | ci-gates | contract | ✓ | | | |
| `tests/test_check_gallery_regression.py` | ci-gates | unit, integration | ✓ | | | |
| `tests/test_precommit_hook.py` | ci-gates | integration | ✓ | | | |
| `tests/test_renderer_staleness.py` | ci-gates, renderer | integration | ✓ | | | Ubuntu-only golden |
| `tests/test_schema_pre_commit.py` | ci-gates, schema | integration | ✓ | | | |

### Project-tooling tests (`scripts/tests/`)

| Test file | Subsystems | Layer | PR | Nightly | Release | Notes |
|---|---|---|:--:|:--:|:--:|---|
| `scripts/tests/test_check_erc_reports.py` | ci-gates | unit, integration | ✓ | | | |
| `scripts/tests/test_phase2b_trigger.py` | ci-gates | unit | ✓ | | | |
| `scripts/tests/test_release_phase2b_gate.py` | ci-gates | unit | ✓ | | | gate also re-runs at release |
| `scripts/tests/test_portability_lint.py` | ci-gates | unit | ✓ | | | |
| `scripts/tests/test_version_lockstep.py` | ci-gates | contract | ✓ | | | gate also re-runs at release |
| `scripts/tests/test_security_review_personal_data.py` | ci-gates | unit | ✓ | | | |
| `scripts/tests/test_codeowner_hook.py` | task-system | unit | ✓ | | | tooling, not product |
| `scripts/tests/test_housekeep.py` | task-system | unit | ✓ | | | tooling |
| `scripts/tests/test_housekeep_concurrency.py` | task-system | unit | ✓ | | | tooling, lock guard |
| `scripts/tests/test_task_system_config.py` | task-system | unit | ✓ | | | tooling |
| `scripts/tests/test_update_idea_overview.py` | task-system | unit | ✓ | | | tooling |
| `scripts/tests/test_release_burnup.py` | task-system | unit | ✓ | | | tooling |
| `scripts/tests/test_release_snapshot.py` | task-system | unit | ✓ | | | tooling |

<!-- MATRIX:END -->
