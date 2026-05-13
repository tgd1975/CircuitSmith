"""Rule catalog — the knowledge layer that pairs with circuitsmith.erc_engine.

The catalog (`rules.json`) is one entry per ERC check (S1..S5 + E1..E10) plus
educational rules with no enforced check. The validator (`validate_catalog.py`)
keeps the catalog and the engine in lock-step.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RULES_PATH = Path(__file__).resolve().parent / "rules.json"


def load_rules() -> list[dict[str, Any]]:
    """Return the parsed catalog as a list of entry dicts."""
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def rule_by_id(catalog: list[dict[str, Any]], rule_id: str) -> dict[str, Any] | None:
    """Find a single entry by `id`; return None when not present."""
    for entry in catalog:
        if entry.get("id") == rule_id:
            return entry
    return None


__all__ = ["RULES_PATH", "load_rules", "rule_by_id"]
