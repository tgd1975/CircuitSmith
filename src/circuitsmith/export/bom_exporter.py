"""
BOM exporter — Markdown table and CSV from a parsed .circuit.yml.

The BOM exporter is a counting problem, not a topology problem. It
iterates the `components` section exactly once, groups instances by
`(component.type, variant_key)`, and emits two artefacts side-by-side:

  - `bom.md`  — Markdown table embedded in the build guide. One row per
                group; reference designators run-length-encoded.
  - `bom.csv` — Un-grouped, one row per reference designator. Columns
                named to satisfy KiCad's BOM importer.

ADR-0004 / dossier §"BOM Exporter" forbids this module from consuming
`NetGraph`. The netlist exporter's flattening rules must not leak into
the BOM output — two 220 Ω resistors collapse to one row regardless of
the netlist topology those resistors participate in.

Variant projection is per-category: resistor on `value`, LED on `color`,
capacitor on `value` (+ `dielectric` if declared), every other category
has no variant axis. The projector lives next to the exporter rather
than on the component profile because it concerns presentation, not
electrical semantics — the "category keys layout, not semantics"
invariant from idea-001.components.md §1.

Reference: idea-001.exporters.md §"BOM Exporter".
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from typing import Any, Iterable

from circuitsmith.schema.registry import Profile


@dataclass(frozen=True)
class BOMRow:
    """One BOM group as rendered in the Markdown output."""

    refs: str           # condensed reference designators ("R1–R3, R5")
    component: str      # human label from metadata.label (or type tail)
    variant: str        # variant projection ("220 Ω", "green", "")
    qty: int


@dataclass(frozen=True)
class BOMCSVRow:
    """One per-instance row for the CSV form (KiCad importer-friendly)."""

    reference: str
    type: str
    value: str
    footprint: str
    datasheet: str
    manufacturer: str


def export(
    circuit: dict[str, Any],
    profiles: dict[str, Profile],
) -> tuple[str, str]:
    """
    Produce `(bom_markdown, bom_csv)` from a validated .circuit.yml dict
    and the resolved profile registry. Caller is responsible for
    schema-validating the circuit first.

    The Markdown form carries one row per group with run-length-encoded
    references. The CSV form is un-grouped, one row per ref, in
    `components:` declaration order — so it seeds KiCad's BOM importer
    directly.
    """
    title = str(circuit.get("meta", {}).get("title", "untitled"))
    components: dict[str, dict[str, Any]] = circuit["components"]

    rows_md = _build_markdown_rows(components, profiles)
    csv_rows = _build_csv_rows(components, profiles)

    return _render_markdown(title, rows_md), _render_csv(csv_rows)


# ── Markdown form ────────────────────────────────────────────────────────


def _build_markdown_rows(
    components: dict[str, dict[str, Any]],
    profiles: dict[str, Profile],
) -> list[BOMRow]:
    """Group instances by (type, variant_key) and render run-length refs."""
    # group_key → list of refs (in declaration order)
    groups: dict[tuple[str, str], list[str]] = {}
    # group_key → (component_label, variant_str) for rendering
    group_meta: dict[tuple[str, str], tuple[str, str]] = {}

    for ref, decl in components.items():
        type_str = decl["type"]
        profile = profiles.get(type_str)
        variant_key = _variant_key(profile, decl)
        variant_str = _variant_display(profile, decl)
        group_key = (type_str, variant_key)
        groups.setdefault(group_key, []).append(ref)
        if group_key not in group_meta:
            label = _component_label(profile, type_str)
            group_meta[group_key] = (label, variant_str)

    rows: list[BOMRow] = []
    for group_key, refs in groups.items():
        label, variant = group_meta[group_key]
        rows.append(BOMRow(
            refs=_condense_refs(refs),
            component=label,
            variant=variant,
            qty=len(refs),
        ))

    rows.sort(key=_row_sort_key)
    return rows


def _row_sort_key(row: BOMRow) -> tuple[str, int, str]:
    """Sort groups by ref-designator prefix (alpha), then by numeric suffix of first member."""
    first_ref = row.refs.split(",")[0].split("–")[0].strip()
    prefix, suffix = _split_ref(first_ref)
    return (prefix, suffix if suffix is not None else 0, row.variant)


def _render_markdown(title: str, rows: list[BOMRow]) -> str:
    lines = [
        f"# Bill of Materials — {title}",
        "",
        "| Ref | Component | Variant | Qty |",
        "|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r.refs} | {r.component} | {r.variant} | {r.qty} |")
    return "\n".join(lines) + "\n"


# ── CSV form ─────────────────────────────────────────────────────────────


def _build_csv_rows(
    components: dict[str, dict[str, Any]],
    profiles: dict[str, Profile],
) -> list[BOMCSVRow]:
    """One row per ref, in components-map declaration order."""
    out: list[BOMCSVRow] = []
    for ref, decl in components.items():
        type_str = decl["type"]
        profile = profiles.get(type_str)
        value = _variant_csv_value(profile, decl)
        metadata = (profile.metadata or {}) if profile is not None else {}
        out.append(BOMCSVRow(
            reference=ref,
            type=type_str,
            value=value,
            footprint=str(metadata.get("footprint", "")),
            datasheet=str(metadata.get("datasheet", "")),
            manufacturer=str(metadata.get("manufacturer", "")),
        ))
    return out


def _render_csv(rows: Iterable[BOMCSVRow]) -> str:
    """Emit CSV with `\\n` line endings (deterministic across platforms)."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["Reference", "Type", "Value", "Footprint", "Datasheet", "Manufacturer"])
    for r in rows:
        writer.writerow([r.reference, r.type, r.value, r.footprint, r.datasheet, r.manufacturer])
    return buf.getvalue()


