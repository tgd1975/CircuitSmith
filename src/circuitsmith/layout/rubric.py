"""
v0.1 structural rubric — gates the rendered layout before SVG emission.

Three blocking checks (idea-001.layout-engine-concept.md §10):

  - `overlaps`        — no two component bodies intersect.
  - `labels_fit`      — every pin label fits within its slot's label budget.
  - `wire_crossings`  — counted; the rubric blocks when over the
    configured threshold (default `0` per Phase 2a).

Two advisory numeric checks, *recorded* but never blocking:

  - `min_label_distance` — nearest-neighbour distance on label bboxes.
  - `density`            — grid-cell histogram of components + labels.

The rubric returns a `RubricResult` with one `Finding` per failing
blocking check plus the advisory metrics under `metrics`. A non-empty
`failures` list aborts SVG emission upstream (idea-001 §10 contract);
caller decides whether to surface waiver instructions.

References:
  - idea-001.layout-engine-concept.md §10 (rubric definition)
  - TASK-019 — numeric-check promotion to blocking (Phase 2b)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from circuitsmith.layout.kernel import LayoutResult, Placement
from circuitsmith.layout.router import RouterResult

# Per-region default label budget (grid units). Configurable per slot
# via `label-budget:` in layout.yml (idea-001 §4.2); the v0.1 default is
# bounded by a single grid cell.
DEFAULT_LABEL_BUDGET = 8

# Blocking threshold for wire_crossings. Day-one is zero; authors who
# need to ship a crossed layout can waive via meta.yml.reviewed.waivers.
DEFAULT_WIRE_CROSSING_THRESHOLD = 0

# Phase 2b numeric thresholds — promoted from advisory to blocking
# under TASK-019. Calibration is per `idea-001.layout-engine-concept.md
# §10` (75th percentile of green Phase 2a runs as the floor); the v0.1
# corpus is two shipped circuits (esp32, nrf52840) both reporting
# `min_label_distance = 1` and `density = 0.1453`. The thresholds below
# accept that corpus and tighten as the trigger gate accumulates more
# green runs.
DEFAULT_MIN_LABEL_DISTANCE_THRESHOLD = 1
"""Minimum Manhattan distance between labelled placement bboxes (lower fails)."""

DEFAULT_DENSITY_THRESHOLD = 0.5
"""Max occupied-cells/bbox-area ratio (higher fails — layout is too crowded)."""


@dataclass(frozen=True)
class Finding:
    """One rubric failure — names check + offending entities."""

    check: str                     # "overlaps" | "labels_fit" | "wire_crossings"
    severity: str                  # "error" (blocking) | "warning" (advisory)
    message: str                   # human-facing summary
    refs: tuple[str, ...] = ()     # component refs / net names involved


@dataclass
class RubricResult:
    findings: list[Finding] = field(default_factory=list)
    metrics: dict[str, float | int | bool] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]


def evaluate(
    *,
    layout: LayoutResult,
    router_result: RouterResult,
    label_budgets: dict[str, int] | None = None,
    wire_crossing_threshold: int = DEFAULT_WIRE_CROSSING_THRESHOLD,
    min_label_distance_threshold: float | None = DEFAULT_MIN_LABEL_DISTANCE_THRESHOLD,
    density_threshold: float | None = DEFAULT_DENSITY_THRESHOLD,
) -> RubricResult:
    """
    Run the rubric over the placement + router output.

    `label_budgets` overrides the per-region default; pass a mapping
    `{region_name: budget}` for slots whose labels need more room.

    `min_label_distance_threshold` / `density_threshold` were
    advisory-only in v0.1 (TASK-011); under TASK-019 they are promoted
    to blocking. Pass `None` to suppress either check (matches the
    v0.1 advisory-only behaviour — useful for pre-Phase-2b fixtures
    that haven't been re-baselined yet).
    """
    findings: list[Finding] = []
    metrics: dict[str, float | int | bool] = {}

    # ── overlaps ─────────────────────────────────────────────────────────
    overlap_pairs = _detect_overlaps(layout.placements)
    metrics["overlaps"] = len(overlap_pairs)
    if overlap_pairs:
        findings.append(Finding(
            check="overlaps",
            severity="error",
            message=(
                f"{len(overlap_pairs)} component pair(s) overlap: "
                + ", ".join(f"{a}↔{b}" for a, b in overlap_pairs)
            ),
            refs=tuple(sorted({ref for pair in overlap_pairs for ref in pair})),
        ))

    # ── labels_fit ───────────────────────────────────────────────────────
    label_failures = _detect_label_failures(layout.placements, label_budgets)
    metrics["labels_fit"] = not label_failures
    if label_failures:
        findings.append(Finding(
            check="labels_fit",
            severity="error",
            message=(
                f"{len(label_failures)} label(s) exceed their slot budget: "
                + ", ".join(label_failures)
            ),
            refs=tuple(label_failures),
        ))

    # ── wire_crossings ───────────────────────────────────────────────────
    metrics["wire_crossings"] = router_result.crossings
    if router_result.crossings > wire_crossing_threshold:
        findings.append(Finding(
            check="wire_crossings",
            severity="error",
            message=(
                f"{router_result.crossings} wire crossing(s) exceeds threshold "
                f"{wire_crossing_threshold}"
            ),
            refs=tuple(_crossing_refs(router_result)),
        ))

    # ── numeric checks (Phase 2b promotion — TASK-019) ───────────────────
    metrics["min_label_distance"] = _min_label_distance(layout.placements)
    metrics["density"] = _density(layout.placements)
    metrics["intra_component_intersections"] = router_result.intra_component_intersections

    if (
        min_label_distance_threshold is not None
        and metrics["min_label_distance"] != float("inf")
        and metrics["min_label_distance"] < min_label_distance_threshold
    ):
        findings.append(Finding(
            check="min_label_distance",
            severity="error",
            message=(
                f"min_label_distance = {metrics['min_label_distance']} "
                f"falls below threshold {min_label_distance_threshold}"
            ),
            refs=tuple(_labelled_refs(layout.placements)),
        ))

    if (
        density_threshold is not None
        and metrics["density"] > density_threshold
    ):
        findings.append(Finding(
            check="density",
            severity="error",
            message=(
                f"density = {metrics['density']:.4g} exceeds threshold {density_threshold}"
            ),
            refs=tuple(sorted(layout.placements)),
        ))

    return RubricResult(findings=findings, metrics=metrics)


def _labelled_refs(placements: dict[str, Placement]) -> list[str]:
    """Sorted list of refs whose placements carry a label."""
    return sorted(ref for ref, p in placements.items() if p.label is not None)


# ── overlaps ─────────────────────────────────────────────────────────────


def _detect_overlaps(placements: dict[str, Placement]) -> list[tuple[str, str]]:
    """Return sorted (ref_a, ref_b) pairs whose bboxes share a grid cell."""
    cells: dict[tuple[int, int], list[str]] = {}
    for ref, p in placements.items():
        bbox = _placement_bbox(p, placements)
        if bbox is None:
            continue
        x_min, y_min, x_max, y_max = bbox
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                cells.setdefault((x, y), []).append(ref)
    pairs: set[tuple[str, str]] = set()
    for cell, refs in cells.items():
        if len(refs) > 1:
            refs_sorted = sorted(refs)
            for i in range(len(refs_sorted)):
                for j in range(i + 1, len(refs_sorted)):
                    pairs.add((refs_sorted[i], refs_sorted[j]))
    return sorted(pairs)


def _placement_bbox(p: Placement, all_placements: dict[str, Placement]) -> tuple[int, int, int, int] | None:
    """1×1 bbox at the placement's grid origin (collapsed in v0.1)."""
    if p.attached_to is not None:
        # Attached components live one cell off the anchor; rely on the
        # anchor's bbox + the attach offset that the router applies.
        anchor = all_placements.get(p.attached_to)
        if anchor is None:
            return None
        anchor_bbox = _placement_bbox(anchor, all_placements)
        if anchor_bbox is None:
            return None
        ax_min, ay_min, ax_max, ay_max = anchor_bbox
        if anchor.region == "left-column":
            return (ax_min + 1, ay_min, ax_max + 1, ay_max)
        if anchor.region == "right-column":
            return (ax_min - 1, ay_min, ax_max - 1, ay_max)
        if anchor.region == "top-row":
            return (ax_min, ay_min + 1, ax_max, ay_max + 1)
        if anchor.region == "bottom-row":
            return (ax_min, ay_min - 1, ax_max, ay_max - 1)
        return anchor_bbox
    if p.region == "mcu-center":
        # MCU is a multi-cell block in the renderer; approximate as 1×1 for v0.1.
        return (0, 0, 0, 0)
    if p.region == "left-column":
        return (-6, (p.row or 0) * 2, -6, (p.row or 0) * 2)
    if p.region == "right-column":
        return (6, (p.row or 0) * 2, 6, (p.row or 0) * 2)
    if p.region == "top-row":
        return ((p.col or 0) * 2, -4, (p.col or 0) * 2, -4)
    if p.region == "bottom-row":
        return ((p.col or 0) * 2, 4, (p.col or 0) * 2, 4)
    return None


# ── labels_fit ───────────────────────────────────────────────────────────


def _detect_label_failures(
    placements: dict[str, Placement],
    overrides: dict[str, int] | None,
) -> list[str]:
    """Return the refs whose label text exceeds the budget for their region."""
    overrides = overrides or {}
    failures: list[str] = []
    for ref, p in placements.items():
        if p.label is None or p.region is None:
            continue
        budget = overrides.get(p.region, DEFAULT_LABEL_BUDGET)
        # Day-one heuristic: label text length ≈ grid units consumed.
        if len(ref) > budget:
            failures.append(ref)
    return sorted(failures)


# ── wire_crossings refs surface ──────────────────────────────────────────


def _crossing_refs(router_result: RouterResult) -> Iterable[str]:
    """Surface the set of nets involved in crossings (best-effort)."""
    nets_seen: set[str] = set()
    for wire in router_result.routes:
        nets_seen.add(wire.net)
    return sorted(nets_seen)


# ── advisory metrics ─────────────────────────────────────────────────────


def _min_label_distance(placements: dict[str, Placement]) -> float:
    """Nearest-neighbour Manhattan distance between labeled placements."""
    labeled = [(ref, p) for ref, p in placements.items() if p.label is not None]
    if len(labeled) < 2:
        return float("inf")
    best = float("inf")
    coords = [(ref, _placement_bbox(p, placements)) for ref, p in labeled]
    coords = [(ref, bbox) for ref, bbox in coords if bbox is not None]
    for i in range(len(coords)):
        ref_a, bbox_a = coords[i]
        for j in range(i + 1, len(coords)):
            ref_b, bbox_b = coords[j]
            d = abs(bbox_a[0] - bbox_b[0]) + abs(bbox_a[1] - bbox_b[1])
            if d < best:
                best = d
    return float(best)


def _density(placements: dict[str, Placement]) -> float:
    """Occupied-cells / bbox-area ratio for a coarse density measure."""
    cells: set[tuple[int, int]] = set()
    for p in placements.values():
        bbox = _placement_bbox(p, placements)
        if bbox is None:
            continue
        x_min, y_min, x_max, y_max = bbox
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                cells.add((x, y))
    if not cells:
        return 0.0
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    width = max(xs) - min(xs) + 1
    height = max(ys) - min(ys) + 1
    bbox_area = width * height
    return len(cells) / bbox_area if bbox_area else 0.0


__all__ = ["Finding", "RubricResult", "evaluate", "DEFAULT_WIRE_CROSSING_THRESHOLD"]
