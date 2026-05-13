"""
Top-level renderer — orchestrates the full pipeline for one circuit.

Reads a `.circuit.yml`, optional `.layout.yml`, and emits:

  - `<out>.svg`        — the rendered schematic (Schemdraw + SVG backend)
  - `<out>.layout.yml` — the (re-)written placement, deterministic
  - `<out>.meta.yml`   — provenance + rubric metrics sidecar (idea-001 §11)

Pipeline (idea-001-circuit-skill.md):

  1. Parse `.circuit.yml`.
  2. Schema-validate (TASK-005).
  3. Build NetGraph (TASK-008).
  4. Run kernel (TASK-009) → LayoutResult (consumes previous .layout.yml).
  5. Run router (TASK-010) → RouterResult.
  6. Evaluate rubric (TASK-011) → RubricResult; abort on failure.
  7. Emit SVG via Schemdraw.
  8. Write meta.yml.

A failure at steps 2/4/6 returns a non-zero CLI exit and surfaces a
structured diagnostic. Visual fidelity is the "readable, not pretty"
bar from `idea-001.layout-engine-concept.md §16.2`; the rich glyph
selection per component category lands as a follow-up.

This module is path-agnostic per ADR-0007: paths come from the CLI
invocation, never hard-coded relative to a specific host repo.

References:
  - idea-001-circuit-skill.md — pipeline overview
  - idea-001.layout-engine-concept.md §11 — meta.yml format
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from circuitsmith.layout import (
    AmbiguityEntry,
    ConvergenceResult,
    EscalationError,
    LLMClient,
    LayoutResult,
    Placement,
    RouterResult,
    RubricResult,
    converge,
    evaluate,
    place,
    render_layout_yaml,
    route,
)
from circuitsmith.netgraph import NetGraph
from circuitsmith.schema import (
    validate,
    validate_layout,
)
from circuitsmith.schema.registry import load_profiles

SKILL_VERSION = "circuit-skill@0.4.0"  # bump when behaviour changes; see ADR-0011


@dataclass
class RenderResult:
    layout: LayoutResult
    router_result: RouterResult
    rubric: RubricResult
    svg_path: Path
    layout_path: Path
    meta_path: Path


class RenderError(Exception):
    """Pipeline halt with structured diagnostic."""

    def __init__(self, stage: str, findings: list[Any], summary: str) -> None:
        super().__init__(summary)
        self.stage = stage
        self.findings = findings
        self.summary = summary


def render(
    *,
    circuit_path: Path,
    layout_path: Path | None,
    out_svg: Path,
    out_layout: Path | None = None,
    out_meta: Path | None = None,
    use_ai_placer: bool = False,
    ai_client: LLMClient | None = None,
) -> RenderResult:
    """
    Run the full pipeline. Raises `RenderError` on schema/rubric/kernel failure.

    `layout_path` is the *input* layout (previous run's). `out_layout`
    defaults to that path — the typical contributor flow re-writes it
    in place.

    `use_ai_placer` controls Phase 2b dispatch. Default `False` keeps
    the renderer hermetic for CI per ADR-0002 (AI only at authoring
    time, never in CI). Pass `True` to invoke `circuitsmith.layout.converge`
    when the kernel hits an `EscalationError`. The CLI `--no-ai` flag
    is the user-facing form: `--no-ai` (default) is the kernel-only
    path, `--ai` opts into the Phase 2b placer.

    `ai_client` is the `LLMClient` adapter to use when AI dispatch
    fires. Defaults to the production `AnthropicClient` adapter.
    """
    circuit = _load_yaml(circuit_path)

    schema_findings = validate(circuit)
    if schema_findings:
        raise RenderError(
            stage="circuit-schema",
            findings=schema_findings,
            summary=f"{len(schema_findings)} circuit-schema finding(s); first: {schema_findings[0].message}",
        )

    previous_layout: dict[str, Any] | None = None
    if layout_path is not None and layout_path.exists():
        previous_layout = _load_yaml(layout_path)
        layout_findings = validate_layout(previous_layout)
        if layout_findings:
            raise RenderError(
                stage="layout-schema",
                findings=layout_findings,
                summary=(
                    f"{len(layout_findings)} layout-schema finding(s); "
                    f"first: {layout_findings[0].message}"
                ),
            )

    graph = NetGraph.from_yaml_dict(circuit)
    profiles = load_profiles()
    # The kernel accepts a flat dict; copy so we don't mutate the cached registry.
    profile_index: dict[str, Any] = dict(profiles)

    escalations: list[dict[str, str]] = []
    actual_out_meta = out_meta or out_svg.with_suffix(".meta.yml")
    actual_out_layout = out_layout or (layout_path if layout_path is not None else out_svg.with_suffix(".layout.yml"))

    ai_invocations: list[dict[str, Any]] = []

    try:
        layout = place(
            circuit=circuit,
            graph=graph,
            profiles=profile_index,
            previous_layout=previous_layout,
            collect_escalations=use_ai_placer,
        )
    except EscalationError as exc:
        # `collect_escalations=True` keeps the kernel from raising, so this
        # branch only fires on the kernel-only `--no-ai` path.
        escalations.append({
            "category": exc.reason,
            "component": exc.ref,
            "circuit": circuit_path.name,
            "detail": str(exc),
        })
        actual_out_meta.parent.mkdir(parents=True, exist_ok=True)
        actual_out_meta.write_text(_emit_meta_yaml_incomplete(
            circuit_path=circuit_path,
            layout_path=actual_out_layout,
            circuit=circuit,
            escalations=escalations,
            placed=0,
            ai_invocations=ai_invocations,
        ))
        raise RenderError(
            stage="kernel",
            findings=[exc],
            summary=f"kernel escalation ({exc.reason}) on {exc.ref}: {exc}",
        ) from None

    if use_ai_placer and layout.unplaced:
        ai_result = _dispatch_ai_placer(
            circuit=circuit,
            layout=layout,
            graph=graph,
            profile_index=profile_index,
            ai_client=ai_client,
        )
        ai_invocations.append({
            "reason": ai_result.reason,
            "iterations": ai_result.iterations,
            "input_tokens": ai_result.total_input_tokens,
            "output_tokens": ai_result.total_output_tokens,
            "components": sorted(ref for ref, _, _ in layout.unplaced),
        })
        if not ai_result.converged:
            for ref, kernel_reason, kernel_detail in layout.unplaced:
                escalations.append({
                    "category": kernel_reason,
                    "component": ref,
                    "circuit": circuit_path.name,
                    "detail": kernel_detail,
                })
            escalations.append({
                "category": f"ai-placer-{ai_result.reason}",
                "circuit": circuit_path.name,
                "detail": (
                    f"AI placer did not converge in {ai_result.iterations} iteration(s); "
                    f"cumulative cost {ai_result.total_input_tokens}/{ai_result.total_output_tokens} "
                    f"in/out tokens"
                ),
            })
            actual_out_meta.parent.mkdir(parents=True, exist_ok=True)
            actual_out_meta.write_text(_emit_meta_yaml_incomplete(
                circuit_path=circuit_path,
                layout_path=actual_out_layout,
                circuit=circuit,
                escalations=escalations,
                placed=len(layout.placements),
                ai_invocations=ai_invocations,
            ))
            raise RenderError(
                stage="ai-placer",
                findings=[ai_result],
                summary=(
                    f"AI placer did not converge ({ai_result.reason}); "
                    f"hand-author `free`-slot entries for "
                    f"{', '.join(ref for ref, _, _ in layout.unplaced)} in layout.yml"
                ),
            ) from None
        # AI converged — merge proposals into the kernel's LayoutResult.
        for ref, ai_placement in ai_result.placements.items():
            layout.placements[ref] = Placement(
                ref=ref,
                region=ai_placement.region,
                row=ai_placement.row,
                col=ai_placement.col,
                position=ai_placement.position,
                step=ai_placement.step,
                attached_to=ai_placement.attached_to,
                attach_step=ai_placement.attach_step,
                label=ai_placement.label,
                topology_fingerprint=f"sha1:ai-{ai_result.reason}",
            )
        layout.unplaced = []

    router_result = route(layout=layout, graph=graph, profiles=profile_index)

    rubric_result = evaluate(layout=layout, router_result=router_result)
    if not rubric_result.passed:
        for failure in rubric_result.failures:
            escalations.append({
                "category": f"rubric-fail-{failure.check.replace('_', '-')}",
                "circuit": circuit_path.name,
                "detail": failure.message,
            })
        actual_out_meta.parent.mkdir(parents=True, exist_ok=True)
        actual_out_meta.write_text(_emit_meta_yaml(
            circuit_path=circuit_path,
            layout_path=actual_out_layout,
            circuit=circuit,
            layout=layout,
            rubric=rubric_result,
            router_result=router_result,
            escalations=escalations,
            state="incomplete",
            ai_invocations=ai_invocations,
        ))
        raise RenderError(
            stage="rubric",
            findings=rubric_result.failures,
            summary=(
                f"{len(rubric_result.failures)} rubric failure(s); first: "
                f"{rubric_result.failures[0].message}"
            ),
        )

    out_svg.parent.mkdir(parents=True, exist_ok=True)
    svg_bytes = _emit_svg(circuit, layout, router_result)
    out_svg.write_bytes(svg_bytes)

    layout_yaml = render_layout_yaml(layout)
    actual_out_layout.parent.mkdir(parents=True, exist_ok=True)
    actual_out_layout.write_text(layout_yaml)

    actual_out_meta.write_text(_emit_meta_yaml(
        circuit_path=circuit_path,
        layout_path=actual_out_layout,
        circuit=circuit,
        layout=layout,
        rubric=rubric_result,
        router_result=router_result,
        escalations=escalations,
        state="complete",
        ai_invocations=ai_invocations,
    ))

    return RenderResult(
        layout=layout,
        router_result=router_result,
        rubric=rubric_result,
        svg_path=out_svg,
        layout_path=actual_out_layout,
        meta_path=actual_out_meta,
    )


# ── SVG emission ─────────────────────────────────────────────────────────


def _emit_svg(
    circuit: dict[str, Any],
    layout: LayoutResult,
    router_result: RouterResult,
) -> bytes:
    """
    v0.1 SVG emit: structural-only.

    Day-one fidelity is "every component is named, every wire is drawn,
    every pin has a data-ref attribute" so the structural-equality test
    in CI (§12 step 6) has something to compare. Rich component glyphs
    (LED triangles, capacitor plates, resistor zigzags) land with the
    Schemdraw integration follow-up; today we draw each placement as a
    labelled rectangle and each routed segment as a polyline.
    """
    grid_unit = 32  # SVG pixels per grid cell
    margin = 64

    # Compute viewBox bounds from placements + routed segments.
    xs: list[int] = []
    ys: list[int] = []
    for p in layout.placements.values():
        origin = _resolve_origin(p, layout)
        if origin is None:
            continue
        xs.append(origin[0])
        ys.append(origin[1])
    for wire in router_result.routes:
        for seg in wire.segments:
            xs.extend([seg.x1, seg.x2])
            ys.extend([seg.y1, seg.y2])
    if not xs:
        xs, ys = [0], [0]
    x_min = min(xs) * grid_unit - margin
    y_min = min(ys) * grid_unit - margin
    x_max = max(xs) * grid_unit + margin
    y_max = max(ys) * grid_unit + margin
    width = x_max - x_min
    height = y_max - y_min

    title = _yaml_string(circuit["meta"].get("title", "untitled"))
    elements: list[str] = []
    elements.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{x_min} {y_min} {width} {height}" '
        f'width="{width}" height="{height}" '
        f'data-skill="{SKILL_VERSION}">'
    )
    elements.append(f"<title>{title}</title>")

    # Wires first, so component bodies render on top.
    elements.append('<g class="wires" stroke="black" stroke-width="2" fill="none">')
    for wire in router_result.routes:
        points = [
            (wire.segments[0].x1 * grid_unit, wire.segments[0].y1 * grid_unit),
        ]
        for seg in wire.segments:
            points.append((seg.x2 * grid_unit, seg.y2 * grid_unit))
        d = "M " + " L ".join(f"{x},{y}" for x, y in points)
        elements.append(
            f'<path d="{d}" data-net="{wire.net}" '
            f'data-from="{wire.a}" data-to="{wire.b}" />'
        )
    elements.append("</g>")

    elements.append('<g class="components">')
    for ref in sorted(layout.placements):
        p = layout.placements[ref]
        origin = _resolve_origin(p, layout)
        if origin is None:
            continue
        cx = origin[0] * grid_unit
        cy = origin[1] * grid_unit
        elements.append(
            f'<g class="component" data-ref="{ref}" data-region="{p.region}">'
            f'<rect x="{cx - grid_unit // 2}" y="{cy - grid_unit // 2}" '
            f'width="{grid_unit}" height="{grid_unit}" '
            f'fill="white" stroke="black" stroke-width="2" />'
            f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" '
            f'font-family="DejaVu Sans" font-size="12">{ref}</text>'
            f"</g>"
        )
    elements.append("</g>")
    elements.append("</svg>")
    return ("\n".join(elements) + "\n").encode("utf-8")


def _resolve_origin(p, layout: LayoutResult) -> tuple[int, int] | None:
    """Mirror the router's coordinate mapping (kept duplicated to avoid a circular import)."""
    if p.attached_to is not None:
        anchor = layout.placements.get(p.attached_to)
        if anchor is None:
            return None
        anchor_origin = _resolve_origin(anchor, layout)
        if anchor_origin is None:
            return None
        ax, ay = anchor_origin
        if anchor.region == "left-column":
            return (ax + 1, ay)
        if anchor.region == "right-column":
            return (ax - 1, ay)
        if anchor.region == "top-row":
            return (ax, ay + 1)
        if anchor.region == "bottom-row":
            return (ax, ay - 1)
        return (ax, ay)
    if p.region == "mcu-center":
        return (0, 0)
    if p.region == "left-column":
        return (-6, (p.row or 0) * 2)
    if p.region == "right-column":
        return (6, (p.row or 0) * 2)
    if p.region == "top-row":
        return ((p.col or 0) * 2, -4)
    if p.region == "bottom-row":
        return ((p.col or 0) * 2, 4)
    return None


# ── meta.yml emission ────────────────────────────────────────────────────


def _dispatch_ai_placer(
    *,
    circuit: dict[str, Any],
    layout: LayoutResult,
    graph: NetGraph,
    profile_index: dict[str, Any],
    ai_client: LLMClient | None,
) -> ConvergenceResult:
    """Invoke the Phase 2b AI placer on the kernel's `unplaced` queue.

    Builds the §7.1 input, wires the rubric-check callback (router +
    rubric re-run on the proposed placements), and returns the
    `ConvergenceResult` for the caller to act on. The caller decides
    whether to merge the proposals or abort.
    """
    if ai_client is None:
        from circuitsmith.layout.ai_placer import AnthropicClient
        ai_client = AnthropicClient()

    ambiguity_queue = [
        AmbiguityEntry(ref=ref, reason=reason, detail=detail)
        for ref, reason, detail in layout.unplaced
    ]
    capacity_map = {
        "left-column": 12,
        "right-column": 12,
        "top-row": 16,
        "bottom-row": 16,
    }

    def rubric_check(proposals) -> tuple[bool, str]:
        # Merge the AI's proposals into a temporary LayoutResult and run
        # router + rubric. The kernel's placements stay frozen.
        merged = LayoutResult(
            placements=dict(layout.placements),
            capacity_overrides=dict(layout.capacity_overrides),
        )
        for ref, ai_placement in proposals.items():
            merged.placements[ref] = Placement(
                ref=ref,
                region=ai_placement.region,
                row=ai_placement.row,
                col=ai_placement.col,
                position=ai_placement.position,
                step=ai_placement.step,
                attached_to=ai_placement.attached_to,
                attach_step=ai_placement.attach_step,
                label=ai_placement.label,
                topology_fingerprint="sha1:ai-trial",
            )
        try:
            trial_router = route(layout=merged, graph=graph, profiles=profile_index)
            trial_rubric = evaluate(layout=merged, router_result=trial_router)
        except Exception as exc:
            return False, f"pipeline failure: {exc}"
        if trial_rubric.passed:
            return True, ""
        first = trial_rubric.failures[0]
        return False, f"{first.check}: {first.message}"

    return converge(
        circuit=circuit,
        frozen_layout=layout,
        ambiguity_queue=ambiguity_queue,
        capacity_map=capacity_map,
        client=ai_client,
        rubric_check=rubric_check,
    )


def _emit_meta_yaml(
    *,
    circuit_path: Path,
    layout_path: Path,
    circuit: dict[str, Any],
    layout: LayoutResult,
    rubric: RubricResult,
    router_result: RouterResult,
    escalations: list[dict[str, str]],
    state: str = "complete",
    ai_invocations: list[dict[str, Any]] | None = None,
) -> str:
    """Stable YAML sidecar; per-key ordering follows §11 example. `escalations` is
    always written (TASK-057) — empty list on clean runs, never absent."""
    lines = ["schema: circuit-meta/v1", "sources:"]
    lines.append(f"  circuit: {circuit_path.as_posix()}")
    lines.append(f"  layout:  {layout_path.as_posix()}")
    lines.append("layout:")
    lines.append(f"  state: {state}")
    lines.append(f"  placed: {len(layout.placements)}")
    lines.append(f"  total:  {len(circuit['components'])}")
    lines.append("rubric:")
    for key in sorted(rubric.metrics):
        value = rubric.metrics[key]
        if isinstance(value, bool):
            lines.append(f"  {key}: {str(value).lower()}")
        elif isinstance(value, float):
            lines.append(f"  {key}: {value:.4g}")
        else:
            lines.append(f"  {key}: {value}")
    lines.extend(_provenance_lines(escalations, ai_invocations or []))
    return "\n".join(lines) + "\n"


def _emit_meta_yaml_incomplete(
    *,
    circuit_path: Path,
    layout_path: Path,
    circuit: dict[str, Any],
    escalations: list[dict[str, str]],
    placed: int,
    ai_invocations: list[dict[str, Any]] | None = None,
) -> str:
    """meta.yml for kernel-escalation runs that never produced a placement."""
    lines = [
        "schema: circuit-meta/v1",
        "sources:",
        f"  circuit: {circuit_path.as_posix()}",
        f"  layout:  {layout_path.as_posix()}",
        "layout:",
        "  state: incomplete",
        f"  placed: {placed}",
        f"  total:  {len(circuit['components'])}",
        "rubric: {}",
    ]
    lines.extend(_provenance_lines(escalations, ai_invocations or []))
    return "\n".join(lines) + "\n"


def _provenance_lines(
    escalations: list[dict[str, str]],
    ai_invocations: list[dict[str, Any]],
) -> list[str]:
    ai_invoked = bool(ai_invocations)
    cumulative_iterations = sum(int(inv.get("iterations", 0)) for inv in ai_invocations)
    lines = [
        "provenance:",
        "  tool:       circuit-renderer",
        f"  skill:      {SKILL_VERSION}",
        f"  ai_invoked: {'true' if ai_invoked else 'false'}",
        f"  iterations: {cumulative_iterations}",
    ]
    if ai_invocations:
        lines.append("  ai_invocations:")
        for inv in ai_invocations:
            inline = ", ".join(f"{k}: {_yaml_inline(v)}" for k, v in inv.items())
            lines.append(f"    - {{ {inline} }}")
    if escalations:
        lines.append("  escalations:")
        for entry in escalations:
            inline = ", ".join(f"{k}: {_yaml_inline(v)}" for k, v in entry.items())
            lines.append(f"    - {{ {inline} }}")
    else:
        lines.append("  escalations: []")
    return lines


def _yaml_inline(value: Any) -> str:
    """Inline-format a value for the escalations flow-style map.

    Lists render in YAML flow form (`[a, b]`); scalars render verbatim,
    quoted only when they contain YAML-special characters. The function
    is intentionally tiny — the rendering surface here is just the
    `ai_invocations` / `escalations` entries the renderer emits.
    """
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_yaml_inline(item) for item in value) + "]"
    s = str(value)
    if any(ch in s for ch in (":", "{", "}", "[", "]", ",", "#")) or s.strip() != s:
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return s


