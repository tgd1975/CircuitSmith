"""
Structural test for committed KiCad netlists — TASK-049.

Parses every `docs/builders/wiring/<target>/main-circuit.net` with a
hand-rolled S-expression parser (`tests/_sexp.py`) and asserts five
structural properties:

1. Top form is `(export ...)` with `version "E"` and a `(source ...)`
   field naming the source `.circuit.yml`.
2. Every `(comp ...)` block has `ref`, `value`, `footprint` children.
   (`tstamp` is deferred — the dossier's v0.1 format target is the
   KiCad 7.x intermediate netlist without per-component timestamps.
   When `IDEA-011` lands and the project ships a real KiCad library,
   the date-stamped format takes over and `tstamp` checks land then.)
3. Every `(net ...)` block has a unique `code` integer and a unique
   `name` string.
4. The set of `(comp ref ...)` references equals the set of components
   in the source `.circuit.yml`'s `components:` block.
5. Round-trip: re-serialise and re-parse — the second parse equals the
   first by structural equality.

The mutation tests under `tests/fixtures/malformed-netlists/` feed
deliberately-broken netlists into the same predicates and confirm
each one fails for the expected reason.

This is the regression guard TASK-034 (manual KiCad GUI spot-check)
cannot be — KiCad imports do not run in CI, but this parser-level
check does.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from ruamel.yaml import YAML

from tests._sexp import parse, serialise

REPO_ROOT = Path(__file__).resolve().parent.parent
WIRING_DIR = REPO_ROOT / "docs" / "builders" / "wiring"
DATA_DIR = REPO_ROOT / "data"
MALFORMED_DIR = Path(__file__).resolve().parent / "fixtures" / "malformed-netlists"


def _net_files() -> list[Path]:
    """Auto-discover every committed netlist for the parametrised tests."""
    return sorted(WIRING_DIR.glob("*/main-circuit.net"))


def _target_from_path(net_path: Path) -> str:
    """`docs/builders/wiring/esp32/main-circuit.net` → `esp32`."""
    return net_path.parent.name


# ── Structural predicates (reused by mutation tests) ─────────────────────


def _check_top_form(tree) -> None:
    assert isinstance(tree, list), "top form must be an S-expression list"
    assert tree[0] == "export", f"top form must be `export`, got {tree[0]!r}"
    # First child after `export` is `(version "E")`.
    version_block = next(
        c for c in tree[1:] if isinstance(c, list) and c[0] == "version"
    )
    assert version_block[1] == "E", f"version must be `E`, got {version_block[1]!r}"
    # `(design (source "...") ...)` must exist with a non-empty source.
    design = next(c for c in tree[1:] if isinstance(c, list) and c[0] == "design")
    source = next(c for c in design[1:] if isinstance(c, list) and c[0] == "source")
    assert source[1], "design.source must be non-empty"


def _check_components(tree) -> list[str]:
    """Return the list of `ref` strings; assert per-comp required children."""
    comps_block = next(c for c in tree[1:] if isinstance(c, list) and c[0] == "components")
    refs: list[str] = []
    for comp in comps_block[1:]:
        assert isinstance(comp, list) and comp[0] == "comp", f"unexpected child in components: {comp!r}"
        children = {c[0]: c for c in comp[1:] if isinstance(c, list)}
        for required in ("ref", "value", "footprint"):
            assert required in children, f"comp is missing required child {required!r}: {comp!r}"
        refs.append(children["ref"][1])
    return refs


def _check_nets(tree) -> None:
    nets_block = next(c for c in tree[1:] if isinstance(c, list) and c[0] == "nets")
    codes: list[int] = []
    names: list[str] = []
    for net in nets_block[1:]:
        assert isinstance(net, list) and net[0] == "net", f"unexpected child in nets: {net!r}"
        code_block = next(c for c in net[1:] if isinstance(c, list) and c[0] == "code")
        name_block = next(c for c in net[1:] if isinstance(c, list) and c[0] == "name")
        code = int(code_block[1])
        name = name_block[1]
        codes.append(code)
        names.append(name)
    assert len(codes) == len(set(codes)), f"net codes are not unique: {codes}"
    assert len(names) == len(set(names)), f"net names are not unique: {names}"


def _components_from_source(target: str) -> set[str]:
    yaml = YAML(typ="safe")
    circuit = yaml.load((DATA_DIR / f"{target}.circuit.yml").read_text())
    return set(circuit["components"].keys())


# ── Parametrised structural tests ────────────────────────────────────────


@pytest.mark.parametrize("net_path", _net_files(), ids=_target_from_path)
def test_top_form_and_version(net_path: Path) -> None:
    tree = parse(net_path.read_text(encoding="utf-8"))
    _check_top_form(tree)


@pytest.mark.parametrize("net_path", _net_files(), ids=_target_from_path)
def test_every_component_has_required_children(net_path: Path) -> None:
    tree = parse(net_path.read_text(encoding="utf-8"))
    _check_components(tree)


@pytest.mark.parametrize("net_path", _net_files(), ids=_target_from_path)
def test_net_codes_and_names_are_unique(net_path: Path) -> None:
    tree = parse(net_path.read_text(encoding="utf-8"))
    _check_nets(tree)


@pytest.mark.parametrize("net_path", _net_files(), ids=_target_from_path)
def test_comp_refs_match_source_components(net_path: Path) -> None:
    tree = parse(net_path.read_text(encoding="utf-8"))
    refs_in_net = set(_check_components(tree))
    target = _target_from_path(net_path)
    refs_in_source = _components_from_source(target)
    assert refs_in_net == refs_in_source, (
        f"{target}: netlist refs differ from .circuit.yml refs. "
        f"extra={refs_in_net - refs_in_source} missing={refs_in_source - refs_in_net}"
    )


@pytest.mark.parametrize("net_path", _net_files(), ids=_target_from_path)
def test_round_trip_serialise_parse(net_path: Path) -> None:
    original_tree = parse(net_path.read_text(encoding="utf-8"))
    reserialised = serialise(original_tree)
    reparsed_tree = parse(reserialised)
    assert reparsed_tree == original_tree, "round-trip parse/serialise mismatch"


# ── Mutation tests ───────────────────────────────────────────────────────


def test_mutation_duplicate_net_code_is_caught() -> None:
    """Net codes must be unique — feed a netlist with a collision."""
    tree = parse((MALFORMED_DIR / "duplicate-net-code.net").read_text(encoding="utf-8"))
    with pytest.raises(AssertionError, match="net codes are not unique"):
        _check_nets(tree)


def test_mutation_missing_comp_value_is_caught() -> None:
    """A (comp ...) block missing `(value ...)` must fail _check_components."""
    tree = parse((MALFORMED_DIR / "missing-value.net").read_text(encoding="utf-8"))
    with pytest.raises(AssertionError, match="missing required child 'value'"):
        _check_components(tree)


def test_mutation_extra_comp_ref_breaks_source_parity() -> None:
    """The ref-set parity check must catch a netlist containing an undeclared ref."""
    tree = parse((MALFORMED_DIR / "extra-comp-ref.net").read_text(encoding="utf-8"))
    refs_in_net = set(_check_components(tree))
    # The fixture is a stripped-down ESP32 derivative with one extra ref.
    refs_in_source = _components_from_source("esp32")
    assert refs_in_net != refs_in_source
