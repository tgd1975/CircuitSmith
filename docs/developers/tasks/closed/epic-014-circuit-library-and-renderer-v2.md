---
id: EPIC-014
name: circuit-library-and-renderer-v2
title: Component library and renderer v2 (sub-blocks, active devices, multi-page)
status: closed
opened: 2026-05-14
closed: 2026-05-14
assigned:
branch: release/epic-014-circuit-library-and-renderer-v2
---

Seeded by IDEA-008 (First-class sub-blocks and non-LED kernel rules)
and IDEA-009 (Active-device component profiles and multi-page
renderer support).

EPIC-012 (the tutorial and example gallery) closed with five entries
scaffolded but unable to render: the voltage divider blocked on the
v0.1 kernel's missing R+R rule, and TASK-097/098/099/100 blocked on
the absence of active-device profiles plus the renderer's page-break
path. The two follow-up ideas (IDEA-008 and IDEA-009) each carry a
full implementation plan; this epic is the execution layer that
turns those plans into landed code.

The epic bundles three independent capability tracks:

- **IDEA-008 Half 1 — non-LED kernel rules.** Four canonical-slot
  rules (R+C low-pass, R+C high-pass, C+C decoupling pair, R+R
  voltage divider) the layout kernel does not have today. Unblocks
  the voltage-divider gallery entry without requiring sub-block
  syntax.
- **IDEA-008 Half 2 — first-class sub-blocks.** `sub-blocks:` /
  `instances:` schema, netgraph flattener, sub-block ERC, inline-box
  renderer mode. Tutorial step 3's "repeated RC filter" example
  becomes expressible.
- **IDEA-009 — active devices + multi-page renderer.** Three new
  component profiles (`bjt_npn`/`bjt_pnp`, `ic/555`,
  `ic/opamp_dual_supply`), active-device ERC, the `pages:` partition
  in `.layout.yml`, multi-page render driver, cross-page net labels,
  and cross-page ERC. Unblocks the four remaining gallery entries.

The three tracks share Phase 0 (frozen decisions) and converge only
at the gallery re-attempt phase. The two ideas' implementation plans
already enumerate per-task scope, acceptance criteria, dependencies,
and effort estimates — this epic preserves that structure across 24
tasks rather than re-deriving it.

Ordering follows the dependency chain captured in each idea's
mermaid graph: freeze → parallel tracks → ERC → renderer → gallery
re-attempt → docs.

## Frozen decisions (TASK-110)

Phase 0 confirmed every proposed default from IDEA-008 and IDEA-009
without override. Each downstream task consumes the rows below as
epic-body invariants, not mid-task ADRs.

### From IDEA-008

| Question | Decision |
|---|---|
| Refdes flattening scheme | `<local-refdes>_<instance>` (e.g. `R_FILT_A`). Groups BOM by component class. |
| Port-naming convention | Named ports as a map: `ports: { signal_in: R.1, ... }`. References use `<instance>.<port-name>`. The `inputs:` / `outputs:` pin-alias form is **not** shipped. |
| Sub-block-internal `connections:` grammar | Reuses the top-level `connections:` grammar verbatim. Nets are local to the sub-block; the flattener prefixes them with the instance name to mint globals. |
| Voltage-divider rule discriminator | Either an explicit hint net-name on the tap (`/^(V?REF\|SENSE\|ADC\|DIV\|TAP)/i`) **or** a `role: divider` annotation on one of the resistors. Without a hint, kernel emits a low-confidence warning and falls back to flat placement. |
| Nested sub-blocks | Disallowed in v1. Schema rejects a sub-block definition whose `components.*.type` references another sub-block name; error message names the offending reference. |
| Renderer mode default for sub-block instances | v1 ships **inline-box** form. Hierarchical-port form is gated on IDEA-009's multi-page renderer and unlocked by the work in this epic (Phase 5). |

### From IDEA-009

