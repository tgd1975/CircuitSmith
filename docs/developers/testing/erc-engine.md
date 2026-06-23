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
| S1 | single-pin / floating net | ✗ | only *avoided* (`ANODE tied off`) — no direct trigger |
| S2 | dangling net | ✓ | `test_S2_fires_on_dangling_net` |
| S3 | duplicate net name | ✓ | `test_S3_fires_on_duplicate_net_name` (warning) |
| S4 | unknown component type | ✓ | schema layer — `test_schema_validation.py` |
| S5 | unknown pin | ✓ | schema layer — `test_schema_validation.py` |
| E1 | floating input | ✓ | `test_E1_fires_on_floating_button_input` (+ pass case) |
| E2 | LED without series resistor | ✓ | `test_E2_fires_on_led_without_resistor` |
| E3 | resistor overcurrent | ✓ | `test_E3_fires_on_resistor_too_small…` (warning) |
| E4 | INPUT_ONLY pin driven | ~ | predicate wired; no clean isolated trigger (S-class gates it) |
| E5 | strapping pin unpulled | ✓ | `test_E5_fires_on_unpulled_strapping_pin…` |
| E6 | IC VCC pin undecoupled | ✗ | dormant on shipped; needs a non-MCU IC with a VCC pin |
| E7 | I²C net without pull-up | ✓ | `test_E7_fires_on_i2c_net_without_pullup` |
| E8 | (electrical) | ✗ | no triggering fixture in the suite |
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

- **S1, E6, E8 have no triggering fixture; E4 only a predicate-path
  test.** This is the concrete output of the coverage table. Rationale,
  per code: S1 is structurally avoided by the other fixtures; E6 needs a
  non-MCU IC profile with a VCC pin (none in the day-one corpus); E8 has
  no minimal fixture authored; E4's clean trigger is masked because an
  S-class error gates the E-class run. All four are TASK-090 candidates
  — the most actionable gaps the whole epic surfaced.
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
