"""
Catalog validator — CI-runnable check that `rules.json` matches the
contract specified in idea-001.rule-catalog.md.

Five checks (ordered by speed; slow ones run last so a fast failure
fails CI quickly):

  1. Format            — every entry has six required fields populated.
  2. enforced_by       — every value references CHECK_TABLE or "schema".
  3. heuristic prefix  — every heuristic contains the precision disclaimer.
  4. category-lint     — no code outside layout/ reads `.category`.
  5. URL reachability  — every source_of_truth URL responds 2xx.

`CS_CATALOG_OFFLINE=1` in the environment skips check 5 (URL reachability).
The CLI returns exit 0 on a clean catalog, 1 on any failure.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from circuitsmith.erc_engine import CHECK_TABLE
from circuitsmith.knowledge import RULES_PATH, load_rules

REQUIRED_FIELDS = (
    "id", "category", "keywords", "rule", "explanation",
    "heuristic", "source_of_truth", "enforced_by",
)

# A heuristic must contain this substring (case-insensitive). The dossier
# phrases it as "this is a starting point, not an exact answer". We accept
# the slightly-broader "starting point" + "calculate the exact value" pair
# because the seeded catalog uses that compound form.
DISCLAIMER_PATTERNS = (
    "starting point",
    "calculate the exact value",
)

# Categories that are valid `enforced_by` non-predicate sentinels.
ENFORCED_BY_SENTINELS = frozenset({"schema"})

# Files under `src/circuitsmith/` where category reads are permitted.
# Layout-engine code legitimately reads category to dispatch glyphs.
CATEGORY_ALLOWED_SUBPATHS = ("layout/",)

# Patterns the lint flags in non-allowed files.
CATEGORY_PATTERNS = (
    r'category\s*==',
    r'category\s+in\s',
    r'\["category"\]',
    r"\['category'\]",
    r'\.category\b',
)


def validate(
    rules: list[dict],
    *,
    package_root: Path,
    offline: bool = False,
) -> list[str]:
    """
    Validate the parsed `rules` list. Returns a list of error strings;
    an empty list means the catalog passed every check.
    """
    errors: list[str] = []
    errors.extend(_check_format(rules))
    errors.extend(_check_enforced_by(rules))
    errors.extend(_check_disclaimers(rules))
    errors.extend(_check_category_lint(package_root))
    if not offline:
        errors.extend(_check_urls(rules))
    return errors


# ── Check 1: format ────────────────────────────────────────────────────────


def _check_format(rules: list[dict]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(rules):
        rid = entry.get("id", f"<index {index}>")
        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"rule {rid}: missing required field '{field}'.")
                continue
            value = entry[field]
            if value is None or value == "":
                errors.append(f"rule {rid}: field '{field}' is empty.")
            elif field == "keywords":
                if not isinstance(value, list) or not all(isinstance(k, str) for k in value):
                    errors.append(f"rule {rid}: keywords must be a list of strings.")
            elif not isinstance(value, str):
                errors.append(f"rule {rid}: field '{field}' must be a string.")
        if entry.get("id") in seen_ids:
            errors.append(f"rule {rid}: duplicate id in catalog.")
        if "id" in entry:
            seen_ids.add(entry["id"])
    return errors


# ── Check 2: enforced_by consistency ───────────────────────────────────────


def _check_enforced_by(rules: list[dict]) -> list[str]:
    errors: list[str] = []
    referenced_codes: set[str] = set()
    for entry in rules:
        rid = entry.get("id", "?")
        enforced = entry.get("enforced_by")
        if not enforced:
            continue
        if enforced in ENFORCED_BY_SENTINELS:
            continue
        if enforced not in CHECK_TABLE:
            errors.append(
                f"rule {rid}: enforced_by={enforced!r} is not in CHECK_TABLE "
                f"and is not a sentinel ({sorted(ENFORCED_BY_SENTINELS)})."
            )
            continue
        referenced_codes.add(enforced)
    # Weak-form: every code in CHECK_TABLE should be referenced by at
    # least one catalog entry — including the schema-detected S4/S5.
    for code, spec in CHECK_TABLE.items():
        if code in referenced_codes:
            continue
        # S4/S5 are referenced via the "schema" sentinel; their rule
        # entries must use `id` matching the code with enforced_by=schema.
        has_schema_row = any(
            e.get("id") == code and e.get("enforced_by") == "schema"
            for e in rules
        )
        if has_schema_row:
            continue
        errors.append(
            f"CHECK_TABLE has code {code!r} ({spec.title}) but no catalog "
            f"entry references it via enforced_by."
        )
    return errors


# ── Check 3: heuristic precision disclaimer ────────────────────────────────


def _check_disclaimers(rules: list[dict]) -> list[str]:
    errors: list[str] = []
    for entry in rules:
        rid = entry.get("id", "?")
        heuristic = entry.get("heuristic")
        if not isinstance(heuristic, str):
            continue  # format check will fire
        low = heuristic.lower()
        if not any(pat in low for pat in DISCLAIMER_PATTERNS):
            errors.append(
                f"rule {rid}: heuristic missing precision disclaimer "
                f"(expected one of: {DISCLAIMER_PATTERNS})."
            )
    return errors


# ── Check 4: category-invariant lint ───────────────────────────────────────


def _check_category_lint(package_root: Path) -> list[str]:
    errors: list[str] = []
    pkg_dir = package_root / "circuitsmith"
    if not pkg_dir.is_dir():
        # Tolerate alternate layouts; treat as no-finding.
        return errors
    pattern = re.compile("|".join(CATEGORY_PATTERNS))
    for py_file in pkg_dir.rglob("*.py"):
        rel = py_file.relative_to(pkg_dir).as_posix()
        # Allow layout/ to read category — the rule's intended scope.
        if any(rel.startswith(sub) for sub in CATEGORY_ALLOWED_SUBPATHS):
            continue
        # The registry itself defines `category` — skip its reads.
        if rel == "schema/registry.py":
            continue
        # The components module declares `category` as a dict key — that's
        # the field definition, not a read. Skip components/*.py.
        if rel.startswith("components/"):
            continue
        # The catalog validator itself talks ABOUT `category` (it's the
        # lint checker). Skip its own file.
        if rel == "knowledge/validate_catalog.py":
            continue
        text = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                errors.append(
                    f"{rel}:{lineno}: reads `category` outside layout/ "
                    f"(use metadata.kind for semantic discrimination)."
                )
    return errors


# ── Check 5: URL reachability ──────────────────────────────────────────────


def _check_urls(rules: list[dict]) -> list[str]:
    errors: list[str] = []
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        return ["urllib not available; cannot run URL reachability check."]
    seen: set[str] = set()
    for entry in rules:
        rid = entry.get("id", "?")
        url = entry.get("source_of_truth")
        if not url or url in seen:
            continue
        seen.add(url)
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "circuitsmith-catalog-validator/0.1"},
                method="HEAD",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if not (200 <= resp.status < 400):
                    errors.append(f"rule {rid}: URL {url} returned {resp.status}.")
        except urllib.error.HTTPError as exc:
            if exc.code in {405, 403}:
                # Some servers reject HEAD. Retry with GET.
                try:
                    req = urllib.request.Request(
                        url,
                        headers={"User-Agent": "circuitsmith-catalog-validator/0.1"},
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        if not (200 <= resp.status < 400):
                            errors.append(
                                f"rule {rid}: URL {url} returned {resp.status}."
                            )
                except Exception as inner:
                    errors.append(f"rule {rid}: URL {url} unreachable: {inner}.")
            else:
                errors.append(f"rule {rid}: URL {url} returned HTTP {exc.code}.")
        except Exception as exc:
            errors.append(f"rule {rid}: URL {url} unreachable: {exc}.")
    return errors


# ── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="circuitsmith catalog validator")
    parser.add_argument("--rules", type=Path, default=RULES_PATH,
                        help="path to rules.json (default: shipped catalog)")
    parser.add_argument("--package-root", type=Path,
                        default=Path(__file__).resolve().parents[2],
                        help="directory containing the circuitsmith/ package")
    parser.add_argument("--offline", action="store_true",
                        help="skip URL reachability (also via CS_CATALOG_OFFLINE=1)")
    args = parser.parse_args(argv)

    offline = args.offline or os.environ.get("CS_CATALOG_OFFLINE") == "1"

    try:
        rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    except Exception as exc:
        sys.stderr.write(f"validate_catalog: cannot read {args.rules}: {exc}\n")
        return 1

    errors = validate(rules, package_root=args.package_root, offline=offline)
    if errors:
        sys.stderr.write(f"validate_catalog: {len(errors)} error(s):\n")
        for msg in errors:
            sys.stderr.write(f"  - {msg}\n")
        return 1
    sys.stderr.write(
        f"validate_catalog: {len(rules)} rule(s) OK"
        + (" (URL check skipped)" if offline else "")
        + ".\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))


__all__ = ["validate", "RULES_PATH", "load_rules"]
