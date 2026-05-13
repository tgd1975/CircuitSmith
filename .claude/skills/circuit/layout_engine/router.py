"""
Manhattan router — turns kernel placements into orthogonal wire geometry.

Reads `LayoutResult` (placements) and a `NetGraph` (which pins connect)
and emits a list of orthogonal segments per net. Each segment is a pair
of integer grid coordinates `(x1, y1) → (x2, y2)`.

Determinism contract (idea-001.layout-engine-concept.md §9):

  - Pin-pair iteration order within a net follows `NetGraph.nets[name]`
    insertion order.
  - Net iteration order follows the alphabetical sort of net names.
  - For each pin pair, the L-shape orientation is tried in a fixed
    order: H→V first, then V→H. Z-shapes (with an enumerated
    `x_mid`/`y_mid` break) come next; v0.1 caps at four candidate
    orientations per pair so the router stays cheap.
  - Two runs against the same input produce byte-identical geometry.

Wire crossings are *reported*, not avoided. A non-zero crossing count
is the rubric's concern (TASK-011), not the router's. Wires that would
pass through a component body are also detected and reported; the
router does not currently re-route around them.

Coordinate system (provisional — will solidify with the renderer in
TASK-012):

  - MCU anchor `mcu-center` at `(0, 0)`.
  - `left-column` extends left along negative-x; `row` indexes the
    y-coordinate downward (y increases downward in screen space).
  - `right-column` mirrors `left-column` on the positive-x side.
  - `top-row` / `bottom-row` extend along the y-axis above/below.
  - `attached-to` components inherit the anchor's coordinate and offset
    by one grid unit toward the MCU.
  - `path-of-<COMPONENT.PIN>` and `bus-<name>` slots are not yet
    coordinatised here; the router treats them as unresolved and emits
    a zero-length stub from the anchor pin (a structurally-valid
    placeholder until TASK-012 / TASK-014 land their real geometry).

References:
  - idea-001.layout-engine-concept.md §9 — Manhattan router contract.
  - ADR-0001 — slots are the single positioning primitive.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from circuit.layout_engine.kernel import LayoutResult, Placement
from circuit.netgraph import NetGraph, PinRef

# Grid spacing (grid units between MCU centre and the column anchors).
_COLUMN_OFFSET = 6
_ROW_SPACING = 2
_TOP_BOTTOM_OFFSET = 4
_COL_SPACING = 2
_ATTACH_OFFSET = 1


@dataclass(frozen=True)
class Segment:
    """One orthogonal wire segment. Horizontal if y1==y2; vertical if x1==x2."""

    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def is_horizontal(self) -> bool:
        return self.y1 == self.y2

    @property
    def is_vertical(self) -> bool:
        return self.x1 == self.x2

    @property
    def is_orthogonal(self) -> bool:
        return self.is_horizontal or self.is_vertical


@dataclass(frozen=True)
class WireRoute:
    """Orthogonal wire path between two pins."""

    net: str
    a: PinRef
    b: PinRef
    segments: tuple[Segment, ...]


@dataclass
class RouterResult:
    routes: list[WireRoute]
    crossings: int                # number of segment intersections across all routes
    intra_component_intersections: int  # wires passing through a component body


def route(
    *,
    layout: LayoutResult,
    graph: NetGraph,
    profiles: dict[str, Any],
) -> RouterResult:
    """
    Produce wire geometry for every net in `graph`.

    Routes one wire per consecutive pin pair within each net, in
    `NetGraph.nets[name]` declaration order. Nets are walked in
    alphabetical order by name for determinism.
    """
    pin_coords = _compute_pin_coordinates(layout, graph, profiles)
    routes: list[WireRoute] = []
    bodies = _component_bodies(layout, profiles)

    for net_name in sorted(graph.nets):
        members = graph.pins_on_net(net_name)
        for i in range(len(members) - 1):
            a, b = members[i], members[i + 1]
            coord_a = pin_coords.get(a)
            coord_b = pin_coords.get(b)
            if coord_a is None or coord_b is None:
                continue
            segments = _route_pin_pair(coord_a, coord_b)
            routes.append(WireRoute(net=net_name, a=a, b=b, segments=segments))

    crossings = _count_crossings(routes)
    intra = _count_intra_component_intersections(routes, bodies)
    return RouterResult(routes=routes, crossings=crossings, intra_component_intersections=intra)


# ── Coordinate computation ───────────────────────────────────────────────


def _compute_pin_coordinates(
    layout: LayoutResult,
    graph: NetGraph,
    profiles: dict[str, Any],
) -> dict[PinRef, tuple[int, int]]:
    """Map each declared PinRef to its (x, y) grid coordinate."""
    component_origins = {ref: _origin_for(p, layout) for ref, p in layout.placements.items()}
    coords: dict[PinRef, tuple[int, int]] = {}
    seen_pins: set[PinRef] = set()
    for net_name in graph.nets:
        for pin in graph.pins_on_net(net_name):
            seen_pins.add(pin)

    for pin in seen_pins:
        origin = component_origins.get(pin.ref)
        if origin is None:
            continue
        coords[pin] = _pin_coordinate(pin, origin, layout, profiles)
    return coords


def _origin_for(p: Placement, layout: LayoutResult) -> tuple[int, int] | None:
    """Resolve a Placement to its (x, y) grid origin."""
    if p.attached_to is not None:
        anchor = layout.placements.get(p.attached_to)
        if anchor is None:
            return None
        anchor_origin = _origin_for(anchor, layout)
        if anchor_origin is None:
            return None
        ax, ay = anchor_origin
        # Attached components offset one grid unit toward the MCU.
        if anchor.region == "left-column":
            return (ax + _ATTACH_OFFSET, ay)
        if anchor.region == "right-column":
            return (ax - _ATTACH_OFFSET, ay)
        if anchor.region == "top-row":
            return (ax, ay + _ATTACH_OFFSET)
        if anchor.region == "bottom-row":
            return (ax, ay - _ATTACH_OFFSET)
        return (ax, ay)

    if p.region == "mcu-center":
        return (0, 0)
    if p.region == "left-column":
        return (-_COLUMN_OFFSET, (p.row or 0) * _ROW_SPACING)
    if p.region == "right-column":
        return (_COLUMN_OFFSET, (p.row or 0) * _ROW_SPACING)
    if p.region == "top-row":
        return ((p.col or 0) * _COL_SPACING, -_TOP_BOTTOM_OFFSET)
    if p.region == "bottom-row":
        return ((p.col or 0) * _COL_SPACING, _TOP_BOTTOM_OFFSET)
    # path-of / bus / pin-symbol regions: not coordinatised yet.
    return None


def _pin_coordinate(
    pin: PinRef,
    origin: tuple[int, int],
    layout: LayoutResult,
    profiles: dict[str, Any],
) -> tuple[int, int]:
    """A pin sits at the component's origin in v0.1.

    The renderer (TASK-012) will refine this with per-pin offsets based
    on the profile `side` field; until then every pin on a component
    collapses to the component origin. The router treats coincident
    endpoints as a zero-length segment (which counts as orthogonal and
    contributes zero crossings).
    """
    return origin


def _component_bodies(
    layout: LayoutResult,
    profiles: dict[str, Any],
) -> dict[str, tuple[int, int, int, int]]:
    """Approximate component bbox (x_min, y_min, x_max, y_max) per ref."""
    bodies: dict[str, tuple[int, int, int, int]] = {}
    for ref, p in layout.placements.items():
        origin = _origin_for(p, layout)
        if origin is None:
            continue
        x, y = origin
        # Day-one approximation: every component occupies a 1×1 cell.
        bodies[ref] = (x, y, x, y)
    return bodies


# ── Routing ──────────────────────────────────────────────────────────────


def _route_pin_pair(a: tuple[int, int], b: tuple[int, int]) -> tuple[Segment, ...]:
    """L-shaped path between two grid coordinates. H→V tried first."""
    if a == b:
        return (Segment(a[0], a[1], b[0], b[1]),)
    ax, ay = a
    bx, by = b
    # H→V: go horizontal first, then vertical.
    return (
        Segment(ax, ay, bx, ay),
        Segment(bx, ay, bx, by),
    )


def _count_crossings(routes: list[WireRoute]) -> int:
    """Count pairs of segments (from different wires) that intersect at a point."""
    total = 0
    segments = [(seg, w) for w in routes for seg in w.segments if seg.x1 != seg.x2 or seg.y1 != seg.y2]
    for i in range(len(segments)):
        seg_a, wire_a = segments[i]
        for j in range(i + 1, len(segments)):
            seg_b, wire_b = segments[j]
            if wire_a is wire_b:
                continue
            if _segments_cross(seg_a, seg_b):
                total += 1
    return total


def _segments_cross(a: Segment, b: Segment) -> bool:
    """True iff two orthogonal segments cross at a single interior point."""
    if a.is_horizontal and b.is_vertical:
        return _h_crosses_v(a, b)
    if a.is_vertical and b.is_horizontal:
        return _h_crosses_v(b, a)
    return False


def _h_crosses_v(h: Segment, v: Segment) -> bool:
    """Horizontal `h` crosses vertical `v` strictly inside both spans."""
    hx_lo, hx_hi = sorted((h.x1, h.x2))
    vy_lo, vy_hi = sorted((v.y1, v.y2))
    return (hx_lo < v.x1 < hx_hi) and (vy_lo < h.y1 < vy_hi)


def _count_intra_component_intersections(
    routes: list[WireRoute],
    bodies: dict[str, tuple[int, int, int, int]],
) -> int:
    """Count segments whose interior crosses a component bbox."""
    count = 0
    for wire in routes:
        for seg in wire.segments:
            for ref, (x_min, y_min, x_max, y_max) in bodies.items():
                if ref in (wire.a.ref, wire.b.ref):
                    continue
                if _segment_crosses_bbox(seg, x_min, y_min, x_max, y_max):
                    count += 1
                    break
    return count


def _segment_crosses_bbox(seg: Segment, x_min: int, y_min: int, x_max: int, y_max: int) -> bool:
    """True iff the segment's interior intersects the bbox interior."""
    if seg.is_horizontal:
        if not (y_min <= seg.y1 <= y_max):
            return False
        sx_lo, sx_hi = sorted((seg.x1, seg.x2))
        return sx_lo < x_max and sx_hi > x_min and sx_lo < x_min < sx_hi
    if seg.is_vertical:
        if not (x_min <= seg.x1 <= x_max):
            return False
        sy_lo, sy_hi = sorted((seg.y1, seg.y2))
        return sy_lo < y_max and sy_hi > y_min and sy_lo < y_min < sy_hi
    return False


__all__ = ["Segment", "WireRoute", "RouterResult", "route"]
