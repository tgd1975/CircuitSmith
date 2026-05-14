"""
Post-schema validator. Runs JSON Schema (structural shape) first, then
the dynamic checks that depend on the component-library state:

  S4 — unknown component-type reference (`components[*].type`)
  S5 — unknown pin reference (`REF.PIN` in any connection form)
  S6 — nested sub-block reference (EPIC-014 / TASK-115; a sub-block
       definition's `components.*.type` names another sub-block key,
       which is disallowed in v1)
  S7 — undeclared sub-block instance (EPIC-014 / TASK-115; an
       `instances.<name>.sub-block:` value names a sub-block that
       does not exist) or undeclared instance-port reference
       (a top-level `connections` entry references
       `<instance>.<port>` where `port` is not in the instance's
       sub-block `ports:` map)

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

    check: str           # "schema" | "S4" | "S5" | "S6" | "S7"
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

    # ── EPIC-014 / TASK-115: sub-block + instance cross-checks ──────────
    sub_blocks: dict[str, dict[str, Any]] = circuit.get("sub-blocks") or {}
    instances: dict[str, dict[str, Any]] = circuit.get("instances") or {}

    # S6: nested-sub-block rejection. Each sub-block's components.*.type
    # must not name another sub-block key. (The check is structural — it
    # only fires when sub-blocks names overlap with the component-type
    # namespace, but the rejection is unambiguous when it does.)
    sub_block_names = set(sub_blocks)
    for sb_name, sb_body in sub_blocks.items():
        sb_components = (sb_body or {}).get("components") or {}
        for inner_ref, inner_entry in sb_components.items():
            inner_type = (inner_entry or {}).get("type", "")
            if inner_type in sub_block_names:
                findings.append(Finding(
                    check="S6",
                    severity="error",
                    message=(
                        f"sub-blocks.{sb_name}.components.{inner_ref}.type "
                        f"references sub-block '{inner_type}' — nested sub-blocks "
                        f"are disallowed in v1 (EPIC-014 frozen decision)."
                    ),
                    location=f"sub-blocks.{sb_name}.components.{inner_ref}.type",
                ))

    # S7a: every instance's `sub-block:` value must exist in `sub-blocks:`.
    instance_to_sub: dict[str, str] = {}
    for inst_name, inst_body in instances.items():
        sub_name = (inst_body or {}).get("sub-block")
        if sub_name is None:
            continue  # JSON Schema already required this — defensive
        if sub_name not in sub_block_names:
            findings.append(Finding(
                check="S7",
                severity="error",
                message=(
                    f"instances.{inst_name}.sub-block: references "
                    f"undeclared sub-block '{sub_name}'. "
                    f"Declared sub-blocks: {sorted(sub_block_names)}."
                ),
                location=f"instances.{inst_name}.sub-block",
            ))
        else:
            instance_to_sub[inst_name] = sub_name

    # Build instance-port lookup: instance_name → set of port-names.
    instance_ports: dict[str, set[str]] = {}
    for inst_name, sub_name in instance_to_sub.items():
        ports_map = (sub_blocks.get(sub_name) or {}).get("ports") or {}
        instance_ports[inst_name] = set(ports_map)

    # S5: every REF.PIN reference must point at a real pin on the profile,
    # OR at a declared instance + port pair.
    for index, net in enumerate(circuit["connections"]):
        net_name = net["net"]
        if "pins" in net:
            _check_pin_tokens(net["pins"], ref_to_profile, findings,
                              f"connections[{index}].pins", net_name,
                              instance_ports=instance_ports)
        if "path" in net:
            _check_path_tokens(net["path"], ref_to_profile, findings,
                               f"connections[{index}].path", net_name,
                               declared_nets={n["net"] for n in circuit["connections"]},
                               instance_ports=instance_ports)
        if net.get("bus") is True:
            if "backbone" in net:
                _check_pin_tokens(net["backbone"], ref_to_profile, findings,
                                  f"connections[{index}].backbone", net_name,
                                  instance_ports=instance_ports)
            if "taps" in net:
                _check_pin_tokens(net["taps"], ref_to_profile, findings,
                                  f"connections[{index}].taps", net_name,
                                  instance_ports=instance_ports)

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
    *,
    instance_ports: dict[str, set[str]] | None = None,
) -> None:
    """Each token must be REF.PIN with REF declared and PIN on its profile."""
    for token in tokens:
        ref, _, pin = token.partition(".")
        if not pin:
            # Schema already rejected this; defensive guard for the future
            # if the schema pattern is ever loosened.
            continue
        _check_ref_pin(ref, pin, ref_to_profile, findings, location, net_name, token,
                       instance_ports=instance_ports)


def _check_path_tokens(
    tokens: list[str],
    ref_to_profile: dict[str, Profile],
    findings: list[Finding],
    location: str,
    net_name: str,
    declared_nets: set[str],
    *,
    instance_ports: dict[str, set[str]] | None = None,
) -> None:
    """Path tokens are either REF.PIN pin references or bare net names."""
    for token in tokens:
        if "." in token:
            ref, _, pin = token.partition(".")
            _check_ref_pin(ref, pin, ref_to_profile, findings, location, net_name, token,
                           instance_ports=instance_ports)
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
    *,
    instance_ports: dict[str, set[str]] | None = None,
) -> None:
    profile = ref_to_profile.get(ref)
    if profile is None:
        # EPIC-014 / TASK-115: maybe this is a sub-block instance reference
        # (e.g. `FILT_A.signal_in`). The instance is declared in
        # `instances:`, not `components:`, so it's absent from
        # `ref_to_profile`. Look it up by instance name; the pin token is
        # the port name.
        if instance_ports is not None and ref in instance_ports:
            if pin not in instance_ports[ref]:
                findings.append(Finding(
                    check="S7",
                    severity="error",
                    message=(
                        f"net {net_name!r} at {location}: instance '{ref}' "
                        f"has no port '{pin}'. Declared ports: "
                        f"{sorted(instance_ports[ref])}."
                    ),
                    location=location,
                ))
            return
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
    if pin not in profile.pins and not _pin_is_alt(pin, profile):
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


def _pin_is_alt(pin: str, profile: Profile) -> bool:
    """EPIC-014 / TASK-121 — accept silicon-name pin aliases (e.g.
    `U1.GND` resolving to `U1.1` on a 555). Walks `pins_detail[*].alt`
    looking for an exact match; case-insensitive comparison would be a
    follow-up policy call, not a v1 default."""
    detail = profile.pins_detail or {}
    for attrs in detail.values():
        for alt in (attrs or {}).get("alt", []) or []:
            if alt == pin:
                return True
    return False


def _path_to_location(path) -> str:
    """Convert a jsonschema absolute_path deque to a dotted location string."""
    parts = [str(p) for p in path]
    return ".".join(parts) if parts else "<root>"
