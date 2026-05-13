"""
Deterministic layout kernel — v0.1, no AI, no randomness, no backtracking.

Reads a NetGraph + components dict + profile registry and emits a
`layout.yml` with one placement per component. The placement rule is the
canonical-slot table from
idea-001.layout-engine-concept.md §5.3; unknown topologies fail loud
via EscalationError so a v0.1 author can either hand-author a `free`
slot or restructure topology.

Incremental stability (§8):
  - kept     = components in both the previous layout and current circuit
  - removed  = components in previous layout but not current circuit
  - new      = components in current circuit but not previous layout

Kept components keep their slots verbatim **as long as their topology-
fingerprint (§8.4) still matches**. A fingerprint mismatch auto-
invalidates the placement and re-queues the component into `new`.

Output layout.yml is deterministic:
  - `placements:` keys sorted alphabetically.
  - Each placement is a flow-style mapping with keys in a fixed order
    (region first, then slot index, then label, then fingerprint).
  - One placement per line, so adding one component produces a one-line
    diff (the §8 incremental invariant the Phase 6 acceptance test
    measures).

References:
  - idea-001.layout-engine-concept.md §§4–8
  - ADR-0001 — slots are the single positioning primitive
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any, Iterable

from circuit.netgraph import NetGraph, PinRef

PIN_TYPE_GROUND = "GROUND"
PIN_TYPE_POWER = "POWER"
PIN_TYPE_INPUT_ONLY = "INPUT_ONLY"
PIN_TYPE_GPIO = "GPIO"

# Default per-region capacity (idea-001.layout-engine-concept.md §4.2).
_DEFAULT_CAPACITY = {
    "left-column":  12,
    "right-column": 12,
    "top-row":      16,
    "bottom-row":   16,
}

LAYOUT_SCHEMA_VERSION = "layout/v1"

# Internal key used to stash the ref → profile lookup so helper functions
# can resolve pin types without rebuilding the index on every call.
_BY_REF_KEY = "_by_ref"


# ── Public types ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Placement:
    """One component's slot assignment — exactly one §4.3 layout.yml row."""

    ref: str
    region: str | None = None
    row: int | None = None
    col: int | None = None
    position: float | None = None
    step: int | None = None
    attached_to: str | None = None
    attach_step: int | None = None
    label: str | None = None
    topology_fingerprint: str = ""


@dataclass
class LayoutResult:
    placements: dict[str, Placement]
    capacity_overrides: dict[str, dict[str, int]] = field(default_factory=dict)
    # When the kernel runs with `collect_escalations=True`, every
    # `no-canonical-rule` (and similar) finding lands here instead of
    # raising. The AI placer (Phase 2b, TASK-017) consumes this list.
    unplaced: list[tuple[str, str, str]] = field(default_factory=list)
    """List of `(ref, reason, detail)` triples for components the kernel could not place."""


@dataclass(frozen=True)
class SlotRule:
    id: int
    shape: str
    description: str


