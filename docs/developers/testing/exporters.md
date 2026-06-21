---
subsystem: exporters
covers: src/circuitsmith/export/
---

# Exporters — test plan

Two exporters turn a circuit into downstream artefacts: the BOM exporter
(Markdown + CSV) and the KiCad netlist exporter (`.net`). They are
deliberately decoupled (ADR-0004): `bom_exporter` walks `components`
directly, `netlist_exporter` walks the `NetGraph`, and they never reach
into each other. The one place they must agree — the `Value` field — is
pinned by a cross-check test.

Covers [`src/circuitsmith/export/`](../../../src/circuitsmith/export/).

Test files covering this subsystem:

```pytest
tests/test_bom_exporter.py
tests/test_netlist_exporter.py
tests/test_netlist_structure.py
```

## Inputs and outputs

- **BOM** — `export(circuit, profiles)` → `(markdown, csv)`. Markdown
  groups by variant with run-length-encoded ref ranges; CSV is one row
  per ref with a KiCad-importable `Value`.
- **Netlist** — `export(circuit, graph, profiles, source_path)` → KiCad
  `.net` S-expression text.

## Unit tests

**BOM** (`tests/test_bom_exporter.py`, TASK-031): variant grouping
(resistors by `value`, LEDs by `color`); run-length encoding that
collapses *consecutive* numeric suffixes to an en-dash range and never
spans a prefix change (`D1, R1–R3`); the Markdown and CSV shapes; the
KiCad `Value` column as a bare projection (no `Ω`, no unit); metadata
columns (datasheet/manufacturer present, footprint blank until the
profile field lands); `meta.title` fallback to `untitled`; and
determinism across two runs. Helpers `_condense_refs`, `_variant_key`,
`_variant_display`, `_variant_csv_value` are unit-tested directly.

**Netlist** (`tests/test_netlist_exporter.py`, TASK-033): named nets
keep their declared name; path-form later segments use the
content-addressed `NetGraph` name (`LED_PWR__R1_2__D1_A`); the
component block emits one `(comp …)` per ref in declaration order;
`(datasheet …)` is omitted when the profile has none and included when
it does; the `(value …)` matches the BOM CSV row-for-row (the
decoupling-seam cross-check); determinism across two runs; the `_escape`
and `_component_value` helpers.

## Integration tests

The netlist round-trip (`test_round_trip_preserves_pin_memberships`) is
an integration check across the exporter and `NetGraph`: it tokenises
and parses the emitted `.net` with a hand-rolled ~30-line S-expression
parser and asserts the reconstructed `{net → set(PinRef)}` equals
`graph.nets`. `test_round_trip_on_bus_form_collapses_to_one_net` pins
the bus-collapse invariant (a bus is one electrical net in KiCad,
however many stubs the renderer draws).

## Golden / snapshot tests

`tests/test_netlist_structure.py` (TASK-049) is a grammar-level
structural test over the committed `.net` artefacts. The shipped BOM +
netlist files are byte-golden-checked by the `check_exporters.py`
staleness gate ([`ci-gates.md`](ci-gates.md)); a legitimate change
requires re-running the exporters and committing the artefacts in the
same commit.

## Property / fuzz tests

**None.** Grouping, RLE, and round-trip are asserted on fixed fixtures.
Rationale: the round-trip test already provides a strong structural
guarantee on real topologies; generated input is lower-value here.

## Performance budget

**No budget.** Both exporters are linear and trivial on every shipped
circuit.

## Known uncovered cases

- **PartsLedger round-trip — known *manual* step, not an uncovered
  gap.** CircuitSmith reads from PartsLedger and the BOM is the natural
  hand-off, but there is no automated test against the external
  PartsLedger repo (cross-repo CI coupling is deliberately avoided). The
  round-trip is verified by hand today; the case for automating it
  strengthens once EPIC-012 ships a PartsLedger round-trip example, at
  which point a fixture-based (not live-repo) test becomes worthwhile.
- **Footprint column.** Emitted blank because no profile carries a
  footprint yet; the column exists for KiCad but is untested with real
  data. Rationale: nothing populates it — revisit when footprints land.
- **KiCad import acceptance.** That the `.net` *parses* is tested; that
  KiCad *imports* it cleanly was a one-off manual spot-check (TASK-034),
  not an automated gate. Rationale: driving the KiCad GUI in CI is out
  of scope; a release-time manual check is the control.

## Cadence

| Test file | PR | Nightly | Release |
|---|:--:|:--:|:--:|
| `tests/test_bom_exporter.py` | ✓ | | |
| `tests/test_netlist_exporter.py` | ✓ | | |
| `tests/test_netlist_structure.py` | ✓ | | |

All run at PR-time. The KiCad-import acceptance check is a manual
release-time step (TASK-034), and a future PartsLedger round-trip test
would be release-tier if it ever touches a live inventory.
