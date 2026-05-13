"""circuitsmith — declarative schematic generation, ERC, BOM, and netlist export.

Top-level public API surfaces are imported from the subpackages:

    from circuitsmith.netgraph import NetGraph
    from circuitsmith.schema import validate
    from circuitsmith.layout import place
    from circuitsmith.renderer import render

See the package README for the architecture overview.
"""
from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
