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

import re
from dataclasses import dataclass, field, replace
from hashlib import sha1
from typing import Any, Iterable

from circuitsmith.netgraph import NetGraph, PinRef

PIN_TYPE_GROUND = "GROUND"
PIN_TYPE_POWER = "POWER"
PIN_TYPE_INPUT_ONLY = "INPUT_ONLY"
PIN_TYPE_GPIO = "GPIO"
PIN_TYPE_SIGNAL_INPUT = "SIGNAL_INPUT"

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
    # EPIC-014 / TASK-124 — pages partition. `page` is a rendering
    # concern (which SVG the component lands on); slot assignment
    # happens within a page's region/slot vocabulary as today. None
    # for single-page layouts; the renderer treats `None` identically
    # to "the only page" so v0.1 .layout.yml files render unchanged.
    page: str | None = None


@dataclass
class LayoutResult:
    placements: dict[str, Placement]
    capacity_overrides: dict[str, dict[str, int]] = field(default_factory=dict)
    # When the kernel runs with `collect_escalations=True`, every
    # `no-canonical-rule` (and similar) finding lands here instead of
    # raising. The AI placer (Phase 2b, TASK-017) consumes this list.
    unplaced: list[tuple[str, str, str]] = field(default_factory=list)
    """List of `(ref, reason, detail)` triples for components the kernel could not place."""
    # EPIC-014 / TASK-124 — pages partition. Round-trips the
    # `pages:` declarations from a previous layout so re-rendering
    # preserves them. The kernel doesn't synthesise pages; they are
    # user-authored in the .layout.yml.
    pages: list[dict[str, Any]] = field(default_factory=list)


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
# EPIC-014 Phase 1 — TASK-111..114. Non-LED kernel rules for the
# textbook RC / CC / RR groupings the v0.1 kernel does not classify.
RULE_RC_LOW_PASS       = SlotRule(11, "rc-low-pass-r-top-c-to-gnd",    "R + C low-pass: R in-path, C from R-out node to GND")
RULE_RC_HIGH_PASS      = SlotRule(12, "rc-high-pass-c-series-r-to-gnd", "R + C high-pass: C in series, R from junction to GND")
RULE_CC_DECOUPLING     = SlotRule(13, "cc-decoupling-pair-on-rail",    "C + C decoupling pair: two caps in parallel on one rail to GND")
RULE_RR_VOLTAGE_DIVIDER = SlotRule(14, "rr-voltage-divider-rail-tap-gnd", "R + R voltage divider: rail → R → tap → R → GND, gated by tap hint or role")
# EPIC-014 Phase 4 — TASK-120. Active-device canonical slot (ADR-0015).
# v1 ships BJT only; FET / op-amp / 555 follow under TASK-121..122 with
# their own rules.
RULE_BJT_TO_GND        = SlotRule(15, "bjt-base-mcu-emitter-gnd",     "BJT: base driven from MCU side, emitter/collector to power rails")
RULE_RESISTOR_WITH_BJT = SlotRule(16, "resistor-in-path-with-bjt",    "Resistor in same path as a BJT (base-drive resistor)")
# EPIC-014 Phase 4 — TASK-121 / TASK-122. Generic-IC canonical slot for
# multi-pin ICs whose only sensible placement is a side-column. Pin
# side dominance picks left vs right, mirroring the I²C-sensor rule.
RULE_GENERIC_IC        = SlotRule(17, "ic-side-column-by-dominant-pin", "Generic multi-pin IC: side-column placement by dominant pin side")
# EPIC-014 / TASK-129 (ADR-0016). Collector-load and emitter-degeneration
# resistors on a BJT — land in synthetic per-BJT regions so the kernel does
# not escalate on textbook CE-amplifier shapes.
RULE_BJT_LOAD          = SlotRule(18, "bjt-collector-load-rail-to-collector", "Resistor between a POWER rail and a BJT collector pin")
RULE_BJT_DEGENERATION  = SlotRule(19, "bjt-emitter-degeneration-gnd",         "Resistor between a BJT emitter pin and GND")


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
                    # Attached components inherit the anchor's page —
                    # EPIC-014 / TASK-124. Co-locates a base-drive
                    # resistor with its BJT, an LED's resistor with
                    # the LED, etc. The user can override by setting
                    # `page:` on the attached entry, which the
                    # previous-layout parse honours.
                    page=anchor.page,
                )
        # EPIC-014 / TASK-124 — preserve user-authored `page:` across
        # topology-fingerprint mismatches. The fingerprint mechanism
        # controls re-classification (slot decisions); page assignment
        # is independent rendering metadata and must survive a re-run.
        prev = prev_placements.get(ref)
        if placement.page is None and prev is not None and prev.page is not None:
            placement = replace(placement, page=prev.page)
        placement = _attach_fingerprint(placement, rule, shape_meta)
        fresh_placements[ref] = placement
        occupancy.record(placement)

    return LayoutResult(
        placements=fresh_placements,
        capacity_overrides=occupancy.snapshot_overrides(),
        unplaced=unplaced,
        pages=_parse_previous_pages(previous_layout),
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
        # EPIC-014 / TASK-120 — only the **base-drive** resistor pairs
        # with a BJT (analogous to the current-limit resistor on an LED).
        # Collector / emitter resistors are handled by the pull-up rule
        # or escalate; they are NOT attached-to the BJT (multiple
        # attached-to entries on one anchor cause rubric overlaps).
        bjt_ref = _resistor_in_same_path_as_bjt_base(
            ref, circuit, graph, profiles
        )
        if bjt_ref is not None:
            return RULE_RESISTOR_WITH_BJT, {"attached_to": bjt_ref}
        # EPIC-014 Phase 1 — RR voltage divider takes priority over RC
        # because a confirmed-divider resistor sits between rail and GND,
        # which would also satisfy the pull-up heuristic if checked first.
        rr_partner, rr_tap, rr_hinted = _detect_rr_voltage_divider_partner(
            ref, circuit, graph, profiles
        )
        if rr_partner is not None and rr_hinted:
            return RULE_RR_VOLTAGE_DIVIDER, {
                "partner": rr_partner,
                "tap_net": rr_tap,
            }
        # Unhinted divider topology → fall through to pull-up/no-rule path.
        # The low-confidence warning is the ERC catalogue's job
        # (`divider-ambiguous`, minted in TASK-114); the kernel stays
        # silent and yields flat placement.
        # RC low-pass (R in-path, C-to-GND from junction).
        rc_lp_partner = _detect_rc_low_pass_partner(ref, circuit, graph, profiles)
        if rc_lp_partner is not None:
            return RULE_RC_LOW_PASS, {"partner": rc_lp_partner, "anchor_role": "r"}
        # RC high-pass (R-to-GND, C series above).
        rc_hp_partner = _detect_rc_high_pass_partner(ref, circuit, graph, profiles)
        if rc_hp_partner is not None:
            return RULE_RC_HIGH_PASS, {"partner": rc_hp_partner, "anchor_role": "r"}
        # EPIC-014 / TASK-129 (ADR-0016) — BJT collector-load and emitter-
        # degeneration shapes. Run before the pull-up fallback since a
        # collector-load R sits between rail and Q.C and would otherwise
        # match the (very permissive) pull-up heuristic, then fail its
        # anchor-pin check at placement time.
        bjt_load_ref = _detect_bjt_collector_load(ref, circuit, graph, profiles)
        if bjt_load_ref is not None:
            return RULE_BJT_LOAD, {"bjt_ref": bjt_load_ref}
        bjt_degen_ref = _detect_bjt_emitter_degeneration(ref, circuit, graph, profiles)
        if bjt_degen_ref is not None:
            return RULE_BJT_DEGENERATION, {"bjt_ref": bjt_degen_ref}
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
        # EPIC-014 Phase 1 — C+C decoupling pair preempts the bare
        # capacitor-VCC-to-GND rule when a partner cap is present on the
        # same rail.
        cc_partner = _detect_cc_decoupling_partner(ref, circuit, graph, profiles)
        if cc_partner is not None:
            return RULE_CC_DECOUPLING, {"partner": cc_partner}
        # RC low-pass (C-to-GND from junction; partner is an R in-path).
        rc_lp_partner = _detect_rc_low_pass_partner_from_cap(
            ref, circuit, graph, profiles
        )
        if rc_lp_partner is not None:
            return RULE_RC_LOW_PASS, {"partner": rc_lp_partner, "anchor_role": "c"}
        # RC high-pass (C in series; partner is an R-to-GND on the junction).
        rc_hp_partner = _detect_rc_high_pass_partner_from_cap(
            ref, circuit, graph, profiles
        )
        if rc_hp_partner is not None:
            return RULE_RC_HIGH_PASS, {"partner": rc_hp_partner, "anchor_role": "c"}
        return RULE_DECOUPLING_CAP, _shape_meta_capacitor(ref, graph, profiles)

    if category in ("i2c_sensor", "i2c-sensor", "sensor"):
        return RULE_I2C_SENSOR, _shape_meta_i2c_sensor(ref, profile, graph)

    if category in ("usb_connector", "audio_jack", "header", "jack"):
        return RULE_HEADER_OR_JACK, _shape_meta_connector(profile)

    # EPIC-014 / TASK-120 — BJT canonical slot (ADR-0015). Anchor pin
    # is the base; layout side is derived from where the base path
    # comes from, defaulting to right-column to mirror the LED row
    # convention. PNP and NPN share this rule — orientation differs
    # only in the schemdraw symbol (`metadata.symbol`), not in slot.
    if category == "transistor":
        base_pin = PinRef(ref=ref, pin="B")
        anchor = _path_source_anchor_for(base_pin, graph)
        return RULE_BJT_TO_GND, {"anchor_pin": anchor}

    # EPIC-014 / TASK-121 + TASK-122 — generic multi-pin IC. The 555
    # timer and dual-supply op-amp share this slot; future ICs (logic
    # gate, voltage regulator) extend the same rule by setting their
    # `category` to a member of this tuple.
    if category in ("ic_timer", "ic_opamp"):
        return RULE_GENERIC_IC, _shape_meta_i2c_sensor(ref, profile, graph)

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
    # Anchor priority: MCU GPIO / INPUT_ONLY first (the canonical
    # "MCU-side anchor" the rule was minted for in TASK-103), then IC
    # SIGNAL_INPUT (ADR-0017). Two passes preserve existing placement
    # for MCU-anchored pull-ups when a circuit happens to have both —
    # e.g. a divider whose tap also reaches an IC input.
    #
    # Restrict the search to the resistor's *own* two nets and skip
    # the rail net — a pull-up sits between a rail and a signal net;
    # the rail also carries the destination IC's power pin and may
    # incidentally carry an unrelated SIGNAL_INPUT (e.g. RESET tied
    # high). Scanning every net in the graph could pick that
    # coincident pin instead of the resistor's actual signal-side
    # terminal.
    r_nets = list(_nets_touching(ref, graph).keys())
    anchor_types_priority = (
        (PIN_TYPE_GPIO, PIN_TYPE_INPUT_ONLY),
        (PIN_TYPE_SIGNAL_INPUT,),
    )
    for accepted_types in anchor_types_priority:
        for net_name in r_nets:
            if _is_gnd_net(net_name):
                continue
            members = graph.pins_on_net(net_name)
            # Skip the rail-side net: a power-net is identified by
            # presence of any POWER-typed pin (VCC/VBUS/V33 on an MCU
            # or IC).
            if any(
                _lookup_pin_type(p, profiles) in (PIN_TYPE_POWER, "POWER_INPUT")
                for p in members
            ):
                continue
            for pin in members:
                if pin.ref == ref:
                    continue
                if _lookup_pin_type(pin, profiles) in accepted_types:
                    return {"anchor_pin": pin}
    return {"anchor_pin": None}


def _resistor_in_same_path_as_led(
    ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> str | None:
    return _resistor_in_same_path_as_category(
        ref, circuit, graph, profiles, "led"
    )


def _resistor_in_same_path_as_bjt_base(
    ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> str | None:
    """Return the BJT refdes whose **base** pin shares a path-sourced net
    with the resistor `ref`. Collector- and emitter-side resistors return
    None — only the base-drive resistor attaches to the BJT.

    Reads `pins.X.role: "base"` from the profile so the rule survives
    a future BJT profile with non-standard `B` pin key (e.g. silicon-
    name keying), per the EPIC-014 frozen-decisions table.
    """
    bjt_refs = {
        cref for cref, entry in circuit["components"].items()
        if _component_category(entry, profiles) == "transistor"
    }
    if not bjt_refs:
        return None
    path_sources: dict[str, tuple[str, ...]] = graph._path_segments  # type: ignore[attr-defined]
    for seg_names in path_sources.values():
        pins_on_path: list[PinRef] = []
        for seg in seg_names:
            pins_on_path.extend(graph.pins_on_net(seg))
        if not any(p.ref == ref for p in pins_on_path):
            continue
        for pin in pins_on_path:
            if pin.ref not in bjt_refs:
                continue
            bjt_profile = profiles.get(circuit["components"][pin.ref]["type"])
            attrs = (_pins_detail(bjt_profile).get(pin.pin) or {})
            if attrs.get("role") == "base":
                return pin.ref
    return None


def _bjt_pin_with_role(
    bjt_ref: str,
    role: str,
    circuit: dict[str, Any],
    profiles: dict[str, Any],
) -> str | None:
    """Return the pin name (e.g. "C", "E") on `bjt_ref` whose profile
    declares `role: <role>`. None if the role is absent."""
    bjt_profile = profiles.get(circuit["components"][bjt_ref]["type"])
    for pin_name, attrs in (_pins_detail(bjt_profile) or {}).items():
        if attrs.get("role") == role:
            return pin_name
    return None


def _detect_bjt_collector_load(
    r_ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> str | None:
    """Return the BJT refdes for which `r_ref` is the collector load — i.e.
    one terminal of `r_ref` shares a net with a `role: collector` pin and
    the other terminal shares a net containing a `POWER` pin (the rail).
    None otherwise (ADR-0016)."""
    bjt_refs = {
        cref for cref, entry in circuit["components"].items()
        if _component_category(entry, profiles) == "transistor"
    }
    if not bjt_refs:
        return None
    r_nets = _nets_touching(r_ref, graph)
    if len(r_nets) != 2:
        return None
    net_names = list(r_nets.keys())
    for collector_net, rail_net in (net_names, list(reversed(net_names))):
        if not _net_contains_pin_type(graph.pins_on_net(rail_net), profiles, PIN_TYPE_POWER):
            continue
        for pin in graph.pins_on_net(collector_net):
            if pin.ref not in bjt_refs:
                continue
            attrs = _pins_detail(profiles.get(circuit["components"][pin.ref]["type"])).get(pin.pin) or {}
            if attrs.get("role") == "collector":
                return pin.ref
    return None


def _detect_bjt_emitter_degeneration(
    r_ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> str | None:
    """Return the BJT refdes for which `r_ref` is the emitter-degeneration
    resistor — i.e. one terminal of `r_ref` is on a GND net and the other
    shares a net with a `role: emitter` pin. None otherwise (ADR-0016)."""
    bjt_refs = {
        cref for cref, entry in circuit["components"].items()
        if _component_category(entry, profiles) == "transistor"
    }
    if not bjt_refs:
        return None
    r_nets = _nets_touching(r_ref, graph)
    if len(r_nets) != 2:
        return None
    net_names = list(r_nets.keys())
    for emitter_net, gnd_net in (net_names, list(reversed(net_names))):
        if not _is_gnd_net(gnd_net):
            continue
        for pin in graph.pins_on_net(emitter_net):
            if pin.ref not in bjt_refs:
                continue
            attrs = _pins_detail(profiles.get(circuit["components"][pin.ref]["type"])).get(pin.pin) or {}
            if attrs.get("role") == "emitter":
                return pin.ref
    return None


def _resistor_in_same_path_as_category(
    ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
    category: str,
) -> str | None:
    """Generalisation of the resistor-on-LED-path detector.

    Returns the refdes of the first component in `category` that shares
    a path-sourced net with `ref`, or None. The protected `_path_segments`
    read is the same compromise as the LED helper — kernel + netgraph
    ship together, exposing this as a public method couples them more
    not less.
    """
    target_refs = {
        cref for cref, entry in circuit["components"].items()
        if _component_category(entry, profiles) == category
    }
    if not target_refs:
        return None
    path_sources: dict[str, tuple[str, ...]] = graph._path_segments  # type: ignore[attr-defined]
    for seg_names in path_sources.values():
        seen_refs: set[str] = set()
        for seg in seg_names:
            for pin in graph.pins_on_net(seg):
                seen_refs.add(pin.ref)
        if ref in seen_refs and seen_refs & target_refs:
            return sorted(seen_refs & target_refs)[0]
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


# ── EPIC-014 Phase 1 — RC / CC / RR pair detection (TASK-111..114) ───────
# Each pair-detection helper returns the *partner* refdes (or None). The
# caller then classifies both halves with the same rule and asks
# `_place_one` to place them in the rule's canonical slot pair.

_GND_NET_NAMES = frozenset({"GND", "AGND", "DGND", "GROUND", "0V", "VSS"})


def _is_gnd_net(net_name: str) -> bool:
    return net_name.upper() in _GND_NET_NAMES


def _nets_touching(ref: str, graph: NetGraph) -> dict[str, "PinRef | None"]:
    """Map net-name → the PinRef on `ref` that's on that net.

    A single ref may appear on multiple nets (one per pin). The returned
    value is the first pin found; callers that need all pins iterate the
    net members directly.
    """
    out: dict[str, PinRef | None] = {}
    for net_name, members in graph.nets.items():
        for pin in members:
            if pin.ref == ref:
                out.setdefault(net_name, pin)
                break
    return out


def _component_type(ref: str, circuit: dict[str, Any]) -> str:
    return (circuit["components"].get(ref) or {}).get("type", "")


def _other_pin_net(
    ref: str,
    this_net: str,
    graph: NetGraph,
) -> str | None:
    """The other net touching `ref` (a two-terminal component).

    Returns None if `ref` only touches one net or is multi-net beyond two.
    """
    nets = [n for n in _nets_touching(ref, graph).keys() if n != this_net]
    return nets[0] if len(nets) == 1 else None


def _detect_rc_low_pass_partner(
    r_ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> str | None:
    """If R is the resistor of an R+C low-pass, return the C ref.

    Low-pass shape: R in-path; R shares a junction net with a capacitor C;
    C's other terminal is on GND. The R's *other* (input-side) net must
    not be GND (else it would be a high-pass with a degenerate R).
    """
    # R must be a passives/resistor.
    if _profile_category(profiles.get(_component_type(r_ref, circuit))) != "resistor":
        return None
    r_nets = _nets_touching(r_ref, graph)
    if len(r_nets) != 2:
        return None
    for junction_net in r_nets:
        if _is_gnd_net(junction_net):
            continue
        # Find a capacitor C also on this junction net.
        for pin in graph.pins_on_net(junction_net):
            if pin.ref == r_ref:
                continue
            if _profile_category(profiles.get(_component_type(pin.ref, circuit))) != "capacitor":
                continue
            c_ref = pin.ref
            c_other = _other_pin_net(c_ref, junction_net, graph)
            if c_other is not None and _is_gnd_net(c_other):
                # Confirm R's other net is not GND (or this is degenerate).
                r_other = _other_pin_net(r_ref, junction_net, graph)
                if r_other is not None and not _is_gnd_net(r_other):
                    return c_ref
    return None


def _detect_rc_high_pass_partner(
    r_ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> str | None:
    """If R is the to-GND resistor of an R+C high-pass, return the C ref.

    High-pass shape: C in series; C shares a junction net with R; R's
    other terminal is on GND. Mirror of low-pass.
    """
    if _profile_category(profiles.get(_component_type(r_ref, circuit))) != "resistor":
        return None
    r_nets = _nets_touching(r_ref, graph)
    if len(r_nets) != 2:
        return None
    # R must have exactly one GND terminal.
    gnd_nets = [n for n in r_nets if _is_gnd_net(n)]
    if len(gnd_nets) != 1:
        return None
    junction_net = next(n for n in r_nets if not _is_gnd_net(n))
    # Find a capacitor C on the junction net; C's other terminal must NOT
    # be GND (else it's a decoupling cap, not high-pass).
    for pin in graph.pins_on_net(junction_net):
        if pin.ref == r_ref:
            continue
        if _profile_category(profiles.get(_component_type(pin.ref, circuit))) != "capacitor":
            continue
        c_ref = pin.ref
        c_other = _other_pin_net(c_ref, junction_net, graph)
        if c_other is not None and not _is_gnd_net(c_other):
            return c_ref
    return None


def _detect_cc_decoupling_partner(
    c_ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> str | None:
    """If C is one half of a C+C decoupling pair, return the partner C ref.

    Both caps share the same two nets: one rail (POWER-class pin
    membership) and GND. The pair is direction-symmetric, so the returned
    partner is the lexicographically-first matching cap not equal to
    `c_ref` (ensures both halves classify to the same partner).
    """
    if _profile_category(profiles.get(_component_type(c_ref, circuit))) != "capacitor":
        return None
    c_nets = set(_nets_touching(c_ref, graph).keys())
    if len(c_nets) != 2:
        return None
    has_gnd = any(_is_gnd_net(n) for n in c_nets)
    if not has_gnd:
        return None
    # The non-GND net must be a power-class rail (any pin on it of type POWER).
    rail = next((n for n in c_nets if not _is_gnd_net(n)), None)
    if rail is None:
        return None
    if not _net_contains_pin_type(graph.pins_on_net(rail), profiles, PIN_TYPE_POWER):
        return None
    # Search for another cap with the same two-net membership.
    candidates: list[str] = []
    for pin in graph.pins_on_net(rail):
        if pin.ref == c_ref:
            continue
        if _profile_category(profiles.get(_component_type(pin.ref, circuit))) != "capacitor":
            continue
        other_nets = set(_nets_touching(pin.ref, graph).keys())
        if other_nets == c_nets:
            candidates.append(pin.ref)
    if not candidates:
        return None
    # Stable pairing: lexicographically-first matching partner.
    return sorted(candidates)[0]


def _detect_rc_low_pass_partner_from_cap(
    c_ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> str | None:
    """Cap-side mirror of `_detect_rc_low_pass_partner`.

    Returns the R refdes if this cap is the to-GND half of an RC low-pass.
    """
    if _profile_category(profiles.get(_component_type(c_ref, circuit))) != "capacitor":
        return None
    c_nets = _nets_touching(c_ref, graph)
    if len(c_nets) != 2:
        return None
    # Cap must have one terminal on GND and one on a junction.
    if not any(_is_gnd_net(n) for n in c_nets):
        return None
    junction_net = next((n for n in c_nets if not _is_gnd_net(n)), None)
    if junction_net is None:
        return None
    for pin in graph.pins_on_net(junction_net):
        if pin.ref == c_ref:
            continue
        if _profile_category(profiles.get(_component_type(pin.ref, circuit))) != "resistor":
            continue
        r_ref = pin.ref
        r_other = _other_pin_net(r_ref, junction_net, graph)
        # R must have an other-side net that is not GND (else it would be
        # a high-pass with the resistor going to GND).
        if r_other is not None and not _is_gnd_net(r_other):
            return r_ref
    return None


def _detect_rc_high_pass_partner_from_cap(
    c_ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> str | None:
    """Cap-side mirror of `_detect_rc_high_pass_partner`.

    Returns the R refdes if this cap is the series cap of an RC high-pass.
    """
    if _profile_category(profiles.get(_component_type(c_ref, circuit))) != "capacitor":
        return None
    c_nets = _nets_touching(c_ref, graph)
    if len(c_nets) != 2:
        return None
    # Cap must NOT have a GND terminal (it is in series).
    if any(_is_gnd_net(n) for n in c_nets):
        return None
    # Each non-GND net could be the junction; one side will have an R to
    # GND on it.
    for junction_net in c_nets:
        for pin in graph.pins_on_net(junction_net):
            if pin.ref == c_ref:
                continue
            if _profile_category(profiles.get(_component_type(pin.ref, circuit))) != "resistor":
                continue
            r_ref = pin.ref
            r_other = _other_pin_net(r_ref, junction_net, graph)
            if r_other is not None and _is_gnd_net(r_other):
                return r_ref
    return None


_DIVIDER_TAP_REGEX = re.compile(r"^(V?REF|SENSE|ADC|DIV|TAP)", re.IGNORECASE)


def _detect_rr_voltage_divider_partner(
    r_ref: str,
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Any],
) -> tuple[str | None, str | None, bool]:
    """Return ``(partner_ref, tap_net, hinted)`` for an R+R voltage divider.

    Divider shape: two resistors in series between a POWER rail and GND;
    a tap net joins them. The discriminator (IDEA-008 *Open questions*)
    fires only when at least one is true:

    - ``tap_net`` matches ``^(V?REF|SENSE|ADC|DIV|TAP)`` (case-insensitive).
    - Either resistor's component entry carries ``role: divider``.

    ``hinted`` reports whether the discriminator fired. If a divider
    topology is present but no hint, the caller emits a low-confidence
    warning and falls back to flat placement.
    """
    if _profile_category(profiles.get(_component_type(r_ref, circuit))) != "resistor":
        return (None, None, False)
    r_nets = _nets_touching(r_ref, graph)
    if len(r_nets) != 2:
        return (None, None, False)
    r_other_pin = {n: p for n, p in r_nets.items()}
    # One terminal must be on a POWER rail, the other on a non-GND junction,
    # OR one terminal is on GND with the junction on the other side.
    for junction_net, _r_junction_pin in r_other_pin.items():
        if _is_gnd_net(junction_net):
            continue
        r_other = _other_pin_net(r_ref, junction_net, graph)
        if r_other is None:
            continue
        # Look for a partner R also on the junction net.
        for pin in graph.pins_on_net(junction_net):
            if pin.ref == r_ref:
                continue
            if _profile_category(profiles.get(_component_type(pin.ref, circuit))) != "resistor":
                continue
            partner = pin.ref
            partner_other = _other_pin_net(partner, junction_net, graph)
            if partner_other is None:
                continue
            # Determine which side is rail and which is GND.
            r_side_is_power = _net_contains_pin_type(
                graph.pins_on_net(r_other), profiles, PIN_TYPE_POWER
            )
            partner_side_is_gnd = _is_gnd_net(partner_other)
            r_side_is_gnd = _is_gnd_net(r_other)
            partner_side_is_power = _net_contains_pin_type(
                graph.pins_on_net(partner_other), profiles, PIN_TYPE_POWER
            )
            if not (
                (r_side_is_power and partner_side_is_gnd)
                or (r_side_is_gnd and partner_side_is_power)
            ):
                continue
            # Topology matches; now apply the discriminator.
            tap_hinted = bool(_DIVIDER_TAP_REGEX.match(junction_net))
            role_hinted = any(
                (circuit["components"].get(ref) or {}).get("role") == "divider"
                for ref in (r_ref, partner)
            )
            return (partner, junction_net, tap_hinted or role_hinted)
    return (None, None, False)


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

    if rule is RULE_RESISTOR_WITH_BJT:
        return Placement(ref=ref, attached_to=shape_meta["attached_to"])

    if rule is RULE_BJT_TO_GND:
        anchor = shape_meta.get("anchor_pin")
        side = _side_from_pin(anchor, profiles)
        region = _side_to_region(side, default="right-column")
        row = occupancy.next_row(region)
        return Placement(ref=ref, region=region, row=row, label=_label_for_region(region))

    if rule is RULE_PULLUP_RESISTOR:
        anchor = shape_meta.get("anchor_pin")
        if anchor is None:
            raise EscalationError(
                reason="no-canonical-rule",
                ref=ref,
                message=f"pull-up resistor {ref} has no MCU-side or IC-input anchor",
            )
        region = f"path-of-{anchor.ref}.{anchor.pin}"
        return Placement(ref=ref, region=region, step=0)

    if rule is RULE_DECOUPLING_CAP:
        power_net = shape_meta.get("power_net") or "V33"
        region = f"bus-{power_net}"
        position = occupancy.next_bus_position(region)
        return Placement(ref=ref, region=region, position=position)

    if rule is RULE_I2C_SENSOR or rule is RULE_GENERIC_IC:
        side = shape_meta.get("dominant_side", "left")
        region = "left-column" if side == "left" else "right-column"
        row = occupancy.next_row(region)
        return Placement(ref=ref, region=region, row=row, label=_label_for_region(region))

    if rule is RULE_HEADER_OR_JACK:
        region = shape_meta.get("edge", "bottom-row")
        col = occupancy.next_col(region)
        return Placement(ref=ref, region=region, col=col)

    # EPIC-014 Phase 1 — RC / CC / RR pair placements. Both halves write
    # into a synthetic per-pair region whose name is derived from the
    # partner refdes pair (sorted so the two halves land in the same
    # region). Each half takes a stable row index (top vs bottom).
    if rule is RULE_RC_LOW_PASS:
        partner = shape_meta["partner"]
        anchor_role = shape_meta["anchor_role"]  # "r" → R-top, "c" → C-bottom
        region = "rc-low-pass-" + "-".join(sorted((ref, partner)))
        row = 0 if anchor_role == "r" else 1
        return Placement(ref=ref, region=region, row=row, label="rc-low-pass")

    if rule is RULE_RC_HIGH_PASS:
        partner = shape_meta["partner"]
        anchor_role = shape_meta["anchor_role"]  # "c" → C-top (series), "r" → R-bottom (to GND)
        region = "rc-high-pass-" + "-".join(sorted((ref, partner)))
        row = 0 if anchor_role == "c" else 1
        return Placement(ref=ref, region=region, row=row, label="rc-high-pass")

    if rule is RULE_CC_DECOUPLING:
        partner = shape_meta["partner"]
        # Stable region name derived from the cap pair. Mirrors the
        # bus-region shape so the renderer can treat the pair like the
        # existing decoupling-cap stack.
        region = "cc-decoupling-" + "-".join(sorted((ref, partner)))
        # Row order: smaller refdes on row 0 → stable across both halves.
        row = 0 if ref < partner else 1
        return Placement(ref=ref, region=region, row=row, label="cc-decoupling")

    if rule is RULE_RR_VOLTAGE_DIVIDER:
        partner = shape_meta["partner"]
        tap_net = shape_meta["tap_net"]
        region = f"divider-{tap_net}"
        # Row order is stable on refdes: smaller ref → top (between rail
        # and tap), larger ref → bottom (between tap and GND). The
        # actual electrical orientation is determined by which side
        # touches the rail vs GND in the connections, but the *layout*
        # convention is "top R first".
        row = 0 if ref < partner else 1
        return Placement(ref=ref, region=region, row=row, label="divider")

    # EPIC-014 / TASK-129 (ADR-0016). BJT collector-load and emitter-
    # degeneration resistors share the BJT's row-0/row-1 stack: load
    # on row 0 ("above" the device), degeneration on row 1 ("below").
    # Region is per-BJT so multi-BJT circuits stay separable.
    if rule is RULE_BJT_LOAD:
        bjt_ref = shape_meta["bjt_ref"]
        region = f"bjt-load-{bjt_ref}"
        return Placement(ref=ref, region=region, row=0, label="bjt-load")

    if rule is RULE_BJT_DEGENERATION:
        bjt_ref = shape_meta["bjt_ref"]
        region = f"bjt-degen-{bjt_ref}"
        return Placement(ref=ref, region=region, row=0, label="bjt-degeneration")

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
        page=p.page,
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
            page=slot.get("page"),
        )
    return out


def _parse_previous_pages(previous: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Round-trip the `pages:` block from a previous .layout.yml (TASK-124)."""
    if previous is None:
        return []
    raw = previous.get("pages")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str):
            continue
        item: dict[str, Any] = {"name": name}
        title = entry.get("title")
        if isinstance(title, str) and title:
            item["title"] = title
        out.append(item)
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
    lines: list[str] = [f"schema: {LAYOUT_SCHEMA_VERSION}"]
    if result.pages:
        # EPIC-014 / TASK-124 — pages block emitted between schema and
        # placements, preserved in user-authored declaration order
        # (not sorted) so the renderer's page-suffix order is stable.
        lines.append("pages:")
        for entry in result.pages:
            parts = [f"name: {entry['name']}"]
            title = entry.get("title")
            if isinstance(title, str) and title:
                parts.append(f"title: {title}")
            lines.append("  - { " + ", ".join(parts) + " }")
    lines.append("placements:")
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
    # EPIC-014 / TASK-124 — `page:` emits last so existing single-page
    # layouts (page is None) produce byte-identical output.
    if p.page is not None:
        parts.append(f"page: {p.page}")
    return "{ " + ", ".join(parts) + " }"


def _format_float(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"
