"""
Module-boundary contract test for TASK-050 / EPIC-008.

Promotes the decoupling claims in
`docs/developers/ideas/archived/idea-001-circuit-skill.md` §Architecture
from prose to machine-checked invariants. Three forbidden edges are
asserted by AST-walking the targeted source files:

- ``circuitsmith.export.bom_exporter`` must never import anything
  named ``netgraph`` — the BOM exporter walks ``components`` directly.
- ``circuitsmith.export.netlist_exporter`` must never import any module
  under ``circuitsmith.components`` — the netlist exporter walks
  ``NetGraph`` and never reads component internals.
- ``circuitsmith.renderer`` must never import
  ``circuitsmith.layout.ai_placer`` — the renderer consumes
  pre-committed ``layout.yml`` via ``layout.py``, keeping the AI
  containment property of the architecture intact.

AST walking (rather than runtime import) avoids ordering dependencies
on the rest of the package being importable in test scope, and means
the test fails on the smallest possible drift: a single stray import
line.

A deliberately-violating fixture under ``tests/fixtures/bad_boundary/``
confirms the checker actually catches a violation (mutation test of the
rule itself).

References:
- Task spec: `docs/developers/tasks/active/task-050-boundary-import-contract-test.md`
- Architecture section: `docs/developers/ideas/archived/idea-001-circuit-skill.md`
- ADR-0012 (library-as-installable-package) — anchors the
  ``src/circuitsmith/`` source layout the rules target.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PKG_ROOT = REPO_ROOT / "src" / "circuitsmith"

DOSSIER_SECTION = (
    "docs/developers/ideas/archived/idea-001-circuit-skill.md §Architecture"
)


@dataclass(frozen=True)
class BoundaryRule:
    """A single forbidden-edge contract.

    ``source`` is the module file under test.
    ``forbidden`` is a tuple of dotted module prefixes that must not
    appear in any ``import`` / ``from ... import`` target.
    ``dossier`` is a human-readable pointer to the architecture
    section defining the rule — surfaced in the assertion message so a
    failure tells the reader *why* the edge is forbidden, not just
    that it is.
    """

    name: str
    source: Path
    forbidden: tuple[str, ...]
    dossier: str


# Source-of-truth table. Edit here if the dossier changes; the test
# itself is mechanical.
RULES: tuple[BoundaryRule, ...] = (
    BoundaryRule(
        name="bom_exporter ⟂ netgraph",
        source=PKG_ROOT / "export" / "bom_exporter.py",
        forbidden=("circuitsmith.netgraph",),
        dossier=DOSSIER_SECTION + " (BOM walks components directly)",
    ),
    BoundaryRule(
        name="netlist_exporter ⟂ components",
        source=PKG_ROOT / "export" / "netlist_exporter.py",
        forbidden=("circuitsmith.components",),
        dossier=DOSSIER_SECTION + " (netlist walks NetGraph, not component internals)",
    ),
    BoundaryRule(
        name="renderer ⟂ ai_placer",
        source=PKG_ROOT / "renderer.py",
        forbidden=("circuitsmith.layout.ai_placer",),
        dossier=DOSSIER_SECTION + " (renderer consumes committed layout.yml only)",
    ),
)


def _collect_imports(source_path: Path) -> list[str]:
    """Return every dotted module name imported by ``source_path``.

    For ``import a.b.c``, yields ``a.b.c``.
    For ``from a.b import c``, yields ``a.b`` and ``a.b.c`` (so the
    rule can match either the package or a specific submodule).
    Relative imports (``from . import x``) are normalised against the
    file's package path so the matcher works the same way as for
    absolute imports.
    """
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    imports: list[str] = []
    package_parts = _package_of(source_path) if source_path.is_relative_to(REPO_ROOT / "src") else ()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                # Relative import — anchor against the file's package.
                anchor = package_parts[: len(package_parts) - node.level + 1]
                base = ".".join(p for p in (*anchor, base) if p)
            for alias in node.names:
                if base:
                    imports.append(base)
                    imports.append(f"{base}.{alias.name}")
                else:
                    imports.append(alias.name)
    return imports


def _package_of(source_path: Path) -> tuple[str, ...]:
    """Return the dotted package path for ``source_path``.

    ``src/circuitsmith/export/bom_exporter.py`` →
    ``("circuitsmith", "export", "bom_exporter")``.
    """
    rel = source_path.relative_to(REPO_ROOT / "src").with_suffix("")
    return tuple(rel.parts)


def _check(rule: BoundaryRule) -> list[tuple[str, str]]:
    """Return the list of ``(forbidden_prefix, actual_import)`` matches.

    Empty list means the rule is satisfied. Each entry is a concrete
    violation suitable for inclusion in the assertion message.
    """
    if not rule.source.exists():
        pytest.skip(f"source not present yet: {rule.source.relative_to(REPO_ROOT)}")
    violations: list[tuple[str, str]] = []
    for imported in _collect_imports(rule.source):
        for prefix in rule.forbidden:
            if imported == prefix or imported.startswith(prefix + "."):
                violations.append((prefix, imported))
    return violations


@pytest.mark.parametrize("rule", RULES, ids=lambda r: r.name)
def test_module_boundary(rule: BoundaryRule) -> None:
    """Each named module respects the decoupling line the dossier draws."""
    violations = _check(rule)
    if violations:
        rel = rule.source.relative_to(REPO_ROOT)
        lines = [f"{rel}: forbidden import detected (rule: {rule.name})"]
        for prefix, actual in violations:
            lines.append(f"  - imports `{actual}` (forbidden prefix `{prefix}`)")
        lines.append(f"  dossier: {rule.dossier}")
        pytest.fail("\n".join(lines))


def test_checker_catches_a_real_violation() -> None:
    """Self-test: a deliberately-violating fixture must trip the checker.

    Mutation-tests the rule itself — without this, a no-op checker
    that always returns "no violations" would silently pass the happy
    paths above.
    """
    fixture = REPO_ROOT / "tests" / "fixtures" / "bad_boundary" / "bom_exporter_violator.py"
    assert fixture.exists(), f"self-test fixture missing: {fixture}"
    rule = BoundaryRule(
        name="self-test fixture must violate",
        source=fixture,
        forbidden=("circuitsmith.netgraph",),
        dossier="self-test",
    )
    violations = _check(rule)
    assert violations, (
        "self-test fixture did not trip the checker — the mutation guard "
        "is broken; future drift in the production rules may pass silently."
    )
