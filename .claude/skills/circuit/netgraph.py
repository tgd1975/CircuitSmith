"""
NetGraph — typed connectivity model derived from a validated .circuit.yml.

Single shared contract between the YAML source and three downstream
consumers (ADR-0003):

  - erc_engine.py            — runs ERC predicates against this graph
  - layout_engine/kernel.py  — routes nets between component pins
  - netlist_exporter.py      — emits KiCad .net by walking NetGraph.nets

bom_exporter.py is deliberately not a consumer (ADR-0004): it iterates
`components` directly, never NetGraph.

The three connection forms allowed in .circuit.yml (`pins`, `path`,
`bus`) all flatten into one canonical net representation. Downstream
code never branches on which form the human wrote.

Invariants surfaced by .claude/skills/co-netgraph/SKILL.md:
  - Hash determinism across parses (canonical_hash).
  - No layout coordinates in the model — geometry lives in
    layout_engine/.
  - Read-only contract for consumers.
  - No host-project imports (ADR-0007 portability).

Source of truth: idea-001.erc-engine.md §Net graph data model and
idea-001.yaml-format.md §Form 2 (path segment-count rule).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any, Iterable


@dataclass(frozen=True, order=True)
class PinRef:
    """A reference to one pin on one component, e.g. PinRef('U1', 'IO13')."""

    ref: str
    pin: str

    def __str__(self) -> str:
        return f"{self.ref}.{self.pin}"


@dataclass(frozen=True)
class NetMeta:
    """
    Sibling metadata for one net. Lives in NetGraph.net_meta keyed by net
    name. Kept separate from NetGraph.nets so the topology graph stays
    minimal and adjacency caches can be invalidation-free.
    """

    pull: str | None = None
    role: str | dict[str, str] | None = None
    erc_overrides: dict[str, str] | None = None
    segment_names: tuple[str, ...] | None = None
    bus_backbone_count: int = 0  # prefix length of pins_on_net for `bus:` nets; 0 otherwise


@dataclass(frozen=True)
class _PathNode:
    """One grouped node inside a path: either consecutive pins of one ref, or a bare net-name token."""

    ref: str | None       # None for net-name nodes
    pins: tuple[PinRef, ...]  # empty tuple for net-name nodes
    netname: str | None   # set on net-name nodes only

    @property
    def is_netname(self) -> bool:
        return self.netname is not None

    @property
    def left_pin(self) -> PinRef:
        return self.pins[0]

    @property
    def right_pin(self) -> PinRef:
        return self.pins[-1]


class NetGraph:
    """Topology-only model of a circuit. Constructed via from_yaml_dict()."""

    def __init__(
        self,
        nets: dict[str, list[PinRef]],
        net_meta: dict[str, NetMeta],
        path_segments: dict[str, tuple[str, ...]],
    ) -> None:
        self._nets: dict[str, list[PinRef]] = nets
        self._net_meta: dict[str, NetMeta] = net_meta
        # path-source-net-name → ordered tuple of segment names (NetGraph.nets keys)
        self._path_segments: dict[str, tuple[str, ...]] = path_segments
        self._pin_index_cache: dict[PinRef, tuple[str, ...]] | None = None

    # ── public surface ────────────────────────────────────────────────────

    @property
    def nets(self) -> dict[str, list[PinRef]]:
        """name → ordered list of pin members (insertion order preserved)."""
        return self._nets

    @property
    def net_meta(self) -> dict[str, NetMeta]:
        return self._net_meta

    @property
    def pin_index(self) -> dict[PinRef, tuple[str, ...]]:
        """PinRef → tuple of net names containing this pin (build once, cached)."""
        if self._pin_index_cache is None:
            idx: dict[PinRef, list[str]] = {}
            for name, members in self._nets.items():
                for pin in members:
                    bucket = idx.setdefault(pin, [])
                    if name not in bucket:
                        bucket.append(name)
            self._pin_index_cache = {p: tuple(names) for p, names in idx.items()}
        return self._pin_index_cache

    def pins_on_net(self, name: str) -> list[PinRef]:
        """Members of the named net, in canonical order."""
        return list(self._nets[name])

    def nets_containing_pin(self, pin: PinRef) -> list[str]:
        """All net names whose membership includes this pin."""
        return list(self.pin_index.get(pin, ()))

    def flattened_segments(self, path_net: str) -> list[tuple[PinRef, PinRef]]:
        """
        Consecutive segment endpoint pairs for a path-sourced net, in
        declaration order. Consumer: netlist_exporter.

        Each segment's pair is (left_endpoint, right_endpoint) — the pins
        from the two adjacent nodes that share this segment's wire. For
        segments terminating at a bare net-name node, the pin-side
        endpoint is repeated on the net-name side so the pair shape stays
        regular (the merge has already wired the named net's membership).
        """
        if path_net not in self._path_segments:
            raise ValueError(
                f"flattened_segments: {path_net!r} is not a path-sourced net "
                f"(known path sources: {sorted(self._path_segments)})"
            )
        return [
            self._segment_endpoints(seg_name)
            for seg_name in self._path_segments[path_net]
        ]

    def components_between(self, a: PinRef, b: PinRef) -> list[str]:
        """
        Ordered list of component refs traversed between two pins on the
        same path-sourced net. Raises if the pins are not co-located on
        a path net or are not path-reachable.

        Consumers: ERC checks E2 ("is there a resistor between GPIO and
        LED anode?") and E3 ("read that resistor's value").
        """
        # Identify a path source whose flattened segments contain both pins.
        for path_net, seg_names in self._path_segments.items():
            ordered_pins = self._path_walk_pins(seg_names)
            if a in ordered_pins and b in ordered_pins:
                start, end = ordered_pins.index(a), ordered_pins.index(b)
                lo, hi = (start, end) if start <= end else (end, start)
                walked = ordered_pins[lo:hi + 1]
                # Component refs in walk order, deduplicated as adjacent grouping
                refs: list[str] = []
                for pin in walked:
                    if pin.ref and (not refs or refs[-1] != pin.ref):
                        refs.append(pin.ref)
                # Endpoint refs are part of the walk; strip them — callers
                # want what lies between, not the endpoints themselves.
                return refs[1:-1] if len(refs) >= 2 else []
        raise ValueError(
            f"components_between: {a} and {b} are not co-located on any path-sourced net"
        )

    def canonical_hash(self) -> str:
        """
        Stable SHA-256 hex digest of the graph. Two NetGraphs constructed
        from the same .circuit.yml input produce byte-identical hashes,
        regardless of dict-iteration luck. Gated by the TASK-053 golden-
        hash CI contract.
        """
        return sha256(self._canonical_bytes()).hexdigest()

    # ── construction ──────────────────────────────────────────────────────

    @classmethod
    def from_yaml_dict(cls, circuit: dict[str, Any]) -> NetGraph:
        """
        Build a NetGraph from a parsed (and schema-validated) .circuit.yml
        dict. The caller is responsible for running schema validation
        first; this constructor assumes structural validity and raises
        on unrecoverable shape problems.
        """
        nets: dict[str, list[PinRef]] = {}
        net_meta: dict[str, NetMeta] = {}
        path_segments: dict[str, tuple[str, ...]] = {}

        declared_net_names = {entry["net"] for entry in circuit["connections"]}

        for entry in circuit["connections"]:
            name = entry["net"]
            if "pins" in entry:
                cls._build_pins_net(name, entry, nets, net_meta)
            elif "path" in entry:
                cls._build_path_net(
                    name, entry, nets, net_meta, path_segments, declared_net_names
                )
            elif entry.get("bus") is True:
                cls._build_bus_net(name, entry, nets, net_meta)
            else:
                raise ValueError(
                    f"NetGraph.from_yaml_dict: net {name!r} has no pins/path/bus form"
                )

        return cls(nets=nets, net_meta=net_meta, path_segments=path_segments)

    # ── builders for each form ────────────────────────────────────────────

    @staticmethod
    def _build_pins_net(
        name: str,
        entry: dict[str, Any],
        nets: dict[str, list[PinRef]],
        net_meta: dict[str, NetMeta],
    ) -> None:
        members = [_parse_pin_token(tok) for tok in entry["pins"]]
        _merge_into_net(nets, name, members)
        net_meta[name] = _meta_from_entry(entry)

    @classmethod
    def _build_path_net(
        cls,
        name: str,
        entry: dict[str, Any],
        nets: dict[str, list[PinRef]],
        net_meta: dict[str, NetMeta],
        path_segments: dict[str, tuple[str, ...]],
        declared_net_names: set[str],
    ) -> None:
        nodes = _group_path_nodes(entry["path"])
        if len(nodes) < 2:
            raise ValueError(
                f"NetGraph: path net {name!r} requires at least two nodes; got {len(nodes)}"
            )

        override = entry.get("segment_names")
        expected_segment_count = len(nodes) - 1
        if override is not None and len(override) != expected_segment_count:
            raise ValueError(
                f"NetGraph: path net {name!r} has {expected_segment_count} segment(s) "
                f"but segment_names declares {len(override)} entry(ies). "
                f"This is a post-schema validation failure; the validator should "
                f"have caught it before NetGraph construction."
            )

        segment_names: list[str] = []
        for index in range(expected_segment_count):
            left, right = nodes[index], nodes[index + 1]
            seg_name = (
                override[index]
                if override is not None
                else (name if index == 0 else _content_addressed_name(name, left, right))
            )
            # Endpoint pins for this segment: pin-side endpoints only.
            seg_members: list[PinRef] = []
            if not left.is_netname:
                seg_members.append(left.right_pin)
            if not right.is_netname:
                seg_members.append(right.left_pin)
            _merge_into_net(nets, seg_name, seg_members)
            # Net-name endpoints trigger the merge into the named net.
            if left.is_netname and left.netname in declared_net_names:
                _merge_into_net(nets, left.netname, [right.left_pin])
            if right.is_netname and right.netname in declared_net_names:
                _merge_into_net(nets, right.netname, [left.right_pin])
            segment_names.append(seg_name)

        path_segments[name] = tuple(segment_names)
        # Meta lives on the declared (first) segment only — the user-named
        # net. Content-addressed segments inherit no metadata.
        net_meta[name] = _meta_from_entry(
            entry, segment_names=tuple(segment_names) if override is not None else None
        )

    @staticmethod
    def _build_bus_net(
        name: str,
        entry: dict[str, Any],
        nets: dict[str, list[PinRef]],
        net_meta: dict[str, NetMeta],
    ) -> None:
        backbone = [_parse_pin_token(tok) for tok in entry["backbone"]]
        taps = [_parse_pin_token(tok) for tok in entry.get("taps", [])]
        # bus collapses to one entry: backbone first (in declared order), then taps.
        # bus_backbone_count records the prefix length so consumers that care
        # (the renderer's stub drawing) can split it back out.
        members = backbone + taps
        _merge_into_net(nets, name, members)
        meta = _meta_from_entry(entry)
        net_meta[name] = replace(meta, bus_backbone_count=len(backbone))

    # ── internals ─────────────────────────────────────────────────────────

    def _segment_endpoints(self, seg_name: str) -> tuple[PinRef, PinRef]:
        members = self._nets[seg_name]
        if len(members) == 2:
            return members[0], members[1]
        if len(members) == 1:
            # Segment terminating at a net-name node — pair the single pin
            # with itself for shape regularity. Callers that need to know
            # the segment touches a named-net node can consult net_meta or
            # the originating segment name.
            return members[0], members[0]
        raise AssertionError(
            f"NetGraph: segment {seg_name!r} has {len(members)} members; "
            f"expected 1 or 2 from path-flattening"
        )

    def _path_walk_pins(self, seg_names: Iterable[str]) -> list[PinRef]:
        """Concatenate segment endpoint pairs into one walk, deduping seams."""
        walk: list[PinRef] = []
        for seg in seg_names:
            members = self._nets[seg]
            for pin in members:
                if walk and walk[-1] == pin:
                    continue
                walk.append(pin)
        return walk

    def _canonical_bytes(self) -> bytes:
        """Deterministic byte serialisation for canonical_hash()."""
        parts: list[str] = ["NETS"]
        for name, members in self._nets.items():
            member_str = ",".join(f"{p.ref}.{p.pin}" for p in members)
            parts.append(f"{name}|{member_str}")
        parts.append("NET_META")
        for name, meta in self._net_meta.items():
            parts.append(
                f"{name}|pull={meta.pull}|role={meta.role}"
                f"|erc={meta.erc_overrides}|seg={meta.segment_names}"
                f"|bbc={meta.bus_backbone_count}"
            )
        parts.append("PATH_SEGMENTS")
        for source, segs in self._path_segments.items():
            parts.append(f"{source}|{','.join(segs)}")
        return "\n".join(parts).encode("utf-8")


# ── module-level helpers ─────────────────────────────────────────────────


def _parse_pin_token(token: str) -> PinRef:
    """REF.PIN → PinRef. Schema has already enforced the shape."""
    ref, _, pin = token.partition(".")
    if not pin:
        raise ValueError(f"NetGraph: pin token {token!r} is not REF.PIN")
    return PinRef(ref=ref, pin=pin)


def _group_path_nodes(path: list[str]) -> list[_PathNode]:
    """
    Walk a path's tokens and group them into nodes per yaml-format §Form 2:
      - Net-name tokens (no `.`) are single-token nodes.
      - Consecutive REF.PIN tokens with the same REF collapse into one
        node carrying its pins in declaration order.
    """
    nodes: list[_PathNode] = []
    current_ref: str | None = None
    current_pins: list[PinRef] = []

    def flush_current() -> None:
        nonlocal current_ref, current_pins
        if current_ref is not None and current_pins:
            nodes.append(_PathNode(ref=current_ref, pins=tuple(current_pins), netname=None))
        current_ref = None
        current_pins = []

    for token in path:
        if "." in token:
            ref, _, pin = token.partition(".")
            pin_ref = PinRef(ref=ref, pin=pin)
            if current_ref == ref:
                current_pins.append(pin_ref)
            else:
                flush_current()
                current_ref = ref
                current_pins = [pin_ref]
        else:
            flush_current()
            nodes.append(_PathNode(ref=None, pins=(), netname=token))
    flush_current()
    return nodes


def _content_addressed_name(net_name: str, left: _PathNode, right: _PathNode) -> str:
    """
    Stable segment name for non-first segments per yaml-format §Form 2:
      <net>__<RefA>_<pinA>__<RefB>_<pinB>

    For a segment touching a net-name node, the net-name slot is filled
    with the bare net name (no ref); this keeps the names path-position-
    independent so inserting an unrelated net does not renumber segments.
    """
    left_token = (
        f"{left.netname}" if left.is_netname else f"{left.right_pin.ref}_{left.right_pin.pin}"
    )
    right_token = (
        f"{right.netname}" if right.is_netname else f"{right.left_pin.ref}_{right.left_pin.pin}"
    )
    return f"{net_name}__{left_token}__{right_token}"


def _merge_into_net(
    nets: dict[str, list[PinRef]],
    name: str,
    new_members: list[PinRef],
) -> None:
    """Append new pins to a net, preserving insertion order and deduplicating."""
    bucket = nets.setdefault(name, [])
    for pin in new_members:
        if pin not in bucket:
            bucket.append(pin)


def _meta_from_entry(
    entry: dict[str, Any],
    *,
    segment_names: tuple[str, ...] | None = None,
) -> NetMeta:
    """Pull NetMeta fields from a connections[*] entry; ignores topology fields."""
    return NetMeta(
        pull=entry.get("pull"),
        role=entry.get("role"),
        erc_overrides=entry.get("erc"),
        segment_names=segment_names,
        bus_backbone_count=0,
    )


__all__ = ["PinRef", "NetMeta", "NetGraph"]
