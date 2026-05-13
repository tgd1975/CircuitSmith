"""
Layout engine — turns a NetGraph into a placement (and, later, an SVG).

v0.1 ships the deterministic kernel only:

  - kernel.py — canonical-slot lookup, incremental-stability diff,
    topology-fingerprint computation, layout.yml emit, and the
    `no-canonical-rule` fail-loud escalation.

The Manhattan router (TASK-010) and the structural rubric (TASK-011)
join this package as siblings. The AI placer (TASK-017, Phase 2b)
joins when its trigger fires.

References:
  - idea-001.layout-engine-concept.md §§4–8 — slots, kernel, fingerprint
  - ADR-0001 — slots-not-coordinates
"""

from .kernel import (
    EscalationError,
    LayoutResult,
    Placement,
    SlotRule,
    place,
    render_layout_yaml,
)
from .router import (
    RouterResult,
    Segment,
    WireRoute,
    route,
)
from .rubric import (
    Finding,
    RubricResult,
    evaluate,
)
from .ai_placer import (
    AIPlacement,
    AmbiguityEntry,
    AnthropicClient,
    ConvergenceResult,
    LLMClient,
    converge,
)

__all__ = [
    "AIPlacement",
    "AmbiguityEntry",
    "AnthropicClient",
    "ConvergenceResult",
    "EscalationError",
    "Finding",
    "LLMClient",
    "LayoutResult",
    "Placement",
    "RouterResult",
    "RubricResult",
    "Segment",
    "SlotRule",
    "WireRoute",
    "converge",
    "evaluate",
    "place",
    "render_layout_yaml",
    "route",
]
