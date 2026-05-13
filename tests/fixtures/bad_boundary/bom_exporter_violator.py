"""
Self-test fixture for ``tests/test_module_boundaries.py``.

Deliberately violates the bom_exporter ⟂ netgraph boundary rule by
importing ``circuitsmith.netgraph``. The boundary checker must trip
on this file; if it does not, the mutation guard is broken and silent
drift in the real rules is possible.

This file is never imported by production code.
"""
from __future__ import annotations

from circuitsmith.netgraph import NetGraph  # noqa: F401 — intentional violation