# ── YAML loader (ruamel pinned per yaml-format §Cross-cutting #1) ────────


def _load_yaml(path: Path) -> Any:
    from ruamel.yaml import YAML
    yaml = YAML(typ="safe")
    with open(path) as fh:
        return yaml.load(fh)


def _yaml_string(value: str) -> str:
    """Escape a string for inclusion in SVG text content."""
    return (
        value.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
    )


# ── CLI ─────────────────────────────────────────────────────────────────


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="circuit-skill renderer (v0.1)")
    parser.add_argument("--circuit", type=Path, required=True, help="input .circuit.yml")
    parser.add_argument("--layout",  type=Path, default=None, help="input .layout.yml (optional)")
    parser.add_argument("--out",     type=Path, required=True, help="output .svg path")
    parser.add_argument("--out-layout", type=Path, default=None, help="output .layout.yml (default: input or <out>.layout.yml)")
    parser.add_argument("--out-meta",   type=Path, default=None, help="output .meta.yml (default: sibling of <out>)")
    ai_group = parser.add_mutually_exclusive_group()
    ai_group.add_argument(
        "--no-ai",
        dest="use_ai_placer",
        action="store_false",
        help="kernel-only path; a `no-canonical-rule` escalation fails loud (default for CI per ADR-0002)",
    )
    ai_group.add_argument(
        "--ai",
        dest="use_ai_placer",
        action="store_true",
        help="invoke the Phase 2b AI placer on kernel escalations (requires ANTHROPIC_API_KEY)",
    )
    parser.set_defaults(use_ai_placer=False)
    args = parser.parse_args(argv)
    try:
        result = render(
            circuit_path=args.circuit,
            layout_path=args.layout,
            out_svg=args.out,
            out_layout=args.out_layout,
            out_meta=args.out_meta,
            use_ai_placer=args.use_ai_placer,
        )
    except RenderError as exc:
        sys.stderr.write(f"renderer aborted at {exc.stage}: {exc.summary}\n")
        for f in exc.findings:
            sys.stderr.write(f"  - {f}\n")
        return 2
    sys.stderr.write(
        f"renderer ok: svg={result.svg_path} "
        f"layout={result.layout_path} meta={result.meta_path}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))


__all__ = ["RenderError", "RenderResult", "render"]