| Question | Decision |
|---|---|
| Bundle vs split | Resolved by this epic's existence — single bundled epic. (Overrides IDEA-009's "split" default.) |
| BJT terminal-role encoding | Per-pin `role:` field (`pins.B.role: "base"`, `pins.C.role: "collector"`, `pins.E.role: "emitter"`). No `metadata.bjt_terminals` map. |
| 555 pin keys | Silkscreen-numbered keys `"1".."8"` per ADR-0010. Silicon names live in `alt:` (e.g. `pins["1"].alt: ["GND"]`). |
| Op-amp pin keys | Symbolic keys: `"IN+"`, `"IN-"`, `"OUT"`, `"V+"`, `"V-"`. ADR-0010 does not bite — op-amp symbols don't show pin numbers. |
| Cross-page label glyph | Schemdraw arrow with text annotation (`SIGNAL ▶ p2`). Unambiguous about direction; degrades well in monochrome. |
| CLI shape for multi-page output | `--out main.svg` auto-suffixes to `main-p1.svg`, `main-p2.svg`, … Single-page output keeps `main.svg` (no suffix), preserving v0.1 behaviour. |
| Cross-page net detection vs declaration | Detection — flattener inspects each net's pin list and the placements' `page:` assignments. No user-authored `cross-page-nets:` block. |

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.

## Implementation log

