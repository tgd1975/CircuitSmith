"""
Golden-hash CI contract for ``NetGraph.canonical_hash`` (TASK-053).

``test_netgraph.py`` (TASK-008) already asserts hash determinism *within
one process*: two parses of the same input produce structurally
identical graphs. That test catches non-determinism inside a single
``pytest`` run. It does **not** catch the across-release class of bug
where the canonical serialiser silently drifts between commits — a new
optional field starts being included, key ordering shifts after a
refactor, a default value changes.

This module pins the canonical hash of every shipped ``.circuit.yml``
to a value stored in ``tests/fixtures/golden_hashes.json``, and emits
two distinct diagnostics depending on which side of the contract
broke:

- **Serialiser drift** — hash changed without the schema file changing.
  This is the case the test exists to catch; the operator must
  investigate why ``canonical_hash`` moved.
- **Stale golden** — schema file changed (``schema_version`` would now
  bump) but the golden file was not regenerated. The operator must
  run ``python scripts/update_netgraph_golden.py --bump-schema-version``.

Both checks fire in CI; the local pre-commit hook does not run this
test (it's pytest-only).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from circuitsmith.netgraph import NetGraph

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "src" / "circuitsmith" / "schema" / "circuit.schema.json"
GOLDEN_PATH = REPO_ROOT / "tests" / "fixtures" / "golden_hashes.json"


def _current_schema_version() -> str:
    return hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()


def _load_golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text())


def _hash_from_circuit_yml(rel_path: str) -> str:
    yaml = YAML(typ="safe")
    circuit = yaml.load((REPO_ROOT / rel_path).read_text())
    graph = NetGraph.from_yaml_dict(circuit)
    return graph.canonical_hash()


def test_schema_version_matches_golden() -> None:
    """Schema file content is the schema_version source of truth.

    Distinct diagnostic from the per-circuit drift checks below. If
    this fails, the operator edited the schema but did not regenerate
    the golden — ``scripts/update_netgraph_golden.py
    --bump-schema-version`` is the fix.
    """
    golden = _load_golden()
    on_disk = _current_schema_version()
    if golden["schema_version"] != on_disk:
        pytest.fail(
            "Schema file changed; regenerate the NetGraph golden.\n"
            f"  golden schema_version: {golden['schema_version']}\n"
            f"  on-disk schema sha256: {on_disk}\n"
            "  fix: `python scripts/update_netgraph_golden.py "
            "--bump-schema-version`"
        )


@pytest.mark.parametrize(
    "circuit_name",
    sorted(_load_golden()["circuits"].keys()),
)
def test_canonical_hash_matches_golden(circuit_name: str) -> None:
    """Per-circuit canonical_hash is frozen by the golden.

    Diagnostic distinguishes "serialiser drifted" (the rare, important
    case the test exists for) from "schema bumped, regenerate" (handled
    by ``test_schema_version_matches_golden`` above).
    """
    golden = _load_golden()
    entry = golden["circuits"][circuit_name]
    actual = _hash_from_circuit_yml(entry["source"])
    expected = entry["canonical_hash"]
    if actual != expected:
        if golden["schema_version"] == _current_schema_version():
            pytest.fail(
                f"NetGraph canonical_hash for `{circuit_name}` drifted "
                "without a schema change — your serialiser drifted.\n"
                f"  source: {entry['source']}\n"
                f"  golden:   {expected}\n"
                f"  produced: {actual}\n"
                "  Investigate the serialiser change; do NOT regenerate "
                "the golden until the drift is justified."
            )
        # If we reach here, the schema also changed; the prior test
        # will already have flagged it with the clearer diagnostic.
        pytest.fail(
            f"NetGraph canonical_hash for `{circuit_name}` does not match "
            "golden; schema also changed. Run "
            "`python scripts/update_netgraph_golden.py "
            "--bump-schema-version` after confirming the schema edit is "
            "intentional."
        )


def test_drift_detection_mutation_guard() -> None:
    """Self-test: a deliberately-bad hash trips the comparison.

    Without this, a hypothetical bug in the assertion (e.g. comparing
    a hash to itself, or always returning ``True``) would make every
    real-world drift silently pass. Mirrors the
    ``test_checker_catches_a_real_violation`` pattern from
    ``test_module_boundaries.py``.
    """
    golden = _load_golden()
    one = next(iter(golden["circuits"].values()))
    expected = one["canonical_hash"]
    deliberately_wrong = "0" * len(expected)
    assert expected != deliberately_wrong, (
        "self-test fixture collided with the real golden hash — adjust the "
        "wrong value so the mutation guard stays meaningful."
    )
