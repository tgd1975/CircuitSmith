#!/usr/bin/env python3
"""
Regenerate ``tests/fixtures/golden_hashes.json`` for TASK-053.

The golden file freezes:

- ``schema_version`` — SHA-256 of ``src/circuitsmith/schema/circuit.schema.json``.
  This is the "schema version" the dossier's TASK-053 spec calls for. Using
  the schema file's content hash rather than a hand-maintained semver string
  means the schema_version naturally bumps when the schema is edited.
- For each shipped circuit (under ``data/``), the ``canonical_hash`` of the
  ``NetGraph`` built from it.

The test ``tests/test_netgraph_golden.py`` fails CI if either:

- A circuit's ``canonical_hash`` drifts while ``schema_version`` is unchanged
  (= serialiser drift), OR
- The schema file changed (= ``schema_version`` would need to bump) but the
  golden file wasn't regenerated.

Operator flow:

1. Make a deliberate schema change.
2. Run ``python scripts/update_netgraph_golden.py --bump-schema-version``.
3. Commit the regenerated ``golden_hashes.json`` alongside the schema change.

Refusing ``--bump-schema-version`` when the on-disk schema hash already
matches the golden's ``schema_version`` keeps the operator honest: you only
regenerate when the schema actually moved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from ruamel.yaml import YAML

from circuitsmith.netgraph import NetGraph

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "src" / "circuitsmith" / "schema" / "circuit.schema.json"
GOLDEN_PATH = REPO_ROOT / "tests" / "fixtures" / "golden_hashes.json"

CIRCUITS: dict[str, str] = {
    "esp32": "data/esp32.circuit.yml",
    "nrf52840": "data/nrf52840.circuit.yml",
}


def current_schema_version() -> str:
    """SHA-256 of the on-disk schema JSON. The TASK-053 schema_version proxy."""
    return hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()


def compute_canonical_hashes() -> dict[str, dict[str, str]]:
    """Build a NetGraph from each shipped circuit and return its canonical_hash."""
    yaml = YAML(typ="safe")
    out: dict[str, dict[str, str]] = {}
    for name, rel in CIRCUITS.items():
        circuit = yaml.load((REPO_ROOT / rel).read_text())
        graph = NetGraph.from_yaml_dict(circuit)
        out[name] = {"source": rel, "canonical_hash": graph.canonical_hash()}
    return out


def load_golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text())


def write_golden(payload: dict) -> None:
    GOLDEN_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--bump-schema-version",
        action="store_true",
        help=(
            "Acknowledge that the schema file has changed and regenerate the "
            "golden. Refused when the on-disk schema hash already matches the "
            "golden's schema_version — the operator is then asking to "
            "regenerate without an actual schema bump, which is the silent-"
            "drift case the test exists to catch."
        ),
    )
    args = parser.parse_args(argv)

    on_disk = current_schema_version()
    existing = load_golden()
    recorded = existing.get("schema_version")

    schema_changed = on_disk != recorded

    if not schema_changed and args.bump_schema_version:
        print(
            "refusing: schema hash unchanged "
            f"(on-disk and golden both {on_disk[:12]}...). "
            "If you need to fix the golden after a serialiser change that "
            "intentionally drifted the canonical_hash without a schema "
            "edit, you are about to silence the regression guard. "
            "Investigate the drift first; do not regenerate.",
            file=sys.stderr,
        )
        return 2

    if schema_changed and not args.bump_schema_version:
        print(
            f"refusing: schema file changed (was {recorded[:12]}..., "
            f"now {on_disk[:12]}...) but --bump-schema-version was not "
            "passed. Pass the flag once you have verified the schema edit "
            "is intentional.",
            file=sys.stderr,
        )
        return 2

    new = dict(existing)
    new["schema_version"] = on_disk
    new["circuits"] = compute_canonical_hashes()
    write_golden(new)
    print(f"wrote {GOLDEN_PATH.relative_to(REPO_ROOT)} (schema_version={on_disk[:12]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
