---
subsystem: erc-engine
covers: src/circuitsmith/erc_engine.py, erc_report.py, knowledge/
---

# ERC engine — test plan

The ERC engine runs the electrical rule checks **strictly pre-layout**
(ADR-0005): a malformed circuit never reaches the router. It is three
pieces — the engine (`erc_engine.py`, the `CHECK_TABLE` + predicates),
the report writer (`erc_report.py`), and the rule catalog
(`knowledge/`). The headline test concern is **rule coverage**: does
every check code in `CHECK_TABLE` have a fixture that actually triggers
it?

Covers [`erc_engine.py`](../../../src/circuitsmith/erc_engine.py),
[`erc_report.py`](../../../src/circuitsmith/erc_report.py), and
[`knowledge/`](../../../src/circuitsmith/knowledge/) (the catalog
validator is detailed in [`schema.md`](schema.md)).

Test files covering this subsystem:

```pytest
tests/test_erc_engine.py
tests/test_erc_report_enrichment.py
tests/test_renderer_erc.py
tests/erc/test_sub_block_rules.py
tests/erc/test_active_device_rules.py
tests/erc/test_cross_page_rules.py
```

## Inputs and outputs

- **Input** — `run(graph, circuit, profiles=…, layout=…)`: the NetGraph,
  the circuit dict (for `meta.erc` severity overrides), profiles, and
  optionally the layout (for the cross-page rules E19–E22).
- **Output** — a list of `Finding(check, ref, pin, net, severity,
  message)`. `CHECK_TABLE` maps each code to its default severity.
  S-class errors short-circuit the E-class run.

## Unit tests

`tests/test_erc_engine.py` (TASK-022) is the core. It asserts the
`CHECK_TABLE` holds all 27 codes, that E9 defaults to `warning`, that
both shipped circuits are ERROR-free with E9 surfacing as a warning, and
that the dormant checks emit nothing without qualifying components. It
then drives one targeted fixture per active predicate (see the coverage
table below). The three-level severity override system (global
`meta.erc`, per-component, per-net, most-severe-wins) is exercised
end-to-end on the shipped ESP32 circuit.

The EPIC-014 rule families have their own files:
`tests/erc/test_sub_block_rules.py` (E11–E15),
`tests/erc/test_active_device_rules.py` (E16–E18),
`tests/erc/test_cross_page_rules.py` (E19–E22).

### Rule-coverage table

Which `CHECK_TABLE` codes have a triggering fixture today:

| Code | Meaning | Triggering fixture | Where |
|---|---|:--:|---|
| S1 | unconnected required pin | ✓ | `test_S1_fires_on_unconnected_required_pin` (synthetic profile with a `required:` pin) |
| S2 | dangling net | ✓ | `test_S2_fires_on_dangling_net` |
| S3 | duplicate net name | ✓ | `test_S3_fires_on_duplicate_net_name` (warning) |
| S4 | unknown component type | ✓ | schema layer — `test_schema_validation.py` |
| S5 | unknown pin | ✓ | schema layer — `test_schema_validation.py` |
| E1 | floating input | ✓ | `test_E1_fires_on_floating_button_input` (+ pass case) |
| E2 | LED without series resistor | ✓ | `test_E2_fires_on_led_without_resistor` |
| E3 | resistor overcurrent | ✓ | `test_E3_fires_on_resistor_too_small…` (warning) |
| E4 | INPUT_ONLY pin driven | ✓ | `test_E4_fires_clean_with_no_s_class_gate` (path-routed anode + `pull:` keep S2/E1/E2 quiet) |
| E5 | strapping pin unpulled | ✓ | `test_E5_fires_on_unpulled_strapping_pin…` |
| E6 | IC VCC pin undecoupled | ✓ | `test_E6_fires_on_non_mcu_ic_without_decoupling_cap` (synthetic `kind: ic` + `POWER` pin) |
| E7 | I²C net without pull-up | ✓ | `test_E7_fires_on_i2c_net_without_pullup` |
| E8 | LED current-budget exceeded | ✓ | `test_E8_fires_when_led_current_exceeds_total_budget` (synthetic low-budget MCU) |
| E9 | USB VBUS without protection | ✓ | shipped circuits (warning) |
| E10 | pin shared across two nets | ✓ | `test_E10_fires_when_pin_in_two_nets` |
| E11–E15 | sub-block + divider ambiguity | ✓ | `tests/erc/test_sub_block_rules.py` |
| E16–E18 | active-device (BJT/op-amp/555) | ✓ | `tests/erc/test_active_device_rules.py` |
| E19–E22 | cross-page | ✓ | `tests/erc/test_cross_page_rules.py` |

## Integration tests

`tests/test_renderer_erc.py` (TASK-023): ERC runs inside the renderer
pipeline pre-layout, and an ERROR-level finding aborts the render before
the router stage — the contract documented from the renderer side in
[`renderer.md`](renderer.md).

## Golden / snapshot tests

`tests/test_erc_report_enrichment.py` (TASK-027) pins the report
writer's catalog-enriched output (rule text, `source_of_truth` links).
The shipped per-target `erc-report.md` files are golden-checked by the
`check_erc_reports.py` staleness gate ([`ci-gates.md`](ci-gates.md)),
**with the auto-stamped header date normalised** so the gate is stable
across days (the same normalisation the gallery gate now uses).

## Property / fuzz tests

**None.** Each rule is triggered by a hand-built minimal fixture, not by
generated circuits. Rationale: targeted fixtures give precise
rule-by-rule signal; fuzzing would muddy which predicate fired.

## Performance budget

**No budget.** ERC is linear in nets/pins and trivial on every shipped
circuit.

## Known uncovered cases

- **S1, E4, E6, E8 — now covered (TASK-134).** Previously the most
  actionable gaps the epic surfaced (originally TASK-090 candidates):
  S1 was only *avoided* by other fixtures, E6/E8 had no triggering
  fixture, and E4 had only a predicate-path test masked by an S-class
  gate. TASK-134 added one targeted fixture per code in
  `tests/test_erc_engine.py` — S1 and E6 via synthetic profiles (a
  `required:` pin; a `kind: ic` IC with a `POWER` pin — neither shape
  exists in the day-one corpus), E8 via a synthetic low-budget MCU, and
  E4 via a clean fixture (path-routed anode plus `pull:`) that keeps the
  circuit structurally valid so the E-class run proceeds and E4 reports
  in isolation. See the rule-coverage table above.
- **Catalog ↔ engine consistency at runtime.** The catalog validator
  checks `enforced_by` codes against `CHECK_TABLE` statically
  ([`schema.md`](schema.md)), but no test asserts every *fired* finding
  resolves to a catalog row. Rationale: the static check is a strong
  proxy; a runtime cross-check is a lower-priority follow-up.

## Cadence

| Test file | PR | Nightly | Release |
|---|:--:|:--:|:--:|
| `tests/test_erc_engine.py` | ✓ | | |
| `tests/test_erc_report_enrichment.py` | ✓ | | |
| `tests/test_renderer_erc.py` | ✓ | | |
| `tests/erc/test_sub_block_rules.py` | ✓ | | |
| `tests/erc/test_active_device_rules.py` | ✓ | | |
| `tests/erc/test_cross_page_rules.py` | ✓ | | |

All run at PR-time. The catalog's online URL-reachability check (catalog
validator) is the only ERC-adjacent piece designated for a nightly tier
that does not yet exist — see [`schema.md`](schema.md).