class EscalationError(Exception):
    """Raised when the kernel has no canonical slot for a component.

    Carries the reason code (§4.2 / §7) and the offending component
    reference so callers can surface it in meta.yml.
    """

    def __init__(self, reason: str, ref: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.ref = ref


# ── Canonical-slot rule IDs ──────────────────────────────────────────────
# Doc-only edits keep the ID; placement-behaviour edits bump it (§8.4).

RULE_LED_TO_GND        = SlotRule(1,  "led-anode-mcu-cathode-gnd",     "LED anode→MCU pin, cathode→GND")
RULE_RESISTOR_WITH_LED = SlotRule(2,  "resistor-in-path-with-led",     "Resistor in same path as an LED")
RULE_BUTTON_TO_GND     = SlotRule(3,  "button-one-side-mcu-other-gnd", "Button: one side→MCU pin, other→GND")
RULE_PULLUP_RESISTOR   = SlotRule(4,  "resistor-pullup-on-path",       "Resistor on a path between power/bus and MCU pin")
RULE_DECOUPLING_CAP    = SlotRule(5,  "capacitor-vcc-to-gnd",          "Capacitor between VCC and GND near an IC")
RULE_I2C_SENSOR        = SlotRule(6,  "i2c-sensor-sda-scl-vcc-gnd",    "I²C sensor: SDA/SCL/VCC/GND")
RULE_HEADER_OR_JACK    = SlotRule(7,  "edge-multipin-connector",       "Multi-pin header/jack on board edge")
RULE_GROUND_TERMINAL   = SlotRule(8,  "ground-terminal-in-slot",       "Ground terminal at a non-pin GND connection")
RULE_MCU_ANCHOR        = SlotRule(9,  "mcu-anchor",                    "MCU (or primary IC) — anchor placement")
RULE_NO_CONNECT        = SlotRule(10, "no-connect-pin",                "Unused pin — no net membership")


# ── Public entry point ───────────────────────────────────────────────────


def place(
    *,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
    previous_layout: dict[str, Any] | None = None,
    collect_escalations: bool = False,
) -> LayoutResult:
    """
    Compute placements for every component in `circuit`.

    `profiles` maps `type:` strings (e.g. `"mcu/esp32"`) to objects with
    `category` and `pins_detail` (the raw dict from components/*.py with
    `side`/`type`/etc.). Dict-shaped stubs are also accepted.

    `collect_escalations` toggles behaviour on a §5.3 dispatch failure:
      - `False` (default) → raise `EscalationError` on the first miss.
      - `True` → record `(ref, reason, detail)` in `LayoutResult.unplaced`
        and continue placing the remaining components. The AI placer
        (TASK-017) consumes the resulting list to converge on slot
        assignments for the unplaced components.
    """
    _build_ref_profile_index(circuit, profiles)
    component_refs = sorted(circuit["components"])

    prev_placements = _parse_previous_placements(previous_layout)
    capacity_overrides: dict[str, dict[str, int]] = dict(
        _parse_capacity_overrides(previous_layout)
    )

    kept_refs, new_refs = _diff_components(component_refs, prev_placements)

    fresh_placements: dict[str, Placement] = {}
    rule_lookup: dict[str, tuple[SlotRule, dict[str, Any]]] = {}

    for ref in kept_refs:
        rule, shape_meta = _classify(ref, circuit, graph, profiles)
        rule_lookup[ref] = (rule, shape_meta)
        prev = prev_placements[ref]
        if prev.topology_fingerprint == _topology_fingerprint(rule, shape_meta):
            fresh_placements[ref] = prev
        else:
            new_refs.append(ref)

    new_refs.sort()

    occupancy = _Occupancy(_DEFAULT_CAPACITY, capacity_overrides)
    for placement in fresh_placements.values():
        occupancy.record(placement)

    unplaced: list[tuple[str, str, str]] = []

    for ref in new_refs:
        if ref not in rule_lookup:
            try:
                rule_lookup[ref] = _classify(ref, circuit, graph, profiles)
            except EscalationError as exc:
                if collect_escalations:
                    unplaced.append((exc.ref, exc.reason, str(exc)))
                    continue
                raise
        rule, shape_meta = rule_lookup[ref]
        placement = _place_one(ref, rule, shape_meta, profiles, occupancy)
        # Attached-to placements inherit the anchor's region for emission so
        # the layout schema's `region: required` invariant holds; the index
        # fields (row/col/position) stay absent per the §4.2 attach-index-
        # redundant rule.
        if placement.attached_to is not None and placement.region is None:
            anchor = fresh_placements.get(placement.attached_to)
            if anchor is not None:
                placement = Placement(
                    ref=placement.ref,
                    region=anchor.region,
                    attached_to=placement.attached_to,
                    attach_step=placement.attach_step,
                    label=anchor.label,
                )
        placement = _attach_fingerprint(placement, rule, shape_meta)
        fresh_placements[ref] = placement
        occupancy.record(placement)

    return LayoutResult(
        placements=fresh_placements,
        capacity_overrides=occupancy.snapshot_overrides(),
        unplaced=unplaced,
    )


# ── Connection-shape classification ──────────────────────────────────────


def _classify(
    ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> tuple[SlotRule, dict[str, Any]]:
    """Pick a canonical rule for `ref`; raises EscalationError on no fit."""
    entry = circuit["components"][ref]
    profile = profiles.get(entry["type"])
    if profile is None:
        raise EscalationError(
            reason="no-profile",
            ref=ref,
            message=f"component {ref} has no profile for type {entry['type']!r}",
        )
    category = _profile_category(profile)

    if entry["type"].startswith("mcu/"):
        return RULE_MCU_ANCHOR, {"role": "anchor"}

    if category == "led":
        return RULE_LED_TO_GND, _shape_meta_led(ref, graph)

    if category == "resistor":
        led_ref = _resistor_in_same_path_as_led(ref, circuit, graph, profiles)
        if led_ref is not None:
            return RULE_RESISTOR_WITH_LED, {"attached_to": led_ref}
        if _resistor_is_pullup(ref, graph, profiles):
            return RULE_PULLUP_RESISTOR, _shape_meta_pullup(ref, graph, profiles)
        raise EscalationError(
            reason="no-canonical-rule",
            ref=ref,
            message=(
                f"resistor {ref} matches no canonical rule "
                f"(not paired with an LED, not on a recognised pull-up path)"
            ),
        )

    if category in ("button", "pushbutton"):
        return RULE_BUTTON_TO_GND, _shape_meta_pushbutton(ref, graph)

    if category == "capacitor":
        return RULE_DECOUPLING_CAP, _shape_meta_capacitor(ref, graph, profiles)

    if category in ("i2c_sensor", "i2c-sensor", "sensor"):
        return RULE_I2C_SENSOR, _shape_meta_i2c_sensor(ref, profile, graph)

    if category in ("usb_connector", "audio_jack", "header", "jack"):
        return RULE_HEADER_OR_JACK, _shape_meta_connector(profile)

    raise EscalationError(
        reason="no-canonical-rule",
        ref=ref,
        message=(
            f"component {ref} (type={entry['type']!r}, category={category!r}) "
            f"has no canonical-slot rule"
        ),
    )


def _shape_meta_led(ref: str, graph: NetGraph) -> dict[str, Any]:
    anode = PinRef(ref=ref, pin="A")
    # The LED's MCU-side anchor is the first pin of the path-source net the
    # anode belongs to. For a typical `[U1.IO25, R1.1, R1.2, D1.A, D1.K,
    # GND]` path, that first pin is the GPIO — even though D1.A's direct
    # net partner is the resistor terminal.
    anchor = _path_source_anchor_for(anode, graph)
    return {"anchor_pin": anchor}


def _shape_meta_pushbutton(ref: str, graph: NetGraph) -> dict[str, Any]:
    # Pin "1" is the MCU-side terminal by convention in passives/pushbutton.
    pin1 = PinRef(ref=ref, pin="1")
    anchor = _path_source_anchor_for(pin1, graph)
    if anchor is not None:
        return {"anchor_pin": anchor}
    # Fall through to pins-form heuristic: any non-self pin on a net with pin 1.
    for net_name in graph.nets:
        members = graph.pins_on_net(net_name)
        if any(p == pin1 for p in members):
            for partner in members:
                if partner.ref != ref:
                    return {"anchor_pin": partner}
    return {"anchor_pin": None}


def _path_source_anchor_for(pin: PinRef, graph: NetGraph) -> PinRef | None:
    """
    Find the first (MCU-side) pin of the path-source net containing `pin`.

    A path `[U1.D25, R1.1, R1.2, D1.A, D1.K, GND]` has segments
    `PWR_LED`, `PWR_LED__R1_2__D1_A`, `PWR_LED__D1_K__GND`. Whichever
    segment contains `pin`, the upstream anchor is `PWR_LED[0]` =
    `U1.D25` — the source the human declared.
    """
    path_sources: dict[str, tuple[str, ...]] = graph._path_segments  # type: ignore[attr-defined]
    for source_name, seg_names in path_sources.items():
        for seg in seg_names:
            if pin in graph.pins_on_net(seg):
                # First pin of the first segment is the upstream anchor.
                head_segment = seg_names[0]
                members = graph.pins_on_net(head_segment)
                return members[0] if members else None
    return None


def _shape_meta_capacitor(ref: str, graph: NetGraph, profiles: dict[str, Any]) -> dict[str, Any]:
    for net_name in graph.nets:
        members = graph.pins_on_net(net_name)
        if not any(p.ref == ref for p in members):
            continue
        if _net_contains_pin_type(members, profiles, PIN_TYPE_POWER):
            return {"power_net": net_name}
    return {"power_net": None}


def _shape_meta_i2c_sensor(ref: str, profile: Any, graph: NetGraph) -> dict[str, Any]:
    pins_detail = _pins_detail(profile)
    left_count = sum(1 for p in pins_detail.values() if p.get("side") == "left")
    right_count = sum(1 for p in pins_detail.values() if p.get("side") == "right")
    if left_count > right_count:
        side = "left"
    elif right_count > left_count:
        side = "right"
    else:
        side = _first_declared_pin_side(ref, pins_detail, graph)
    return {"dominant_side": side}


def _shape_meta_connector(profile: Any) -> dict[str, Any]:
    pins_detail = _pins_detail(profile)
    sides = {p.get("side") for p in pins_detail.values()}
    if "top" in sides:
        return {"edge": "top-row"}
    return {"edge": "bottom-row"}


def _shape_meta_pullup(ref: str, graph: NetGraph, profiles: dict[str, Any]) -> dict[str, Any]:
    for net_name in graph.nets:
        members = graph.pins_on_net(net_name)
        if not any(p.ref == ref for p in members):
            continue
        for pin in members:
            if pin.ref == ref:
                continue
            if _lookup_pin_type(pin, profiles) in (PIN_TYPE_GPIO, PIN_TYPE_INPUT_ONLY):
                return {"anchor_pin": pin}
    return {"anchor_pin": None}


def _resistor_in_same_path_as_led(
    ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> str | None:
    led_refs = {
        cref for cref, entry in circuit["components"].items()
        if _component_category(entry, profiles) == "led"
    }
    if not led_refs:
        return None
    # Walk every path-sourced net's segments and collect refs seen on it.
    # We deliberately read the protected attribute on NetGraph here because
    # the kernel and netgraph ship in the same skill and the design is
    # joint; exposing this as a public method would couple them more, not
    # less.
    path_sources: dict[str, tuple[str, ...]] = graph._path_segments  # type: ignore[attr-defined]
    for seg_names in path_sources.values():
        seen_refs: set[str] = set()
        for seg in seg_names:
            for pin in graph.pins_on_net(seg):
                seen_refs.add(pin.ref)
        if ref in seen_refs and seen_refs & led_refs:
            return sorted(seen_refs & led_refs)[0]
    return None


def _resistor_is_pullup(
    ref: str,
    graph: NetGraph,
    profiles: dict[str, Any],
) -> bool:
    for net_name in graph.nets:
        members = graph.pins_on_net(net_name)
        if any(p.ref == ref for p in members) and _net_contains_pin_type(
            members, profiles, PIN_TYPE_POWER
        ):
            return True
    return False


# ── Placement (after classification) ─────────────────────────────────────


def _place_one(
    ref: str,
    rule: SlotRule,
    shape_meta: dict[str, Any],
    profiles: dict[str, Any],
    occupancy: "_Occupancy",
) -> Placement:
    if rule is RULE_MCU_ANCHOR:
        return Placement(ref=ref, region="mcu-center")

    if rule is RULE_LED_TO_GND or rule is RULE_BUTTON_TO_GND:
        anchor = shape_meta.get("anchor_pin")
        side = _side_from_pin(anchor, profiles)
        region = _side_to_region(side, default="right-column")
        row = occupancy.next_row(region)
        return Placement(ref=ref, region=region, row=row, label=_label_for_region(region))

    if rule is RULE_RESISTOR_WITH_LED:
        return Placement(ref=ref, attached_to=shape_meta["attached_to"])

    if rule is RULE_PULLUP_RESISTOR:
        anchor = shape_meta.get("anchor_pin")
        if anchor is None:
            raise EscalationError(
                reason="no-canonical-rule",
                ref=ref,
                message=f"pull-up resistor {ref} has no MCU-side anchor",
            )
        region = f"path-of-{anchor.ref}.{anchor.pin}"
        return Placement(ref=ref, region=region, step=0)

    if rule is RULE_DECOUPLING_CAP:
        power_net = shape_meta.get("power_net") or "V33"
        region = f"bus-{power_net}"
        position = occupancy.next_bus_position(region)
        return Placement(ref=ref, region=region, position=position)

    if rule is RULE_I2C_SENSOR:
        side = shape_meta.get("dominant_side", "left")
        region = "left-column" if side == "left" else "right-column"
        row = occupancy.next_row(region)
        return Placement(ref=ref, region=region, row=row, label=_label_for_region(region))

    if rule is RULE_HEADER_OR_JACK:
        region = shape_meta.get("edge", "bottom-row")
        col = occupancy.next_col(region)
        return Placement(ref=ref, region=region, col=col)

    raise EscalationError(
        reason="kernel-bug",
        ref=ref,
        message=f"_place_one reached fallthrough for rule {rule}",
    )


# ── Topology fingerprint (§8.4) ──────────────────────────────────────────


def _topology_fingerprint(rule: SlotRule, shape_meta: dict[str, Any]) -> str:
    canonical = _canonical_shape_form(shape_meta)
    payload = f"rule={rule.id}|shape={rule.shape}|{canonical}".encode("utf-8")
    return f"sha1:{sha1(payload).hexdigest()[:12]}"


def _canonical_shape_form(shape_meta: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in sorted(shape_meta):
        value = shape_meta[key]
        if isinstance(value, PinRef):
            value = f"{value.ref}.{value.pin}"
        parts.append(f"{key}={value}")
    return ",".join(parts)


def _attach_fingerprint(p: Placement, rule: SlotRule, shape_meta: dict[str, Any]) -> Placement:
    return Placement(
        ref=p.ref,
        region=p.region,
        row=p.row,
        col=p.col,
        position=p.position,
        step=p.step,
        attached_to=p.attached_to,
        attach_step=p.attach_step,
        label=p.label,
        topology_fingerprint=_topology_fingerprint(rule, shape_meta),
    )


# ── Occupancy ────────────────────────────────────────────────────────────


class _Occupancy:
    """Tracks next-free row/col/step per region, with capacity overrides."""

    def __init__(self, defaults: dict[str, int], overrides: dict[str, dict[str, int]]):
        self._defaults = defaults
        self._overrides = overrides
        self._rows: dict[str, set[int]] = {}
        self._cols: dict[str, set[int]] = {}
        self._bus_positions: dict[str, list[float]] = {}

    def record(self, p: Placement) -> None:
        if p.region is None:
            return
        if p.row is not None:
            self._rows.setdefault(p.region, set()).add(p.row)
        if p.col is not None:
            self._cols.setdefault(p.region, set()).add(p.col)
        if p.position is not None:
            self._bus_positions.setdefault(p.region, []).append(p.position)

    def next_row(self, region: str) -> int:
        used = self._rows.setdefault(region, set())
        capacity = self._capacity_for(region, "rows")
        for row in range(capacity):
            if row not in used:
                used.add(row)
                return row
        self._overrides.setdefault(region, {})["rows"] = capacity + 1
        used.add(capacity)
        return capacity

    def next_col(self, region: str) -> int:
        used = self._cols.setdefault(region, set())
        capacity = self._capacity_for(region, "cols")
        for col in range(capacity):
            if col not in used:
                used.add(col)
                return col
        self._overrides.setdefault(region, {})["cols"] = capacity + 1
        used.add(capacity)
        return capacity

    def next_bus_position(self, region: str) -> float:
        used = self._bus_positions.setdefault(region, [])
        # 1/16 resolution candidates, mid-outward.
        candidates = [
            0.5, 0.25, 0.75, 0.125, 0.375, 0.625, 0.875,
            0.0625, 0.1875, 0.3125, 0.4375, 0.5625, 0.6875, 0.8125, 0.9375,
        ]
        for pos in candidates:
            if pos not in used:
                used.append(pos)
                return pos
        raise EscalationError(
            reason="bus-saturated",
            ref="",
            message=f"bus region {region} saturated at 1/16 resolution",
        )

    def snapshot_overrides(self) -> dict[str, dict[str, int]]:
        return {k: dict(v) for k, v in self._overrides.items()}

    def _capacity_for(self, region: str, axis: str) -> int:
        override = self._overrides.get(region, {}).get(axis)
        if override is not None:
            return override
        if axis == "rows":
            return self._defaults.get(region, 12)
        return self._defaults.get(region, 16)


# ── Profile / pin helpers ────────────────────────────────────────────────


def _build_ref_profile_index(
    circuit: dict[str, Any],
    profiles: dict[str, Any],
) -> None:
    """Build `ref → profile` lookup and stash it under `_by_ref`."""
    by_ref: dict[str, Any] = {}
    for ref, entry in circuit["components"].items():
        by_ref[ref] = profiles.get(entry["type"])
    profiles[_BY_REF_KEY] = by_ref


def _profile_category(profile: Any) -> str:
    if isinstance(profile, dict):
        return profile.get("category", "")
    return getattr(profile, "category", "") or ""


def _pins_detail(profile: Any) -> dict[str, dict[str, Any]]:
    detail = getattr(profile, "pins_detail", None)
    if isinstance(detail, dict):
        return detail
    if isinstance(profile, dict):
        return profile.get("pins", {})
    return {}


def _lookup_pin_type(pin: PinRef, profiles: dict[str, Any]) -> str | None:
    by_ref = profiles.get(_BY_REF_KEY)
    if not isinstance(by_ref, dict):
        return None
    profile = by_ref.get(pin.ref)
    if profile is None:
        return None
    return (_pins_detail(profile).get(pin.pin) or {}).get("type")


def _net_contains_pin_type(
    pins: Iterable[PinRef],
    profiles: dict[str, Any],
    pin_type: str,
) -> bool:
    return any(_lookup_pin_type(p, profiles) == pin_type for p in pins)


def _side_from_pin(pin: PinRef | None, profiles: dict[str, Any]) -> str | None:
    if pin is None:
        return None
    profile = profiles.get(_BY_REF_KEY, {}).get(pin.ref)
    if profile is None:
        return None
    return (_pins_detail(profile).get(pin.pin) or {}).get("side")


def _side_to_region(side: str | None, *, default: str) -> str:
    return {
        "left":   "left-column",
        "right":  "right-column",
        "top":    "top-row",
        "bottom": "bottom-row",
    }.get(side or "", default)


def _label_for_region(region: str) -> str | None:
    return {
        "left-column":  "left",
        "right-column": "right",
        "top-row":      "above",
        "bottom-row":   "below",
    }.get(region)


def _first_declared_pin_side(ref: str, pins_detail: dict, graph: NetGraph) -> str:
    for name in graph.nets:
        for pin in graph.pins_on_net(name):
            if pin.ref == ref:
                side = (pins_detail.get(pin.pin) or {}).get("side")
                if side in ("left", "right"):
                    return side
    return "left"


def _component_category(entry: dict[str, Any], profiles: dict[str, Any]) -> str:
    return _profile_category(profiles.get(entry["type"]))


# ── Previous-layout parsing ──────────────────────────────────────────────


def _parse_previous_placements(previous: dict[str, Any] | None) -> dict[str, Placement]:
    if previous is None:
        return {}
    raw = previous.get("placements", {})
    if not isinstance(raw, dict):
        return {}
    out: dict[str, Placement] = {}
    for ref, slot in raw.items():
        if not isinstance(slot, dict):
            continue
        out[ref] = Placement(
            ref=ref,
            region=slot.get("region"),
            row=slot.get("row"),
            col=slot.get("col"),
            position=slot.get("position"),
            step=slot.get("step"),
            attached_to=slot.get("attached-to"),
            attach_step=slot.get("attach-step"),
            label=slot.get("label"),
            topology_fingerprint=slot.get("topology-fingerprint", ""),
        )
    return out


def _parse_capacity_overrides(previous: dict[str, Any] | None) -> dict[str, dict[str, int]]:
    if previous is None:
        return {}
    raw = previous.get("capacity-overrides", {})
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, int]] = {}
    for region, overrides in raw.items():
        if isinstance(overrides, dict):
            out[region] = dict(overrides)
    return out


def _diff_components(
    current: list[str],
    previous: dict[str, Placement],
) -> tuple[list[str], list[str]]:
    kept = sorted(ref for ref in current if ref in previous)
    new = sorted(ref for ref in current if ref not in previous)
    return kept, new


# ── layout.yml emission ──────────────────────────────────────────────────


def render_layout_yaml(result: LayoutResult) -> str:
    """
    Serialise the LayoutResult to a byte-stable layout.yml string.

    Format requirements (§4.3, §8.2):
      - `schema: layout/v1` first.
      - `placements:` keys sorted alphabetically.
      - Each placement on one line as a flow-style mapping; fields in a
        fixed key order so a one-line topology change produces a one-
        line diff.
      - `capacity-overrides:` block at the bottom, omitted when empty.
    """
    lines: list[str] = [f"schema: {LAYOUT_SCHEMA_VERSION}", "placements:"]
    for ref in sorted(result.placements):
        lines.append(f"  {ref}: " + _format_placement_inline(result.placements[ref]))
    if result.capacity_overrides:
        lines.append("capacity-overrides:")
        for region in sorted(result.capacity_overrides):
            overrides = result.capacity_overrides[region]
            override_parts = [f"{k}: {v}" for k, v in sorted(overrides.items())]
            lines.append(f"  {region}: " + "{ " + ", ".join(override_parts) + " }")
    return "\n".join(lines) + "\n"


def _format_placement_inline(p: Placement) -> str:
    parts: list[str] = []
    if p.region is not None:
        parts.append(f"region: {p.region}")
    if p.attached_to is not None:
        parts.append(f"attached-to: {p.attached_to}")
    if p.attach_step is not None:
        parts.append(f"attach-step: {p.attach_step}")
    if p.row is not None:
        parts.append(f"row: {p.row}")
    if p.col is not None:
        parts.append(f"col: {p.col}")
    if p.step is not None:
        parts.append(f"step: {p.step}")
    if p.position is not None:
        parts.append(f"position: {_format_float(p.position)}")
    if p.label is not None:
        parts.append(f"label: {p.label}")
    if p.topology_fingerprint:
        parts.append(f"topology-fingerprint: {p.topology_fingerprint}")
    return "{ " + ", ".join(parts) + " }"


def _format_float(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"
