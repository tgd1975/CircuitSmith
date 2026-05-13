"""
Netlist exporter — flatten `NetGraph` to a KiCad 7.x intermediate netlist.

The exporter is a thin projection: all flattening (`pins` membership,
`path` segmentation, terminal net-name merging, bus collapse) is
already done inside `NetGraph` (ADR-0003). This module walks
`NetGraph.nets` once in insertion order and emits one `(net ...)`
block per entry — it never re-parses YAML or re-implements flattening.

Output format is KiCad 7.x intermediate (`version "E"`) — the
S-expression eeschema writes for the legacy import flow. KiCad 7 and
8 both consume it via Tools → Update PCB from Netlist. The newer
`.kicad_netlist` and date-stamped formats are out of scope for v0.1;
they require shipping a KiCad project + library that this repo does
not yet have.

ADR-0004 forbids this module from consuming the `components` map for
BOM purposes; the BOM exporter has its own path. The `(components ...)`
block here uses each profile's `metadata` to emit value / footprint /
datasheet — the same projection the BOM CSV uses, so a 220 Ω resistor's
KiCad `(value "220")` and BOM CSV `Value=220` match row-for-row.

Reference: idea-001.exporters.md §"Netlist Exporter".
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Iterable

from circuitsmith.netgraph import NetGraph, PinRef
from circuitsmith.schema.registry import Profile

SKILL_VERSION = "circuit-skill 0.4"


def export(
    circuit: dict[str, Any],
    graph: NetGraph,
    profiles: dict[str, Profile],
    source_path: Path,
) -> str:
    """
    Render the KiCad `.net` text for one circuit.

    The caller passes the validated circuit dict, the constructed
    `NetGraph`, the profile registry, and the source `.circuit.yml`
    path. The path is used for `(source ...)` (basename) and the
    `(date ...)` field (git last-modified date — see `_source_date`).
    """
    lines: list[str] = []
    lines.append('(export (version "E")')
    lines.extend(_design_block(source_path, circuit))
    lines.extend(_components_block(circuit, profiles))
    lines.extend(_nets_block(graph))
    lines.append(")")
    return "\n".join(lines) + "\n"


# ── (design ...) ─────────────────────────────────────────────────────────


def _design_block(source_path: Path, circuit: dict[str, Any]) -> list[str]:
    date_str = _source_date(source_path)
    return [
        "  (design",
        f'    (source "{source_path.name}")',
        f'    (date "{date_str}")',
        f'    (tool "{SKILL_VERSION}"))',
    ]


def _source_date(source_path: Path) -> str:
    """
    Return the source .circuit.yml's last-modified date as ISO-8601 YYYY-MM-DD.

    Uses `git log -1 --format=%cI -- <path>` so the date is reproducible
    across machines (wall-clock would change every CI run and trip the
    staleness guard daily). Falls back to filesystem mtime when git is
    unavailable or the file has no history — that fallback path only
    fires during local dev before the first commit.
    """
    try:
        cwd = source_path.parent if source_path.parent.exists() else Path.cwd()
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(source_path)],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            # %cI is ISO-8601 with timezone; take the date prefix.
            return result.stdout.strip().split("T", 1)[0]
    except (OSError, FileNotFoundError):
        pass
    # Fallback: filesystem mtime when the source exists but is untracked
    # or git is unavailable. The path-does-not-exist case (synthetic test
    # fixtures pointing at non-existent files) falls through to the
    # sentinel below.
    import datetime
    try:
        stat = source_path.stat()
        return datetime.date.fromtimestamp(stat.st_mtime).isoformat()
    except (OSError, FileNotFoundError):
        return "1970-01-01"


# ── (components ...) ─────────────────────────────────────────────────────


def _components_block(
    circuit: dict[str, Any],
    profiles: dict[str, Profile],
) -> list[str]:
    lines = ["  (components"]
    components: dict[str, dict[str, Any]] = circuit["components"]
    items = list(components.items())
    last_index = len(items) - 1
    for index, (ref, decl) in enumerate(items):
        is_last = index == last_index
        lines.append(_component_line(ref, decl, profiles, is_last))
    return lines


def _component_line(
    ref: str,
    decl: dict[str, Any],
    profiles: dict[str, Profile],
    is_last: bool,
) -> str:
    """Render one `(comp ...)` entry. Last entry closes the parent `(components ...)`."""
    type_str = decl["type"]
    profile = profiles.get(type_str)
    metadata = (profile.metadata or {}) if profile is not None else {}

    value = _component_value(profile, decl)
    footprint = str(metadata.get("footprint", ""))
    datasheet = metadata.get("datasheet")

    parts = [
        f"(ref {ref})",
        f'(value "{_escape(value)}")',
        f'(footprint "{_escape(footprint)}")',
    ]
    if isinstance(datasheet, str) and datasheet:
        parts.append(f'(datasheet "{_escape(datasheet)}")')

    body = f"    (comp {' '.join(parts)})"
    if is_last:
        return body + ")"
    return body


def _component_value(profile: Profile | None, decl: dict[str, Any]) -> str:
    """
    KiCad `(value ...)` projection — must match the BOM CSV `Value` column
    row-for-row (idea-001.exporters.md §"KiCad format target").

    Dispatches on `metadata.kind` rather than `category` per the
    catalog-lint invariant; the projection table mirrors
    `bom_exporter._variant_csv_value`.
    """
    if profile is None or profile.metadata is None:
        return ""
    kind = profile.metadata.get("kind")
    if kind == "resistor":
        value = decl.get("value")
        return "" if value is None else str(value)
    if kind == "capacitor":
        value = decl.get("value")
        dielectric = decl.get("dielectric")
        if value is None and dielectric is None:
            return ""
        if dielectric is None:
            return str(value)
        if value is None:
            return str(dielectric)
        return f"{value} {dielectric}"
    if kind == "led":
        color = decl.get("color")
        return "" if color is None else str(color)
    return ""


# ── (nets ...) ───────────────────────────────────────────────────────────


def _nets_block(graph: NetGraph) -> list[str]:
    lines = ["  (nets"]
    entries = list(graph.nets.items())
    last_index = len(entries) - 1
    for index, (name, members) in enumerate(entries):
        is_last = index == last_index
        lines.extend(_net_lines(index + 1, name, members, is_last))
    return lines


def _net_lines(
    code: int,
    name: str,
    members: Iterable[PinRef],
    is_last: bool,
) -> list[str]:
    """
    Render one `(net (code N) (name NAME) (node ...) ...)` block.

    Member emission order is the order `NetGraph.nets[name]` exposes,
    which is canonical per net form (dossier §"Member emission order").
    """
    lines = [f'    (net (code {code}) (name "{_escape(name)}")']
    members_list = list(members)
    if not members_list:
        # Net with no members — emit an empty block; KiCad will skip it
        # on import but the structural shape is preserved.
        if is_last:
            lines[0] = lines[0] + "))"
        else:
            lines[0] = lines[0] + ")"
        return lines
    last_member = len(members_list) - 1
    for member_index, pin in enumerate(members_list):
        node = f'      (node (ref {pin.ref}) (pin {pin.pin}))'
        if member_index == last_member:
            # Close the (net ...) on the last member; also close the
            # parent (nets ...) on the last net.
            tail = "))" if is_last else ")"
            node = node + tail
        lines.append(node)
    return lines


# ── helpers ──────────────────────────────────────────────────────────────


def _escape(text: str) -> str:
    """Escape a string for inclusion inside a KiCad S-expression literal."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


__all__ = ["export"]
