"""
Post-schema validator. Runs JSON Schema (structural shape) first, then
the dynamic checks that depend on the component-library state:

  S4 — unknown component-type reference (`components[*].type`)
  S5 — unknown pin reference (`REF.PIN` in any connection form)

Output: a list of `Finding` records. Empty list = valid. JSON Schema
errors arrive as findings with check code `schema` and severity `error`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from .registry import Profile, load_profiles

SCHEMA_PATH = Path(__file__).resolve().parent / "circuit.schema.json"


@dataclass(frozen=True)
class Finding:
    """One validation finding."""

    check: str           # "schema" | "S4" | "S5"
    severity: str        # "error" | "warning"
    message: str
    location: str        # JSON-pointer-ish dotted path into the circuit dict


def validate(
    circuit: dict[str, Any],
    *,
    profiles: dict[str, Profile] | None = None,
) -> list[Finding]:
    """
    Validate a `.circuit.yml`-loaded dict. Returns an empty list on
    success; otherwise one Finding per problem found.

    `profiles` overrides the component library — useful in tests. When
    omitted, the registry is loaded from `circuitsmith/components/`.
    """
    findings: list[Finding] = []

    # ── Phase 1: structural JSON Schema ─────────────────────────────────
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(circuit), key=lambda e: e.path):
        findings.append(Finding(
            check="schema",
            severity="error",
            message=err.message,
            location=_path_to_location(err.absolute_path),
        ))
    # If the structural shape is broken, S4/S5 traversal would crash on
    # malformed dicts; bail out and let the author fix the shape first.
    if findings:
        return findings

    # ── Phase 2: dynamic type + pin checks ──────────────────────────────
    if profiles is None:
        profiles = load_profiles()

    components: dict[str, dict[str, Any]] = circuit["components"]
    ref_to_profile: dict[str, Profile] = {}
    for ref, entry in components.items():
        type_string = entry["type"]
        profile = profiles.get(type_string)
        if profile is None:
            findings.append(Finding(
                check="S4",
                severity="error",
                message=(
                    f"components.{ref}: unknown component type '{type_string}'. "
                    f"Known types: {sorted(profiles)}"
                ),
                location=f"components.{ref}.type",
            ))
        else:
            ref_to_profile[ref] = profile

    # S5: every REF.PIN reference must point at a real pin on the profile.
    for index, net in enumerate(circuit["connections"]):
        net_name = net["net"]
        if "pins" in net:
            _check_pin_tokens(net["pins"], ref_to_profile, findings,
                              f"connections[{index}].pins", net_name)
        if "path" in net:
            _check_path_tokens(net["path"], ref_to_profile, findings,
                               f"connections[{index}].path", net_name,
                               declared_nets={n["net"] for n in circuit["connections"]})
        if net.get("bus") is True:
            if "backbone" in net:
                _check_pin_tokens(net["backbone"], ref_to_profile, findings,
                                  f"connections[{index}].backbone", net_name)
            if "taps" in net:
                _check_pin_tokens(net["taps"], ref_to_profile, findings,
                                  f"connections[{index}].taps", net_name)

    return findings


def validate_file(yml_path: Path | str) -> list[Finding]:
    """Convenience: load YAML via ruamel.yaml and validate the result."""
    from ruamel.yaml import YAML
    yaml = YAML(typ="safe")
    with open(yml_path) as fh:
        circuit = yaml.load(fh)
    return validate(circuit)


# ── Internals ───────────────────────────────────────────────────────────

def _check_pin_tokens(
    tokens: list[str],
    ref_to_profile: dict[str, Profile],
    findings: list[Finding],
    location: str,
    net_name: str,
) -> None:
    """Each token must be REF.PIN with REF declared and PIN on its profile."""
    for token in tokens:
        ref, _, pin = token.partition(".")
        if not pin:
            # Schema already rejected this; defensive guard for the future
            # if the schema pattern is ever loosened.
            continue
        _check_ref_pin(ref, pin, ref_to_profile, findings, location, net_name, token)


def _check_path_tokens(
    tokens: list[str],
    ref_to_profile: dict[str, Profile],
    findings: list[Finding],
    location: str,
    net_name: str,
    declared_nets: set[str],
) -> None:
    """Path tokens are either REF.PIN pin references or bare net names."""
    for token in tokens:
        if "." in token:
            ref, _, pin = token.partition(".")
            _check_ref_pin(ref, pin, ref_to_profile, findings, location, net_name, token)
        # Bare-token resolution (net name vs unknown identifier) is the
        # post-schema validator's job per yaml-format §"Cross-cutting
        # decisions" #3. Not enforced here in this first cut; comes with
        # the flattener in EPIC-002.


def _check_ref_pin(
    ref: str,
    pin: str,
    ref_to_profile: dict[str, Profile],
    findings: list[Finding],
    location: str,
    net_name: str,
    token: str,
) -> None:
    profile = ref_to_profile.get(ref)
    if profile is None:
        findings.append(Finding(
            check="S4",
            severity="error",
            message=(
                f"net {net_name!r} at {location}: token '{token}' references "
                f"component '{ref}' which is not declared in components."
            ),
            location=location,
        ))
        return
    if pin not in profile.pins:
        findings.append(Finding(
            check="S5",
            severity="error",
            message=(
                f"net {net_name!r} at {location}: pin '{pin}' is not on "
                f"profile {profile.type} (component '{ref}'). "
                f"Valid pins: {sorted(profile.pins)}"
            ),
            location=location,
        ))


def _path_to_location(path) -> str:
    """Convert a jsonschema absolute_path deque to a dotted location string."""
    parts = [str(p) for p in path]
    return ".".join(parts) if parts else "<root>"
