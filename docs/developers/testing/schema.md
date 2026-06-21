---
subsystem: schema
covers: src/circuitsmith/schema/ + rule-catalog validation
---

# Schema — test plan

The schema layer is the pipeline's front door: it rejects malformed or
nonsensical `.circuit.yml` / `.layout.yml` before any downstream stage
runs. It is two-staged — a JSON Schema pass (structural, the `schema` /
`layout-schema` check codes) followed by post-schema *semantic* checks
that JSON Schema can't express (`S4`/`S5` for circuits, `S6`/`S7` for
sub-blocks, `layout-attached-to-unknown` and the `pages` cross-checks for
layouts). The rule-catalog validator is folded in here because the
catalog is itself a schema-validated artefact.

Covers [`src/circuitsmith/schema/`](../../../src/circuitsmith/schema/)
(`validator.py`, `registry.py`, the `*.schema.json` files) and
[`knowledge/validate_catalog.py`](../../../src/circuitsmith/knowledge/validate_catalog.py).

Test files covering this subsystem:

```pytest
tests/test_schema_validation.py
tests/test_layout_schema.py
tests/schema/test_sub_blocks_schema.py
tests/schema/test_pages_schema.py
tests/test_validate_catalog.py
tests/test_components.py
tests/components/test_555_profile.py
tests/components/test_bjt_profiles.py
tests/components/test_opamp_profile.py
tests/test_schema_pre_commit.py
```

## Inputs and outputs

- **Input** — a circuit or layout dict (or a YAML file via
  `validate_file`), plus the component `profiles` registry loaded by
  `registry.load_profiles()`. The catalog validator takes the parsed
  `rules.json`.
- **Output** — a list of `Finding(check, ref, pin, message, …)`; an
  empty list means valid. Check codes are the contract: `schema`, `S4`,
  `S5`, `S6`, `S7` (circuits); `layout-schema`,
  `layout-attached-to-unknown`, `layout-pages-duplicate-name`,
  `layout-page-undeclared` (layouts).

## Unit tests

**Circuit schema** (`tests/test_schema_validation.py`, TASK-005):
the valid minimal circuit passes; `S4` fires on an unknown component
type, `S5` on an unknown pin; all three connection forms validate; the
schema `oneOf` rejects a net mixing `pins` and `path`; the three
top-level sections (`meta`/`components`/`connections`) are each required
(parametrized); and `validate_file` round-trips real YAML via
`ruamel.yaml`.

**Layout schema** (`tests/test_layout_schema.py`, TASK-013): a clean
`layout/v1` validates; a missing `topology-fingerprint` fails (catches
stale layouts from a pre-fingerprint kernel); `attached-to` pointing at
a non-existent placement surfaces `layout-attached-to-unknown`; an
attached placement carrying redundant index fields (`row`/`col`) is
rejected; the `free` region requires `gx`/`gy`; region-anchor and
capacity overrides validate; the `path-of-*` and `bus-*` region
patterns validate; an unknown `schema` version is rejected.

**Sub-blocks** (`tests/schema/test_sub_blocks_schema.py`, TASK-115):
the worked RC-pair validates; a nested sub-block reference is rejected
by the component-type regex `^[a-z][a-z0-9_]*/[a-z0-9_]+$`; `S7` fires
on an undeclared sub-block reference and on an undeclared port; flat
circuits and mixed flat+sub-block circuits still validate.

**Pages** (`tests/schema/test_pages_schema.py`, TASK-124): layouts
without `pages:` still validate; named pages + per-placement assignment
validate; duplicate page names (`layout-pages-duplicate-name`),
undeclared page references (`layout-page-undeclared`), an empty `pages:`
list, and invalid name patterns are each rejected.

**Rule catalog** (`tests/test_validate_catalog.py`, TASK-025): the
shipped `rules.json` passes in offline mode; the four offline checks
each fail on a planted defect — `_check_format` (missing field),
`_check_enforced_by` (unknown code + a `CHECK_TABLE` code with no catalog
row), `_check_disclaimers` (heuristic without the disclaimer phrase),
`_check_category_lint` (a `.category ==` read outside `layout/` is
flagged; inside `layout/` is allowed). The CLI returns 0 on the clean
catalog and 1 on a format failure.

**Component profiles** (`tests/test_components.py` and
`tests/components/test_{555,bjt,opamp}_profile.py`): connector-factory
edge cases, and profile auto-discovery + schema validation + pin keying
for the active-device profiles (these straddle schema and the layout
kernel — see [`layout-kernel.md`](layout-kernel.md) for the BJT rule
half of `test_bjt_profiles.py`).

## Integration tests

`tests/test_schema_pre_commit.py` (TASK-052) exercises
`scripts/check_circuit_schema.py`, the gate that re-validates every
committed `.circuit.yml` at pre-commit and in CI — the same check from
the contributor's side rather than the library API's. It is also
inventoried under [`ci-gates.md`](ci-gates.md); it lives in both because
it is the schema layer's CI manifestation.

## Golden / snapshot tests

**None as snapshots.** The closest is "the shipped `rules.json`
validates clean offline" (`test_shipped_catalog_passes_offline`), which
pins the real artefact rather than a captured snapshot. Schema findings
are asserted by check-code, not by golden output.

## Property / fuzz tests

**None.** Validation is asserted on hand-written valid and
deliberately-broken fixtures, not generated input. See *Known
uncovered*.

## Performance budget

**No budget.** Validation is fast on every shipped circuit; no number is
pinned because nothing has approached a concern.

## Known uncovered cases

- **`S6` (slash-form sub-block name collision).** The nested-sub-block
  test exercises the *structural* type-regex defence; `S6`, the
  cross-reference defence for a sub-block deliberately named in the
  `foo/bar` slash form, has no direct triggering fixture. Rationale: the
  regex makes the collision hard to express, so `S6` is a belt-and-braces
  check; worth a fixture but not a blocker — a candidate for TASK-090.
- **`meta.schema.json` in isolation.** The meta sidecar schema is
  exercised transitively through the renderer's meta output, not by a
  dedicated schema unit test. Rationale: meta is renderer-authored, so
  the renderer tests are the natural owner; noted so the gap is explicit.
- **No fuzzing of structurally-valid-but-odd YAML.** Rationale: the
  check-code fixtures cover the failure modes that matter; randomised
  YAML generation is lower-value than property tests on the kernel.
- **Catalog URL reachability.** The online `enforced_by`-URL check is
  skipped in the offline PR-time tests; it only runs online. Rationale:
  network reachability is a nightly/release concern, not a per-PR gate
  (see *Cadence*).

## Cadence

| Test file | PR | Nightly | Release |
|---|:--:|:--:|:--:|
| `tests/test_schema_validation.py` | ✓ | | |
| `tests/test_layout_schema.py` | ✓ | | |
| `tests/schema/test_sub_blocks_schema.py` | ✓ | | |
| `tests/schema/test_pages_schema.py` | ✓ | | |
| `tests/test_validate_catalog.py` | ✓ | | |
| `tests/test_components.py` | ✓ | | |
| `tests/components/test_555_profile.py` | ✓ | | |
| `tests/components/test_bjt_profiles.py` | ✓ | | |
| `tests/components/test_opamp_profile.py` | ✓ | | |
| `tests/test_schema_pre_commit.py` | ✓ | | |

All run at PR-time. The catalog validator's **online** URL-reachability
check is designated nightly in `ci.yml`, but no nightly workflow exists
yet — the PR-time run is offline-only (`CS_CATALOG_OFFLINE=1`). Wiring
the nightly online check is a candidate gap for TASK-090.
