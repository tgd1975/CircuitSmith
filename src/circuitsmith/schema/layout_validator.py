"""
Post-schema validator for `.layout.yml`.

Phase 1: JSON-Schema check against layout.schema.json.
Phase 2: cross-reference check (every `attached-to` target exists in the
same placements block).

Returns a list of `Finding` records compatible with circuit-side
validation (`schema/validator.py`). Empty list = valid.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from .validator import Finding, _path_to_location

LAYOUT_SCHEMA_PATH = Path(__file__).resolve().parent / "layout.schema.json"


def validate_layout(layout: dict[str, Any]) -> list[Finding]:
    """Validate a parsed .layout.yml dict; empty list = valid."""
    findings: list[Finding] = []
    schema = json.loads(LAYOUT_SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(layout), key=lambda e: list(e.absolute_path)):
        findings.append(Finding(
            check="layout-schema",
            severity="error",
            message=err.message,
            location=_path_to_location(err.absolute_path),
        ))
    if findings:
        return findings

    placements = layout.get("placements", {})
    for ref, slot in placements.items():
        target = slot.get("attached-to") if isinstance(slot, dict) else None
        if target is not None and target not in placements:
            findings.append(Finding(
                check="layout-attached-to-unknown",
                severity="error",
                message=(
                    f"placements.{ref}: attached-to={target!r} does not name a "
                    f"declared placement"
                ),
                location=f"placements.{ref}.attached-to",
            ))

    # EPIC-014 / TASK-124 — pages-partition cross-references.
    pages = layout.get("pages")
    declared_pages: set[str] = set()
    if isinstance(pages, list):
        seen: set[str] = set()
        for idx, entry in enumerate(pages):
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not isinstance(name, str):
                continue
            if name in seen:
                findings.append(Finding(
                    check="layout-pages-duplicate-name",
                    severity="error",
                    message=f"pages[{idx}]: duplicate page name {name!r}",
                    location=f"pages[{idx}].name",
                ))
            seen.add(name)
        declared_pages = seen

    for ref, slot in placements.items():
        if not isinstance(slot, dict):
            continue
        page = slot.get("page")
        if page is None:
            continue
        if page not in declared_pages:
            findings.append(Finding(
                check="layout-page-undeclared",
                severity="error",
                message=(
                    f"placements.{ref}: page={page!r} is not declared in the "
                    f"top-level `pages:` block"
                ),
                location=f"placements.{ref}.page",
            ))
    return findings


def validate_layout_file(yml_path: Path | str) -> list[Finding]:
    """Convenience: load YAML via ruamel.yaml and validate."""
    from ruamel.yaml import YAML
    yaml = YAML(typ="safe")
    with open(yml_path) as fh:
        layout = yaml.load(fh)
    return validate_layout(layout)


__all__ = ["validate_layout", "validate_layout_file"]