<!-- append-only; one line per task closure -->
- 2026-05-14 — TASK-110 closed (ADRs filed: 0). Effort actual: XS. Notes: all proposed defaults from IDEA-008/009 accepted verbatim; bundle-vs-split overridden to bundled per epic existence.
- 2026-05-14 — TASK-111 closed (ADRs filed: 0). Effort actual: Small. Notes: RULE_RC_LOW_PASS (id 11); R-on-row-0, C-on-row-1 in synthetic region `rc-low-pass-<sorted-pair>`.
- 2026-05-14 — TASK-112 closed (ADRs filed: 0). Effort actual: Small. Notes: RULE_RC_HIGH_PASS (id 12); mirror of low-pass — C-in-series on row 0, R-to-GND on row 1.
- 2026-05-14 — TASK-113 closed (ADRs filed: 0). Effort actual: Small. Notes: RULE_CC_DECOUPLING (id 13); pair detection requires shared two-net membership (POWER rail + GND); singleton caps preserved via RULE_DECOUPLING_CAP.
- 2026-05-14 — TASK-114 closed (ADRs filed: 0). Effort actual: Small. Notes: RULE_RR_VOLTAGE_DIVIDER (id 14); discriminator regex `/^(V?REF\|SENSE\|ADC\|DIV\|TAP)/i` or `role: divider` annotation. Kernel reserves `divider-ambiguous` reason code; ERC catalogue entry rides with the Phase 2/3 ERC work.
- 2026-05-14 — TASK-115 closed (ADRs filed: 0). Effort actual: Small. Notes: `sub-blocks:` + `instances:` schema with named-port map; validator gains S6 (nested) + S7 (undeclared instance/port). Netgraph golden hash bumped.
- 2026-05-14 — TASK-116 closed (ADRs filed: 0). Effort actual: Small. Notes: `flatten_sub_blocks(circuit)` added; `NetGraph.from_yaml_dict` auto-flattens transparently. Refdes minted `<local>_<instance>` per frozen decision.
- 2026-05-14 — TASK-117 closed (ADRs filed: 0). Effort actual: Small. Notes: E11/E12/E13/E14 sub-block ERC + E15 divider-ambiguity. Catalogue entries in `rules.json`. CHECK_TABLE grew from 15 → 20 codes.
- 2026-05-14 — TASK-118 closed (ADRs filed: 0). Effort actual: Small. Notes: meta-yml sidecar gains `instances:` block listing each instance's sub-block, label, and constituent refdes. Renderer hands the flat shadow to the kernel. Schemdraw bounding-box rectangle deferred as Schemdraw API task.
- 2026-05-14 — TASK-119 closed (ADRs filed: 0). Effort actual: Small. Notes: tutorial step 3 rewritten end-to-end against first-class `sub-blocks:` + `instances:` syntax (`led_indicator` sub-block, three instances `PWR`/`BT`/`ERR`); circuit-yaml.md gains a "Sub-blocks and instances" section with the frozen-decisions contract; layout.md gains an "inline-box mode" section. Fixed a counting regression in renderer meta-yml: `total:` now reports flat-component count rather than pre-flatten `len(circuit['components'])`.
- 2026-05-14 — TASK-120 closed (ADRs filed: 1 — ADR-0015). Effort actual: Medium. Notes: `actives.py` ships `bjt_npn` + `bjt_pnp` with per-pin `role:` ("base"/"collector"/"emitter") on the same dict that carries `side`/`type`/`direction`. Two new kernel rules — `RULE_BJT_TO_GND` (id 15) and `RULE_RESISTOR_WITH_BJT` (id 16) — only the **base-drive** resistor attaches to the BJT (collector / emitter resistors fall through to pull-up or escalate, avoiding the multi-attach rubric overlap). ADR-0015 records the canonical-slot decision (right-column next-free, mirroring the LED row convention) and the v1 narrow-scope tradeoff for multi-transistor topologies. Tutorial / gallery rendering and the active-device ERC rules ride on TASK-121..123.
- 2026-05-14 — TASK-121 closed (ADRs filed: 0). Effort actual: Small. Notes: `ics.py` ships `ic/555` with silkscreen-pin keying `"1".."8"` and silicon names in `pins.X.alt:` per ADR-0010. Registry gains a `metadata.type:` override mechanism so `ics.py:ic_555` registers as `ic/555` (singular). Validator's S5 check now consults `alt:` lists, so `T1.GND` resolves to `T1.1`. Kernel gains `RULE_GENERIC_IC` (id 17) for multi-pin ICs — same dominant-side-pick as the I²C sensor rule. Op-amp profile rides on TASK-122; pin-naming-drift ERC warning rides on TASK-123.
- 2026-05-14 — TASK-122 closed (ADRs filed: 0). Effort actual: XS. Notes: `ics.py` extended with `ic/opamp_dual_supply` (symbolic pin keys `IN+`/`IN-`/`OUT`/`V+`/`V-`; ADR-0010 doesn't apply because op-amp symbols have no pin numbers). `V+`/`V-` are unconditionally `direction: in` — TASK-123's power-pin-floating ERC rule depends on this invariant. Shares `RULE_GENERIC_IC` with the 555. Non-inverting buffer fixture renders in left-column (dominant-side resolves there: 2 left pins vs 1 right).
- 2026-05-14 — TASK-123 closed (ADRs filed: 0). Effort actual: Medium. Notes: Three active-device ERC rules — E16 (BJT pin role unset, error), E17 (op-amp power pin floating, error), E18 (555 pin-naming drift, warning). Catalogue entries in `rules.json`. CHECK_TABLE grew 20 → 23. ERC rules read `metadata.kind` per the project's category-lint contract, so the op-amp profile's `kind:` changed from `"ic"` to `"opamp"` and the 555's to `"timer"` for semantic discrimination. 7 new tests under `tests/erc/`; erc-checks.md gains E11..E18 doc sections.
- 2026-05-14 — TASK-124 closed (ADRs filed: 0). Effort actual: Small. Notes: `pages:` partition lands in `layout.schema.json` (top-level array of `{name, title?}` plus per-placement `page:` field). Two new layout-validator checks: `layout-pages-duplicate-name`, `layout-page-undeclared`. `Placement` and `LayoutResult` gain `page` round-trip; page survives topology-fingerprint mismatches (it's user-authored rendering metadata, independent of slot re-classification). Attached components inherit the anchor's page so RWL/RWB pairs never split across pages. Byte-identical coexistence for v0.1 layouts: no `pages:` block ⇒ no emitted `pages:` line and no `page:` field. 11 new tests across schema/ and layout/; layout.md gains a "Pages partition" doc section.
- 2026-05-14 — TASK-125 closed (ADRs filed: 0). Effort actual: Medium. Notes: multi-page render driver via two small helpers — `_emit_pages_or_single` (single-vs-multi decision) and `_filter_to_page` (per-page LayoutResult + RouterResult construction, drops cross-page wires). Each page reuses the existing `_emit_svg`; no SVG emission code duplication. `RenderResult.svg_paths` lists every SVG written; `svg_path` aliases the first for backwards-compat. `.layout.yml` and `.meta.yml` stay singletons (whole-circuit provenance). CLI `--out` help updated. 6 new tests in `tests/render/test_multi_page_driver.py` covering single-page (no suffix), two/three-page, singleton sidecars, determinism, and independent-subsystem rendering. Cross-page wires (where endpoints land on different pages) are silently dropped per-page — TASK-126 adds the boundary label rendering.
- 2026-05-14 — TASK-126 closed (ADRs filed: 0). Effort actual: Small. Notes: cross-page net labels via `_cross_page_labels_for(page, layout, router_result)` (walks the full route list, emits label dicts at each cross-page endpoint, dedup key `(net, ref, pin, other_page)`). `_emit_svg` grows an optional `cross_page_labels` parameter; emits a stub line + `▶`/`◀` Unicode glyph + `<net> ▶ <other>` text. ViewBox extended ±2 cells around labels so glyphs don't spill. Schemdraw-arrow decision became SVG-primitive-arrow without changing the user-facing contract (v0.1's emit doesn't use Schemdraw). 5 new tests in `tests/render/test_cross_page_labels.py`.
- 2026-05-14 — TASK-127 closed (ADRs filed: 0). Effort actual: Small. Notes: four cross-page ERC rules — E19 (page declared but empty, warning), E20 (page referenced but undeclared, error), E21 (cross-page net invisible on one side, error), E22 (excessive cross-page net count, warning). ERC `run()` grows a `layout=` kwarg; `_Context` plumbs the parsed `.layout.yml`. Renderer passes the user's *input* layout. Threshold knob `meta.erc.cross-page-threshold` (default 6). CHECK_TABLE grew 23 → 27. Catalogue entries in `rules.json`. 7 new tests in `tests/erc/test_cross_page_rules.py`; erc-checks.md gains E19..E22 sections.
- 2026-05-14 — TASK-128 closed (ADRs filed: 0). Effort actual: Small. Notes: voltage-divider gallery entry rendered end-to-end via TASK-114's `RULE_RR_VOLTAGE_DIVIDER`. `ADC_IN` tap-net matched the regex `/^(V?REF|SENSE|ADC|DIV|TAP)/i`, kernel minted region `divider-ADC_IN`, R1/R2 placed on rows 0/1. README rewritten with inline SVG + BOM table. Two **pre-existing** layout-schema gaps fixed (broaden `label` enum to free-form string, add patterns for `rc-(low|high)-pass-*` / `cc-decoupling-*` / `divider-*` regions). Tutorial meta.yml tmpdir-drift bug noted but not fixed (out of scope).
- 2026-05-14 — TASK-129 closed (ADRs filed: 1 — ADR-0016). Effort actual: Medium. Notes: common-emitter amplifier gallery entry. Surfaced an ADR-0015 coverage gap on the first real CE topology — base-drive R was handled, but the collector load `R_C` (rail → R → Q.C) escalated through the pull-up rule's anchor-pin check (Q.C is POWER_INPUT not GPIO), and the emitter degeneration `R_E` (Q.E → R → GND) had no matching rule at all. Filed ADR-0016 and added two kernel rules: `RULE_BJT_LOAD` (id 18) and `RULE_BJT_DEGENERATION` (id 19), each minting a per-BJT synthetic region (`bjt-load-<ref>`, `bjt-degen-<ref>`). Layout schema gains the two region patterns. Circuit values picked for a ~1 mA bias / Av ≈ 10 audio-band amp: VCC = 5 V, R_B1 = 47 k, R_B2 = 10 k, R_C = 2.7 k, R_E = 270 Ω, C_IN/C_OUT = 10 µF. 4 new kernel tests; gallery regression diff (`scripts/check_gallery_regression.py`) green. Tutorial meta.yml tmpdir-drift bug reverted again (still out of scope, recurs every rebaseline).
- 2026-05-14 — TASK-130 closed (ADRs filed: 1 — ADR-0017). Effort actual: Small. Notes: 555 monostable gallery entry — first multi-pin IC gallery example. R_T + C_T match `RULE_RC_LOW_PASS` cleanly (timing pair, 100 kΩ / 10 µF → t ≈ 1.1 s). R_TRIG (pull-up between VCC and U1.2/TRIG) escalated `no-canonical-rule` because `_shape_meta_pullup` only accepted GPIO/INPUT_ONLY as anchor types. Filed ADR-0017 and widened the anchor to also accept SIGNAL_INPUT, with two refinements: (a) two-pass search (MCU first, IC second) to preserve placement for mixed-anchor circuits; (b) rail-skip so the anchor reflects the resistor's signal-side terminal — needed because the 555's RESET pin (SIGNAL_INPUT, tied to VCC for monostable) shares the VCC net and would otherwise be picked as the anchor in preference to TRIG. Silkscreen-pin form used throughout to keep E18 silent. 2 new layout tests in `tests/layout/test_pullup_ic_anchor.py`. 9/9 components placed; gallery regression green. ERC clean (1 expected E9 warning).
- 2026-05-14 — TASK-131 closed (ADRs filed: 0). Effort actual: XS. Notes: op-amp non-inverting buffer gallery entry — first dual-rail-supply gallery example. Unity-gain feedback (A1.OUT ↔ A1.IN-) collapsed onto a single `BUF_OUT` net (mirrors `tests/components/test_opamp_profile.py::_opamp_buffer_circuit`) to keep E10 (multi-net-pin) quiet. Two USB-C jacks provide V+ (J1.VBUS → V_PLUS) and V- (J2.VBUS → V_MINUS) supplies — the USB-C profile's POWER-typed pin doesn't model polarity; the negative-rail framing is in the README prose. One 100 nF decoupling cap per rail (C_VCC on V_PLUS, C_VEE on V_MINUS); they don't pair into C+C (different rails) and each lands on its own `bus-<rail>` row via `RULE_DECOUPLING_CAP` — correct behaviour, no kernel diff. All 8 components placed; ERC clean (2 expected E9 warnings on the two USB-C inputs). No new tests beyond the gallery regression script's coverage.
- 2026-05-14 — TASK-132 closed (ADRs filed: 0). Effort actual: Small. Notes: multi-page split gallery entry. Reuses the common-emitter amplifier circuit unchanged; only `layout.yml` differs (adds `pages:` block + per-component `page:` assignments). Page partition: input section (U1, J1, J_IN, C_IN, R_B1, R_B2) on p1; active section (Q1, R_C, R_E, C_OUT, J_OUT) on p2. Three nets cross the boundary (VCC, GND, BASE) — under TASK-127's six-net threshold. The renderer emits `multi-page-split-p1.svg` and `multi-page-split-p2.svg`; `_cross_page_labels_for` emits the GND cross-page glyph on both pages (`GND ▶ p2` / `p1 ◀ GND`). VCC and BASE also span the boundary but their non-jack endpoints sit in v0.1 uncoordinatised synthetic regions (`divider-BASE`, `bjt-load-Q1`) so the router doesn't emit routed wires for them and the label glyph stays silent for those two — documented in the README as a known trade-off. Gallery regression script (`scripts/check_gallery_regression.py`) extended: `_artefact_paths` now returns a list of `<base>-p<N>.svg` paths when no single `<base>.svg` exists but per-page SVGs do; `_check_one` pairs them positionally with the regen output. Existing single-SVG path preserved (5 existing regression-script tests pass). 9/9 gallery circuits regenerate identically; full suite 519 passes.
- 2026-05-14 — TASK-133 closed (ADRs filed: 0). Effort actual: XS. Notes: docs-only final pass closing EPIC-014. layout.md's canonical-slot table extended from 8 rows to 19 (added rule IDs 11–19 from EPIC-014 phases 1/3/4/6); pull-up row updated with ADR-0017's IC SIGNAL_INPUT widening; "synthetic regions are uncoordinatised in v0.1" note added. index.md ERC count corrected from "15-rule catalog (S1–S5 + E1–E10)" to "27-rule catalog (S1–S7 + E1–E22)"; status paragraph rewritten to mention sub-blocks, twelve canonical-slot rules, and multi-page rendering. erc-checks.md gains S6/S7 section (sub-block schema validation, TASK-117); header public-contract reminder updated to S1–S7 / E1–E22. Gallery README (docs/users/examples/README.md) source-column links re-pointed at the closed EPIC-014 tasks (TASK-128..132); blocked-on prose removed since all five entries ship with committed SVGs. IDEA-008/009 archive-reason check passed (already named EPIC-014). All edited files lint clean.
