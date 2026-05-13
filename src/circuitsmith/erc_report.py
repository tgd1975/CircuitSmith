"""
ERC report writer — turns a list of `erc_engine.Finding` into the
diffable Markdown artefact specified in idea-001.erc-engine.md §Output.

Pipeline position: consumes engine output; the renderer-CLI hooks
write the rendered string to the host project's chosen path (see
TASK-028). Catalog-backed enrichment (TASK-027): every non-OK finding
gets a "Why / Senior's tip / Source" block sourced from `rules.json`
(lookup by check code only — no fuzzy match, no LLM).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_cls
from typing import Any

from circuitsmith.erc_engine import CHECK_TABLE, EMPTY, Finding
from circuitsmith.knowledge import load_rules


@dataclass(frozen=True)
class _Rule:
    """A subset of the catalog row used by the report writer."""

    id: str
    rule: str
    explanation: str
    heuristic: str
    source_of_truth: str


class CatalogLookupError(KeyError):
    """A non-OK finding referenced a check code with no catalog row."""


def render_report(
    findings: list[Finding],
    *,
    title: str,
    target: str,
    today: date_cls | None = None,
    catalog: list[dict[str, Any]] | None = None,
) -> str:
    """
    Render the ERC report Markdown for a circuit. `findings` is the
    engine's output (already sorted into canonical order). `title` and
    `target` come from `meta.title` and `meta.target` of the
    `.circuit.yml`; `today` defaults to the local date.

    Raises `CatalogLookupError` if a non-OK finding has no catalog row.
    """
    if today is None:
        today = date_cls.today()
    rules_by_id = _index_catalog(catalog if catalog is not None else load_rules())

    lines: list[str] = []
    lines.append(f"# ERC Report — {title} — {today.isoformat()}")
    lines.append("")
    lines.append("| Severity | Ref | Pin | Check | Net | Message |")
    lines.append("|---|---|---|---|---|---|")
    for f in findings:
        if f.check == "S0":  # banner finding from the gate — render as table note
            continue
        emoji = _severity_emoji(f.severity)
        lines.append(
            f"| {emoji} {f.severity.upper()} | {f.ref} | {f.pin} | "
            f"{f.check} {_title(f.check)} | {f.net} | {f.message} |"
        )

    error_count = sum(1 for f in findings if f.severity == "error")
    warning_count = sum(1 for f in findings if f.severity == "warning")
    skip_banner = any(f.check == "S0" for f in findings)
    lines.append("")
    lines.append(f"{error_count} error(s), {warning_count} warning(s).")
    if skip_banner:
        lines.append("")
        lines.append("**Note.** Electrical (E-class) checks skipped — fix structural (S-class) errors first.")
    lines.append("")

    # Per-finding catalog enrichment for every non-OK finding.
    for f in findings:
        if f.severity == "ok" or f.check == "S0":
            continue
        rule = rules_by_id.get(f.check)
        if rule is None:
            raise CatalogLookupError(
                f"ERC finding {f.check} on {f.ref}.{f.pin} has no matching "
                f"catalog row in rules.json. Every shipped check must have "
                f"at least one row (ADR-0006)."
            )
        lines.append(_render_enrichment_block(f, rule))
        lines.append("")

    # Pending-promotions rationale: appended whenever E9 surfaces as
    # WARNING — the auto-promote-to-ERROR path is gated on the `diode`
    # category landing, and the report stating that protects future
    # readers from misreading the warning as a transient.
    if any(f.check == "E9" and f.severity == "warning" for f in findings):
        lines.append(_pending_promotions_block())
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _pending_promotions_block() -> str:
    return "\n".join([
        "## Pending promotions",
        "",
        "**E9 — Reverse-polarity unprotected.** Surfaces as WARNING in v0.1.",
        "The check's intended severity is ERROR (a missing protection diode on",
        "a barrel jack or USB-C power input destroys the MCU on a wiring",
        "mistake), but the `diode` component category is still on the backlog.",
        "Without a way to semantically distinguish a protection diode from any",
        "other 2-terminal passive, every USB-C / barrel-jack circuit would",
        "fail E9 by construction. E9 auto-promotes to ERROR once the `diode`",
        "category lands; see `idea-001.components.md` §Backlog.",
    ])


def _render_enrichment_block(f: Finding, rule: _Rule) -> str:
    emoji = _severity_emoji(f.severity)
    pin_loc = f.pin if f.pin != EMPTY else "—"
    ref_loc = f.ref if f.ref != EMPTY else "—"
    heading = f"## {emoji} {ref_loc}.{pin_loc} — {f.check} {_title(f.check)}"
    return "\n".join([
        heading,
        "",
        f"**Why.** {rule.explanation}",
        "",
        f"**Senior's tip.** {rule.heuristic}",
        "",
        f"**Source.** <{rule.source_of_truth}>",
    ])


def _severity_emoji(severity: str) -> str:
    return {"error": "❌", "warning": "⚠️", "ok": "✅"}.get(severity, "•")


def _title(check_code: str) -> str:
    spec = CHECK_TABLE.get(check_code)
    return spec.title if spec else check_code


def _index_catalog(catalog: list[dict[str, Any]]) -> dict[str, _Rule]:
    """Map check-id → _Rule, taking the first entry per id."""
    out: dict[str, _Rule] = {}
    for entry in catalog:
        rid = entry.get("id")
        if not isinstance(rid, str) or rid in out:
            continue
        out[rid] = _Rule(
            id=rid,
            rule=str(entry.get("rule", "")),
            explanation=str(entry.get("explanation", "")),
            heuristic=str(entry.get("heuristic", "")),
            source_of_truth=str(entry.get("source_of_truth", "")),
        )
    return out


__all__ = ["CatalogLookupError", "render_report"]
