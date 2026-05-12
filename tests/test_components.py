"""
Connector-factory edge cases — gaps surfaced by EPIC-001 coverage review.

The `make_header(n)` and `make_screw_terminal(n)` factories in
`components/connectors.py` reject `n < 1`; the original test sweep
exercised the happy path (sizes 2 / 3 / 4 / 6 / 8) but not the
guard. Without this test the ValueError branches sat at 0% and a
future refactor could silently drop them.
"""
from __future__ import annotations

import pytest

from circuit.components.connectors import make_header, make_screw_terminal


@pytest.mark.parametrize("factory", [make_header, make_screw_terminal])
@pytest.mark.parametrize("n", [0, -1, -7])
def test_factories_reject_non_positive_n(factory, n):
    with pytest.raises(ValueError, match="n >= 1"):
        factory(n)


def test_make_header_produces_n_pins():
    profile = make_header(4)
    assert profile["category"] == "header"
    assert set(profile["pins"]) == {"1", "2", "3", "4"}
    assert all(p["side"] == "bottom" for p in profile["pins"].values())


def test_make_screw_terminal_produces_n_pins():
    profile = make_screw_terminal(3)
    assert profile["category"] == "header"
    assert set(profile["pins"]) == {"1", "2", "3"}