# ── Variant projection ───────────────────────────────────────────────────
#
# Variant projection dispatches on `metadata.kind`, not `category`.
# `category` is a layout-engine axis (it keys the placement kernel's
# component-shape dispatch); semantic-level discrimination outside
# layout/ must read `metadata.kind` (idea-001.components.md §1 invariant,
# enforced by the catalog category-lint).


def _kind(profile: Profile | None) -> str:
    if profile is None or profile.metadata is None:
        return ""
    kind = profile.metadata.get("kind")
    return str(kind) if isinstance(kind, str) else ""


def _variant_key(profile: Profile | None, decl: dict[str, Any]) -> str:
    """
    Per-kind variant key used for grouping. Pure projection — never
    user-facing; the display form is _variant_display.
    """
    kind = _kind(profile)
    if kind == "resistor":
        return str(decl.get("value", ""))
    if kind == "capacitor":
        value = str(decl.get("value", ""))
        dielectric = str(decl.get("dielectric", ""))
        return f"{value}|{dielectric}" if dielectric else value
    if kind == "led":
        return str(decl.get("color", "default"))
    return ""


def _variant_display(profile: Profile | None, decl: dict[str, Any]) -> str:
    """Markdown-column display form of the variant axis (with units)."""
    kind = _kind(profile)
    if kind == "resistor":
        value = decl.get("value")
        return f"{value} Ω" if value is not None else ""
    if kind == "capacitor":
        value = decl.get("value")
        dielectric = decl.get("dielectric")
        parts: list[str] = []
        if value is not None:
            parts.append(f"{value} F")
        if dielectric is not None:
            parts.append(str(dielectric))
        return " ".join(parts)
    if kind == "led":
        color = decl.get("color")
        return str(color) if color is not None else ""
    return ""


def _variant_csv_value(profile: Profile | None, decl: dict[str, Any]) -> str:
    """KiCad `Value` column — bare projection (no unit suffix, no Ω)."""
    kind = _kind(profile)
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


def _component_label(profile: Profile | None, type_str: str) -> str:
    """Human label for the Markdown `Component` column."""
    if profile is not None and profile.metadata is not None:
        label = profile.metadata.get("label")
        if isinstance(label, str) and label:
            return label
    # Fall back to the type tail (e.g. `passives/led` → `led`).
    return type_str.split("/")[-1]


# ── Reference-designator run-length encoding ─────────────────────────────


_REF_SPLIT_RE = re.compile(r"^([A-Za-z_]+)(\d+)$")


def _split_ref(ref: str) -> tuple[str, int | None]:
    """Split a reference designator into `(alpha_prefix, numeric_suffix)`."""
    match = _REF_SPLIT_RE.match(ref)
    if match is None:
        return (ref, None)
    return (match.group(1), int(match.group(2)))


def _condense_refs(refs: list[str]) -> str:
    """
    Condense a list of reference designators by run-length-encoding
    consecutive numeric suffixes within the same alpha prefix.

    Operates within one group only; gaps caused by another group's
    members do not produce sub-ranges (per dossier §"Reference column").
    """
    # Group by prefix; within each prefix, sort numerically and run-length-encode.
    by_prefix: dict[str, list[tuple[int, str]]] = {}
    no_suffix: list[str] = []
    for ref in refs:
        prefix, suffix = _split_ref(ref)
        if suffix is None:
            no_suffix.append(ref)
        else:
            by_prefix.setdefault(prefix, []).append((suffix, ref))

    chunks: list[str] = []
    for prefix in sorted(by_prefix):
        entries = sorted(by_prefix[prefix], key=lambda x: x[0])
        # Run-length-encode consecutive numeric suffixes.
        run_start_idx = 0
        for i in range(1, len(entries) + 1):
            if i == len(entries) or entries[i][0] != entries[i - 1][0] + 1:
                run = entries[run_start_idx:i]
                if len(run) == 1:
                    chunks.append(run[0][1])
                elif len(run) == 2:
                    chunks.append(run[0][1])
                    chunks.append(run[1][1])
                else:
                    chunks.append(f"{run[0][1]}–{run[-1][1]}")
                run_start_idx = i

    chunks.extend(sorted(no_suffix))
    return ", ".join(chunks)


__all__ = ["BOMRow", "BOMCSVRow", "export"]
