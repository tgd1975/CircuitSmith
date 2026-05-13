"""
ERC engine — topology-only Electrical Rule Check.

Runs strictly pre-layout against the typed `NetGraph` produced by
`circuitsmith.netgraph`. Implements the v0.1 check set:

  Structural (graph-shape) — S1, S2, S3
  Electrical (topology-keyed safety) — E1 .. E10

`S4` (unknown component reference) and `S5` (unknown pin reference)
are detected by the schema validator in `circuitsmith.schema`, but
their codes (severity, message template, id) live in the same constant
table here so report writers and the catalog validator (TASK-025) can
introspect a single source of truth — see ADR-0006.

Public contract:
  - CHECK_TABLE: dict[code, CheckSpec] — every code S1..S5 + E1..E10.
  - run(graph, circuit, *, profiles=None) -> list[Finding].
  - The function is import-clean and CLI-invokable (`python -m
    circuitsmith.erc_engine --circuit path/to/x.circuit.yml`).

Invariants (co-erc-engine):
  - ERC is strictly pre-layout — no geometry, no layout.yml reads.
  - Public check IDs (S1..S5, E1..E10) are stable.
  - Engine consumes NetGraph read-only.
  - No LLM in the predicate path — pure Python over typed data.
  - No host-project imports (ADR-0012 portability).

References:
  docs/developers/ideas/archived/idea-001.erc-engine.md (predicates,
  severity defaults, severity precedence).
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from circuitsmith.netgraph import NetGraph, PinRef
from circuitsmith.schema.registry import Profile, load_profiles


# ── Check table ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CheckSpec:
    """One entry in the ERC check table — codes, defaults, descriptions."""

    id: str                  # "S1", "E2", ...
    category: str            # "structural" | "electrical"
    severity_default: str    # "error" | "warning"
    title: str               # short human-readable title
    activator: str           # "always" or a short description (what activates)


CHECK_TABLE: dict[str, CheckSpec] = {
    # ── Structural ─────────────────────────────────────────────────────────
    "S1": CheckSpec("S1", "structural", "error",
                    "Unconnected required pin",
                    "Always (per instantiated component)"),
    "S2": CheckSpec("S2", "structural", "error",
                    "Dangling net",
                    "Always"),
    "S3": CheckSpec("S3", "structural", "warning",
                    "Duplicate net name",
                    "Always"),
    # S4/S5 surface via schema validation but the codes live here so the
    # report and the catalog validator share one table (ADR-0006).
    "S4": CheckSpec("S4", "structural", "error",
                    "Unknown reference",
                    "Detected by schema validator"),
    "S5": CheckSpec("S5", "structural", "error",
                    "Unknown pin",
                    "Detected by schema validator"),
    # ── Electrical ─────────────────────────────────────────────────────────
    "E1": CheckSpec("E1", "electrical", "error",
                    "Floating input",
                    "Net containing a signal input pin"),
    "E2": CheckSpec("E2", "electrical", "error",
                    "LED missing resistor",
                    "Any LED in the circuit"),
    "E3": CheckSpec("E3", "electrical", "warning",
                    "LED resistor out of range",
                    "LED path containing a resistor"),
    "E4": CheckSpec("E4", "electrical", "error",
                    "INPUT_ONLY pin driven",
                    "Any INPUT_ONLY pin in a net"),
    "E5": CheckSpec("E5", "electrical", "warning",
                    "Strapping pin without pull",
                    "Strapping pin net containing a switch"),
    "E6": CheckSpec("E6", "electrical", "warning",
                    "Missing decoupling cap",
                    "Any IC with a VCC pin"),
    "E7": CheckSpec("E7", "electrical", "warning",
                    "I2C missing pull-up",
                    "Any pin with func I2C_SDA or I2C_SCL"),
    "E8": CheckSpec("E8", "electrical", "warning",
                    "Current budget exceeded",
                    "MCU + any LEDs"),
    # E9 ships as WARNING in v0.1 because the `diode` category is backlogged
    # — see idea-001.erc-engine.md §E9 notes for the auto-promote condition.
    "E9": CheckSpec("E9", "electrical", "warning",
                    "Reverse-polarity unprotected",
                    "Any power input connector"),
    "E10": CheckSpec("E10", "electrical", "error",
                     "Pin conflict",
                     "Any pin appearing in more than one net"),
}


# ── Findings ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Finding:
    """One ERC finding emitted by `run`."""

    check: str           # check id (S1..S5, E1..E10)
    severity: str        # "error" | "warning" | "ok"
    ref: str             # component ref, or "—" for circuit-wide findings
    pin: str             # pin name, or "—"
    net: str             # affected net name, or "—"
    message: str         # one-line summary; report writer adds catalog block

    def sort_key(self) -> tuple[int, str, str, str]:
        """Deterministic ordering: severity desc, check asc, ref asc, pin asc."""
        severity_rank = {"error": 0, "warning": 1, "ok": 2}.get(self.severity, 3)
        return (severity_rank, self.check, self.ref, self.pin)


EMPTY = "—"


# ── Severity resolution ────────────────────────────────────────────────────


def _resolve_severity(
    code: str,
    *,
    circuit_overrides: dict[str, str],
    net_overrides: dict[str, str] | None,
    component_overrides_on_net: list[dict[str, str]] | None,
) -> str:
    """
    Resolve effective severity for one check on one net, per
    idea-001.erc-engine.md §Severity precedence:

      1. Per-net override (specificity wins outright).
      2. Per-component overrides on the net: most severe wins among them.
      3. Global meta.erc override.
      4. Built-in default from CHECK_TABLE.

    Returns one of: "error", "warning", "off".
    """
    if net_overrides and code in net_overrides:
        return _norm_severity(net_overrides[code])

    if component_overrides_on_net:
        component_values: list[str] = []
        for overrides in component_overrides_on_net:
            if code in overrides:
                component_values.append(_norm_severity(overrides[code]))
        if component_values:
            return _most_severe(component_values)

    if code in circuit_overrides:
        return _norm_severity(circuit_overrides[code])

    return CHECK_TABLE[code].severity_default


def _norm_severity(value: str) -> str:
    """Normalise severity tokens used in YAML to canonical lowercase."""
    s = value.strip().lower()
    if s == "warn":
        return "warning"
    return s


def _most_severe(values: list[str]) -> str:
    """error > warning > off — see §Severity precedence axis 2."""
    rank = {"error": 2, "warning": 1, "off": 0}
    return max(values, key=lambda v: rank.get(v, -1))


# ── Engine entry point ─────────────────────────────────────────────────────


def run(
    graph: NetGraph,
    circuit: dict[str, Any],
    *,
    profiles: dict[str, Profile] | None = None,
    schema_findings: Iterable[Finding] | None = None,
) -> list[Finding]:
    """
    Run the ERC against `graph`. Returns a list of findings, sorted into
    the canonical (severity, check, ref, pin) order documented in
    idea-001.erc-engine.md §Output.

    `schema_findings` lets the renderer-side pipeline feed S4/S5
    findings the schema validator produced earlier so they appear in
    the same emitted list under the same severity/order discipline.
    """
    if profiles is None:
        profiles = load_profiles()

    ctx = _Context.build(graph=graph, circuit=circuit, profiles=profiles)

    findings: list[Finding] = []

    # S-class is always run, in numerical order; collect every finding.
    findings.extend(_check_S1(ctx))
    findings.extend(_check_S2(ctx))
    findings.extend(_check_S3(ctx))
    if schema_findings:
        for f in schema_findings:
            findings.append(f)

    # E-class gate: if any S-class produced an ERROR, skip electrical checks.
    s_errors = [f for f in findings if f.check.startswith("S") and f.severity == "error"]
    if s_errors:
        findings.append(Finding(
            check="S0",  # banner only — not in CHECK_TABLE; report writer drops it
            severity="warning",
            ref=EMPTY, pin=EMPTY, net=EMPTY,
            message="Electrical checks skipped — fix structural errors first.",
        ))
    else:
        # Electrical, ordered by numeric check id for traceability.
        findings.extend(_check_E1(ctx))
        findings.extend(_check_E2(ctx))
        findings.extend(_check_E3(ctx))
        findings.extend(_check_E4(ctx))
        findings.extend(_check_E5(ctx))
        findings.extend(_check_E6(ctx))
        findings.extend(_check_E7(ctx))
        findings.extend(_check_E8(ctx))
        findings.extend(_check_E9(ctx))
        findings.extend(_check_E10(ctx))

    # Drop suppressed findings ("off" severity is never reported).
    findings = [f for f in findings if f.severity != "off"]

    findings.sort(key=Finding.sort_key)
    return findings


# ── Engine context (precomputed lookups) ───────────────────────────────────


@dataclass
class _Context:
    """Precomputed views of NetGraph + YAML used by multiple predicates."""

    graph: NetGraph
    circuit: dict[str, Any]
    profiles: dict[str, Profile]
    # Component ref → profile
    profile_by_ref: dict[str, Profile] = field(default_factory=dict)
    # Component ref → component entry from .circuit.yml
    entry_by_ref: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Global meta.erc overrides
    circuit_overrides: dict[str, str] = field(default_factory=dict)
    # Nets actually declared by the user in `connections[*].net` (excludes
    # the content-addressed segment artifacts NetGraph introduces during
    # path-flattening).
    declared_net_names: set[str] = field(default_factory=set)
    # Net name → declared `role:` mapping for GPIO-typed pins on that net
    # — schema-validated to be dict (per-pin) or str (whole-net).
    # Net name → effective signal-input pins (PinRef list)
    signal_inputs_per_net: dict[str, list[PinRef]] = field(default_factory=dict)
    # All LEDs in the circuit
    led_refs: list[str] = field(default_factory=list)
    # All MCU refs
    mcu_refs: list[str] = field(default_factory=list)

    @classmethod
    def build(
        cls,
        *,
        graph: NetGraph,
        circuit: dict[str, Any],
        profiles: dict[str, Profile],
    ) -> "_Context":
        ctx = cls(graph=graph, circuit=circuit, profiles=profiles)
        ctx.declared_net_names = {entry["net"] for entry in circuit["connections"]}
        for ref, entry in circuit["components"].items():
            ctx.entry_by_ref[ref] = entry
            type_string = entry["type"]
            prof = profiles.get(type_string)
            if prof is not None:
                ctx.profile_by_ref[ref] = prof
                kind = _kind(prof)
                if kind == "led":
                    ctx.led_refs.append(ref)
                if kind == "mcu" and _has_pin_type(prof, "POWER"):
                    ctx.mcu_refs.append(ref)
        ctx.circuit_overrides = _norm_overrides(circuit.get("meta", {}).get("erc"))
        return ctx

    # ── helpers used by predicates ────────────────────────────────────────

    def pin_profile_attr(self, pin: PinRef, key: str) -> Any:
        """Return profile-pin attribute `key` (None if pin or profile is unknown)."""
        prof = self.profile_by_ref.get(pin.ref)
        if prof is None or prof.pins_detail is None:
            return None
        return prof.pins_detail.get(pin.pin, {}).get(key)

    def component_overrides_on_net(self, net_name: str) -> list[dict[str, str]]:
        """List of per-component erc-override dicts for refs touching this net."""
        seen: set[str] = set()
        out: list[dict[str, str]] = []
        for pin in self.graph.pins_on_net(net_name):
            if pin.ref in seen:
                continue
            seen.add(pin.ref)
            entry = self.entry_by_ref.get(pin.ref, {})
            overrides = _norm_overrides(entry.get("erc"))
            if overrides:
                out.append(overrides)
        return out

    def net_overrides(self, net_name: str) -> dict[str, str]:
        return self.graph.net_meta.get(net_name, _emptymeta()).erc_overrides or {}

    def severity_for(self, code: str, net_name: str | None) -> str:
        """Resolve effective severity for `code` on `net_name` (or globally)."""
        if net_name is None:
            # Component- and net-overrides do not apply to circuit-wide checks.
            if code in self.circuit_overrides:
                return _norm_severity(self.circuit_overrides[code])
            return CHECK_TABLE[code].severity_default
        return _resolve_severity(
            code,
            circuit_overrides=self.circuit_overrides,
            net_overrides=_norm_overrides(self.net_overrides(net_name)),
            component_overrides_on_net=self.component_overrides_on_net(net_name),
        )

    def is_power_class_net(self, name: str) -> bool:
        for pin in self.graph.pins_on_net(name):
            if self.pin_profile_attr(pin, "type") == "POWER":
                return True
        return False

    def is_ground_class_net(self, name: str) -> bool:
        for pin in self.graph.pins_on_net(name):
            if self.pin_profile_attr(pin, "type") == "GROUND":
                return True
        return False

    def pin_role(self, net_name: str, pin: PinRef) -> str | None:
        """
        Resolve runtime `role:` for one pin on one net. Per yaml-format
        §role: it is a string (whole-net) or a dict (per-pin REF.PIN keyed).
        Returns None when unset — caller decides fallback behaviour.
        """
        meta = self.graph.net_meta.get(net_name)
        if meta is None:
            return None
        role = meta.role
        if role is None:
            return None
        if isinstance(role, str):
            return role
        if isinstance(role, dict):
            return role.get(str(pin)) or role.get(f"{pin.ref}.{pin.pin}")
        return None


def _emptymeta():
    from circuitsmith.netgraph import NetMeta
    return NetMeta()


def _norm_overrides(value: Any) -> dict[str, str]:
    """Normalise an erc-overrides dict; returns {} for None or non-dict."""
    if not isinstance(value, dict):
        return {}
    return {k: str(v) for k, v in value.items()}


def _has_pin_type(profile: Profile, pin_type: str) -> bool:
    if profile.pins_detail is None:
        return False
    return any(attrs.get("type") == pin_type for attrs in profile.pins_detail.values())


def _kind(profile: Profile | None) -> str | None:
    """
    Return the semantic component kind from `metadata.kind` — the field
    ERC predicates key on. Separate from `category` (which keys layout
    geometry only, per the dossier's "category keys layout, not
    semantics" invariant — see idea-001.components.md §1).
    """
    if profile is None or profile.metadata is None:
        return None
    return profile.metadata.get("kind")


def _kind_of_ref(ctx: "_Context", ref: str) -> str | None:
    return _kind(ctx.profile_by_ref.get(ref))


# ── Structural checks ──────────────────────────────────────────────────────


def _check_S1(ctx: _Context) -> list[Finding]:
    """Every required pin on every instantiated component must appear in some net."""
    findings: list[Finding] = []
    pin_index = ctx.graph.pin_index
    for ref, profile in ctx.profile_by_ref.items():
        if profile.pins_detail is None:
            continue
        for pin_name, attrs in profile.pins_detail.items():
            if not attrs.get("required"):
                continue
            pin_ref = PinRef(ref=ref, pin=pin_name)
            if pin_ref not in pin_index:
                severity = ctx.severity_for("S1", None)
                if severity == "off":
                    continue
                findings.append(Finding(
                    check="S1",
                    severity=severity,
                    ref=ref, pin=pin_name, net=EMPTY,
                    message=f"required pin {pin_ref} is not connected to any net.",
                ))
    return findings


def _check_S2(ctx: _Context) -> list[Finding]:
    """A net with only one endpoint pin is a wiring typo. Scoped to
    user-declared nets only — content-addressed path segments are
    construction artifacts of NetGraph and may legitimately have a
    single endpoint when they terminate at a named-net merge."""
    findings: list[Finding] = []
    for name in ctx.declared_net_names:
        members = ctx.graph.nets.get(name, [])
        if len(members) <= 1:
            severity = ctx.severity_for("S2", name)
            if severity == "off":
                continue
            only_pin = members[0] if members else None
            findings.append(Finding(
                check="S2",
                severity=severity,
                ref=(only_pin.ref if only_pin else EMPTY),
                pin=(only_pin.pin if only_pin else EMPTY),
                net=name,
                message=f"net {name!r} has {len(members)} endpoint(s); needs at least two.",
            ))
    return findings


def _check_S3(ctx: _Context) -> list[Finding]:
    """Two `net:` entries share a name without explicit merge intent."""
    findings: list[Finding] = []
    seen: dict[str, int] = {}
    for entry in ctx.circuit["connections"]:
        name = entry["net"]
        seen[name] = seen.get(name, 0) + 1
    for name, count in seen.items():
        if count > 1:
            severity = ctx.severity_for("S3", name)
            if severity == "off":
                continue
            findings.append(Finding(
                check="S3",
                severity=severity,
                ref=EMPTY, pin=EMPTY, net=name,
                message=f"net {name!r} is declared {count}× — collapse or rename.",
            ))
    return findings


# ── Electrical checks ──────────────────────────────────────────────────────


def _check_E1(ctx: _Context) -> list[Finding]:
    """Floating input — signal-input pin on a net with no pull and no external pull-resistor."""
    findings: list[Finding] = []
    for name in ctx.declared_net_names:
        signal_inputs = _signal_inputs_on_net(ctx, name)
        if not signal_inputs:
            continue
        severity = ctx.severity_for("E1", name)
        if severity == "off":
            continue
        meta = ctx.graph.net_meta.get(name)
        has_pull = bool(meta and meta.pull)
        if has_pull:
            continue
        # Search for an external pull-resistor: a 2-terminal passive
        # whose other terminal lands on a power-class or ground-class net.
        if _has_external_pull_resistor(ctx, name):
            continue
        # If any signal input is an unresolved-role GPIO, downgrade to warning.
        downgrade = any(_is_unresolved_role_gpio(ctx, name, pin) for pin in signal_inputs)
        effective = "warning" if downgrade and severity == "error" else severity
        for pin in signal_inputs:
            msg = (
                f"signal input {pin} on net {name!r} has no pull (declare "
                f"`pull:` on the net, or wire an external pull-up/down resistor)."
            )
            if downgrade and severity == "error":
                msg = (
                    f"signal input {pin} on net {name!r} could not be classified "
                    f"(unresolved `role:`); downgraded from ERROR to WARNING."
                )
            findings.append(Finding(
                check="E1", severity=effective,
                ref=pin.ref, pin=pin.pin, net=name,
                message=msg,
            ))
    return findings


def _check_E2(ctx: _Context) -> list[Finding]:
    """LED missing resistor — anode pin's path must include a resistor between GPIO and anode."""
    findings: list[Finding] = []
    path_sources = _path_net_names(ctx.graph)
    for led_ref in ctx.led_refs:
        anode = PinRef(led_ref, "A")
        if anode not in ctx.graph.pin_index:
            continue
        # Resolve which declared net the anode belongs to: either a path
        # source whose flattened walk includes the anode, or a pins/bus
        # net that names the anode directly.
        declared_nets_with_anode = _declared_nets_containing_pin(ctx, anode, path_sources)
        for net_name in declared_nets_with_anode:
            severity = ctx.severity_for("E2", net_name)
            if severity == "off":
                continue
            if net_name not in path_sources:
                findings.append(Finding(
                    check="E2", severity=severity,
                    ref=led_ref, pin="A", net=net_name,
                    message=(
                        f"LED {led_ref}.A wired on non-path net {net_name!r}; "
                        f"current-limit resistor has no defined position. "
                        f"Use `path:` form."
                    ),
                ))
                continue
            gpio = _driving_gpio_for_path(ctx, net_name)
            if gpio is None:
                continue
            try:
                refs_between = ctx.graph.components_between(gpio, anode)
            except ValueError:
                continue
            if not any(_kind_of_ref(ctx, r) == "resistor" for r in refs_between):
                findings.append(Finding(
                    check="E2", severity=severity,
                    ref=led_ref, pin="A", net=net_name,
                    message=(
                        f"LED {led_ref}.A on path net {net_name!r} has no "
                        f"current-limit resistor between {gpio} and the anode."
                    ),
                ))
    return findings


def _check_E3(ctx: _Context) -> list[Finding]:
    """LED resistor out of range — read VCC from MCU, v_forward from LED."""
    findings: list[Finding] = []
    vcc, max_gpio_ma = _mcu_voltage_and_current(ctx)
    if vcc is None:
        return findings
    path_sources = _path_net_names(ctx.graph)
    for led_ref in ctx.led_refs:
        led_profile = ctx.profile_by_ref.get(led_ref)
        if led_profile is None:
            continue
        anode = PinRef(led_ref, "A")
        if anode not in ctx.graph.pin_index:
            continue
        v_forward = _led_v_forward(led_profile, ctx.entry_by_ref.get(led_ref, {}))
        for net_name in _declared_nets_containing_pin(ctx, anode, path_sources):
            if net_name not in path_sources:
                continue
            severity = ctx.severity_for("E3", net_name)
            if severity == "off":
                continue
            gpio = _driving_gpio_for_path(ctx, net_name)
            if gpio is None:
                continue
            try:
                refs_between = ctx.graph.components_between(gpio, anode)
            except ValueError:
                continue
            resistor_ref = next(
                (r for r in refs_between if _kind_of_ref(ctx, r) == "resistor"),
                None,
            )
            if resistor_ref is None:
                continue  # E2 already fired
            r_value = _resistor_value_ohms(ctx.entry_by_ref.get(resistor_ref, {}))
            if r_value is None or r_value <= 0:
                continue
            current_ma = (vcc - v_forward) / r_value * 1000.0
            if current_ma < 1.0:
                findings.append(Finding(
                    check="E3", severity=severity,
                    ref=resistor_ref, pin=EMPTY, net=net_name,
                    message=(
                        f"resistor {resistor_ref}={r_value:g}Ω gives "
                        f"I≈{current_ma:.2f} mA on net {net_name!r} (LED too dim)."
                    ),
                ))
            elif max_gpio_ma is not None and current_ma > max_gpio_ma:
                findings.append(Finding(
                    check="E3", severity=severity,
                    ref=resistor_ref, pin=EMPTY, net=net_name,
                    message=(
                        f"resistor {resistor_ref}={r_value:g}Ω gives "
                        f"I≈{current_ma:.2f} mA on net {net_name!r}; exceeds "
                        f"per-GPIO budget {max_gpio_ma} mA (pin at risk)."
                    ),
                ))
    return findings


def _check_E4(ctx: _Context) -> list[Finding]:
    """INPUT_ONLY pin sharing a net with any pin whose `direction: out`."""
    findings: list[Finding] = []
    for name in ctx.declared_net_names:
        members = ctx.graph.nets.get(name, [])
        input_only_pins = [p for p in members if ctx.pin_profile_attr(p, "type") == "INPUT_ONLY"]
        if not input_only_pins:
            continue
        driving_pins = [p for p in members if ctx.pin_profile_attr(p, "direction") == "out"]
        if not driving_pins:
            continue
        severity = ctx.severity_for("E4", name)
        if severity == "off":
            continue
        for pin in input_only_pins:
            drivers = ", ".join(str(d) for d in driving_pins)
            findings.append(Finding(
                check="E4", severity=severity,
                ref=pin.ref, pin=pin.pin, net=name,
                message=(
                    f"INPUT_ONLY pin {pin} on net {name!r} is driven by output pin(s): {drivers}."
                ),
            ))
    return findings


def _check_E5(ctx: _Context) -> list[Finding]:
    """Strapping pin on a net with a switch but no firmware/hardware pull."""
    findings: list[Finding] = []
    for name in ctx.declared_net_names:
        members = ctx.graph.nets.get(name, [])
        # Need a strapping pin on this net
        strap_pins = [p for p in members
                      if ctx.pin_profile_attr(p, "is_strapping") is True]
        if not strap_pins:
            continue
        # Need a switch (button category) somewhere on this net
        has_switch = any(_kind_of_ref(ctx, p.ref) == "switch" for p in members)
        if not has_switch:
            continue
        meta = ctx.graph.net_meta.get(name)
        pull = meta.pull if meta else None
        if pull in ("firmware", "hardware_up", "hardware_down"):
            continue
        severity = ctx.severity_for("E5", name)
        if severity == "off":
            continue
        for pin in strap_pins:
            findings.append(Finding(
                check="E5", severity=severity,
                ref=pin.ref, pin=pin.pin, net=name,
                message=(
                    f"strapping pin {pin} on net {name!r} has no pull (`pull: firmware`"
                    f" or external hardware pull)."
                ),
            ))
    return findings


def _check_E6(ctx: _Context) -> list[Finding]:
    """Each non-MCU IC with a POWER pin must have a capacitor on the VCC-side net.

    MCUs are treated as dev-board units with integrated decoupling on the
    shipped profiles — their `POWER` pin is the board-level input (VIN,
    VBUS, V33), not a chip-die VCC. E6 therefore activates only when an
    IC *other than the MCU* sits on the rail. See idea-001.erc-engine.md
    §"E6, E7, E10: inactive on the current circuit"."""
    findings: list[Finding] = []
    mcu_refs = set(ctx.mcu_refs)
    for ref, profile in ctx.profile_by_ref.items():
        if _kind(profile) != "ic":
            continue
        if ref in mcu_refs:
            continue
        if profile.pins_detail is None:
            continue
        for pin_name, attrs in profile.pins_detail.items():
            if attrs.get("type") != "POWER":
                continue
            pin = PinRef(ref, pin_name)
            path_sources = _path_net_names(ctx.graph)
            for net_name in _declared_nets_containing_pin(ctx, pin, path_sources):
                if ctx.is_ground_class_net(net_name) and not ctx.is_power_class_net(net_name):
                    continue
                severity = ctx.severity_for("E6", net_name)
                if severity == "off":
                    continue
                has_cap = any(
                    _kind_of_ref(ctx, p.ref) == "capacitor"
                    for p in ctx.graph.pins_on_net(net_name)
                )
                if has_cap:
                    continue
                findings.append(Finding(
                    check="E6", severity=severity,
                    ref=ref, pin=pin_name, net=net_name,
                    message=(
                        f"IC {ref} VCC pin {pin} on net {net_name!r} has no "
                        f"decoupling capacitor on the rail (100 nF expected)."
                    ),
                ))
    return findings


def _check_E7(ctx: _Context) -> list[Finding]:
    """I2C SDA/SCL net must include a resistor to a power-class net.

    Activation requires *two or more* pins on the net carrying an I2C
    `func:` tag — i.e., an MCU plus an I2C peripheral. On a circuit
    where an I2C-capable MCU pin is used as a regular GPIO (no
    peripheral attached), the func tag is a capability, not a use,
    and E7 is dormant. This matches the dossier's "E7 active when an
    I2C peripheral is present" framing.
    """
    findings: list[Finding] = []
    for name in ctx.declared_net_names:
        members = ctx.graph.nets.get(name, [])
        i2c_pins = [
            p for p in members
            if _func_contains(ctx.pin_profile_attr(p, "func"), ("I2C_SDA", "I2C_SCL"))
        ]
        if len(i2c_pins) < 2:
            continue
        severity = ctx.severity_for("E7", name)
        if severity == "off":
            continue
        if _has_pullup_to_power(ctx, name):
            continue
        for pin in i2c_pins:
            findings.append(Finding(
                check="E7", severity=severity,
                ref=pin.ref, pin=pin.pin, net=name,
                message=(
                    f"I2C pin {pin} on net {name!r} has no pull-up to a power rail."
                ),
            ))
    return findings


def _check_E8(ctx: _Context) -> list[Finding]:
    """Sum of (VCC - v_forward) / R across LED nets must not exceed max_total_current_ma."""
    findings: list[Finding] = []
    if not ctx.led_refs:
        return findings
    vcc, _ = _mcu_voltage_and_current(ctx)
    max_total = _mcu_max_total_current_ma(ctx)
    if vcc is None or max_total is None:
        return findings
    severity = ctx.severity_for("E8", None)
    if severity == "off":
        return findings
    total_ma = 0.0
    contributions: list[str] = []
    path_sources = _path_net_names(ctx.graph)
    for led_ref in ctx.led_refs:
        led_profile = ctx.profile_by_ref.get(led_ref)
        if led_profile is None:
            continue
        anode = PinRef(led_ref, "A")
        if anode not in ctx.graph.pin_index:
            continue
        v_forward = _led_v_forward(led_profile, ctx.entry_by_ref.get(led_ref, {}))
        for net_name in _declared_nets_containing_pin(ctx, anode, path_sources):
            if net_name not in path_sources:
                continue
            gpio = _driving_gpio_for_path(ctx, net_name)
            if gpio is None:
                continue
            try:
                refs_between = ctx.graph.components_between(gpio, anode)
            except ValueError:
                continue
            resistor_ref = next(
                (r for r in refs_between if _kind_of_ref(ctx, r) == "resistor"),
                None,
            )
            if resistor_ref is None:
                continue
            r_value = _resistor_value_ohms(ctx.entry_by_ref.get(resistor_ref, {}))
            if r_value is None or r_value <= 0:
                continue
            current_ma = (vcc - v_forward) / r_value * 1000.0
            total_ma += current_ma
            contributions.append(f"{led_ref}~{current_ma:.1f}mA")
    if total_ma > max_total:
        findings.append(Finding(
            check="E8", severity=severity,
            ref=EMPTY, pin=EMPTY, net=EMPTY,
            message=(
                f"LED total current {total_ma:.1f} mA exceeds budget {max_total} mA "
                f"({', '.join(contributions)})."
            ),
        ))
    return findings


def _check_E9(ctx: _Context) -> list[Finding]:
    """Power input connector pins must share their net with a diode or P-MOSFET."""
    findings: list[Finding] = []
    for ref, profile in ctx.profile_by_ref.items():
        if _kind(profile) not in {"power-connector", "signal-connector"}:
            continue
        if profile.pins_detail is None:
            continue
        for pin_name, attrs in profile.pins_detail.items():
            if attrs.get("type") != "POWER":
                continue
            pin = PinRef(ref, pin_name)
            path_sources = _path_net_names(ctx.graph)
            for net_name in _declared_nets_containing_pin(ctx, pin, path_sources):
                severity = ctx.severity_for("E9", net_name)
                if severity == "off":
                    continue
                if _has_protection_element(ctx, net_name):
                    continue
                findings.append(Finding(
                    check="E9", severity=severity,
                    ref=ref, pin=pin_name, net=net_name,
                    message=(
                        f"power input pin {pin} on net {net_name!r} has no "
                        f"diode or P-MOSFET protection element. "
                        f"(WARNING at v0.1 pending the `diode` category.)"
                    ),
                ))
    return findings


def _check_E10(ctx: _Context) -> list[Finding]:
    """The same physical pin appears in more than one *declared* net.

    Content-addressed segment nets are construction artifacts of path
    flattening and not user-visible; a pin legitimately appears in
    multiple of them. Filter to declared nets so E10 fires only on
    real wiring duplicates."""
    findings: list[Finding] = []
    for pin, names in ctx.graph.pin_index.items():
        declared = tuple(n for n in names if n in ctx.declared_net_names)
        if len(declared) < 2:
            continue
        effective_levels = [ctx.severity_for("E10", n) for n in declared]
        on_levels = [s for s in effective_levels if s != "off"]
        if not on_levels:
            continue
        effective = _most_severe(on_levels)
        findings.append(Finding(
            check="E10", severity=effective,
            ref=pin.ref, pin=pin.pin, net=", ".join(declared),
            message=f"pin {pin} appears in multiple nets: {', '.join(declared)}.",
        ))
    return findings


# ── Predicate helpers ──────────────────────────────────────────────────────


def _signal_inputs_on_net(ctx: _Context, net_name: str) -> list[PinRef]:
    """
    Signal-input pins on `net_name` per E1's definition:
      - INPUT_ONLY-typed pins, or
      - GPIO-typed pins whose runtime role resolves to "in", or
      - GPIO-typed pins whose role is unresolved AND the net has at least
        one other signal-source candidate (e.g. a switch contact). On
        nets that are unambiguously output paths (GPIO → resistor → LED
        → GND), no `role:` declaration is required; the LED's cathode
        acts as the output peer and the GPIO is the driver.

    POWER and GROUND pins are excluded even though their profile
    direction is `"in"` — they are supply sinks, not signal inputs.
    """
    candidates: list[PinRef] = []
    members = ctx.graph.pins_on_net(net_name)
    has_switch_on_net = any(_kind_of_ref(ctx, p.ref) == "switch" for p in members)
    for pin in members:
        ptype = ctx.pin_profile_attr(pin, "type")
        if ptype == "INPUT_ONLY":
            candidates.append(pin)
            continue
        if ptype != "GPIO":
            continue
        role = ctx.pin_role(net_name, pin)
        if role == "in":
            candidates.append(pin)
        elif role is None and has_switch_on_net:
            # Switches need defined idle levels. Without an explicit role
            # declaration on a switch-touching net, treat the GPIO as a
            # potential input — E1 will emit WARNING on unresolved role.
            candidates.append(pin)
    return candidates


def _is_unresolved_role_gpio(ctx: _Context, net_name: str, pin: PinRef) -> bool:
    if ctx.pin_profile_attr(pin, "type") != "GPIO":
        return False
    return ctx.pin_role(net_name, pin) is None


def _has_external_pull_resistor(ctx: _Context, net_name: str) -> bool:
    """
    A 2-terminal resistor is an external pull when one of its terminals
    is on this net and the other terminal is on a power-class or
    ground-class net.
    """
    members = ctx.graph.pins_on_net(net_name)
    for pin in members:
        prof = ctx.profile_by_ref.get(pin.ref)
        if _kind(prof) != "resistor":
            continue
        terminals = [pin_name for pin_name in (prof.pins or ())]
        if len(terminals) != 2:
            continue
        other_pin_name = next((t for t in terminals if t != pin.pin), None)
        if other_pin_name is None:
            continue
        other_pin = PinRef(pin.ref, other_pin_name)
        for other_net in ctx.graph.nets_containing_pin(other_pin):
            if other_net == net_name:
                continue
            if ctx.is_power_class_net(other_net) or ctx.is_ground_class_net(other_net):
                return True
    return False


def _has_pullup_to_power(ctx: _Context, net_name: str) -> bool:
    """E7: any resistor with one terminal on this net and the other on a power-class net."""
    for pin in ctx.graph.pins_on_net(net_name):
        prof = ctx.profile_by_ref.get(pin.ref)
        if _kind(prof) != "resistor":
            continue
        terminals = list(prof.pins)
        if len(terminals) != 2:
            continue
        other_pin_name = next((t for t in terminals if t != pin.pin), None)
        if other_pin_name is None:
            continue
        other_pin = PinRef(pin.ref, other_pin_name)
        for other_net in ctx.graph.nets_containing_pin(other_pin):
            if other_net == net_name:
                continue
            if ctx.is_power_class_net(other_net):
                return True
    return False


def _has_protection_element(ctx: _Context, net_name: str) -> bool:
    """E9: any diode or P-MOSFET on the net.

    The `diode` category is backlogged (see idea-001.components.md §Backlog),
    so this check returns False on every v0.1 circuit by construction —
    which is the documented reason E9 ships as WARNING.
    """
    for pin in ctx.graph.pins_on_net(net_name):
        kind = _kind_of_ref(ctx, pin.ref)
        if kind in {"diode", "mosfet"}:
            return True
    return False


def _declared_nets_containing_pin(
    ctx: _Context, pin: PinRef, path_sources: set[str],
) -> list[str]:
    """
    Return the user-declared nets containing `pin`. A pin can be hosted
    either by a `pins:`/`bus:` net that names it directly, or by a path
    source whose flattened walk includes it.
    """
    out: list[str] = []
    direct = set(ctx.graph.nets_containing_pin(pin))
    for name in ctx.declared_net_names:
        if name in direct:
            out.append(name)
            continue
        if name in path_sources:
            walk = ctx.graph._path_walk_pins(  # noqa: SLF001
                ctx.graph._path_segments[name]  # noqa: SLF001
            )
            if pin in walk:
                out.append(name)
    return out


def _path_net_names(graph: NetGraph) -> set[str]:
    """Return the names of nets declared in `path:` form (path source nets)."""
    return set(graph._path_segments.keys())  # noqa: SLF001 — controlled access


def _driving_gpio_for_path(ctx: _Context, path_net: str) -> PinRef | None:
    """Pick the first GPIO/POWER pin walking a path net — the source of current."""
    # path_net is a path source; segments live under graph._path_segments.
    # Walk the first segment's left endpoint to find a GPIO/POWER pin.
    walk = ctx.graph._path_walk_pins(  # noqa: SLF001
        ctx.graph._path_segments[path_net]  # noqa: SLF001
    )
    for pin in walk:
        ptype = ctx.pin_profile_attr(pin, "type")
        if ptype in {"GPIO", "POWER"}:
            return pin
    return None


def _func_contains(value: Any, needles: tuple[str, ...]) -> bool:
    if not isinstance(value, list):
        return False
    return any(needle in value for needle in needles)


def _mcu_voltage_and_current(ctx: _Context) -> tuple[float | None, float | None]:
    """Return (vcc_max, max_gpio_current_ma) for the first MCU profile."""
    for ref in ctx.mcu_refs:
        prof = ctx.profile_by_ref[ref]
        if prof.metadata is None:
            continue
        vcc = prof.metadata.get("vcc_max")
        ma = prof.metadata.get("max_gpio_current_ma")
        if vcc is not None:
            return float(vcc), (float(ma) if ma is not None else None)
    return None, None


def _mcu_max_total_current_ma(ctx: _Context) -> float | None:
    for ref in ctx.mcu_refs:
        prof = ctx.profile_by_ref[ref]
        if prof.metadata is None:
            continue
        total = prof.metadata.get("max_total_current_ma")
        if total is not None:
            return float(total)
    return None


def _led_v_forward(profile: Profile, entry: dict[str, Any]) -> float:
    """Resolve the LED forward voltage from profile + entry color selection."""
    meta = profile.metadata or {}
    color = entry.get("color")
    by_color = meta.get("v_forward_by_color") or {}
    if color and color in by_color:
        return float(by_color[color])
    return float(meta.get("v_forward_default", 2.0))


def _resistor_value_ohms(entry: dict[str, Any]) -> float | None:
    """Parse a resistor `value:` (int/float) — `100`, `220`, etc."""
    v = entry.get("value")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="circuitsmith ERC engine (topology-only)")
    parser.add_argument("--circuit", type=Path, required=True,
                        help="path to a .circuit.yml")
    parser.add_argument("--no-schema", action="store_true",
                        help="skip the schema validator (S4/S5 surface only if specified)")
    args = parser.parse_args(argv)

    from ruamel.yaml import YAML
    yaml = YAML(typ="safe")
    with open(args.circuit) as fh:
        circuit = yaml.load(fh)

    schema_findings: list[Finding] = []
    if not args.no_schema:
        from circuitsmith.schema import validate
        schema_findings = [
            Finding(
                check=f.check if f.check in CHECK_TABLE else "S4",
                severity=f.severity,
                ref=EMPTY, pin=EMPTY,
                net=f.location,
                message=f.message,
            )
            for f in validate(circuit)
        ]

    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, schema_findings=schema_findings or None)

    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")

    for f in findings:
        sys.stdout.write(
            f"{f.severity.upper():7s} {f.check:3s} {f.ref:>6s} {f.pin:>8s} "
            f"{f.net:>20s}  {f.message}\n"
        )
    sys.stdout.write(f"\n{errors} error(s), {warnings} warning(s).\n")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))


__all__ = ["CHECK_TABLE", "CheckSpec", "Finding", "run"]
