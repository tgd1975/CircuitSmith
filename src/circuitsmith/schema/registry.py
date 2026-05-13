"""
Component-profile registry — derives the set of valid `type:` strings and
per-profile pin sets from `circuitsmith/components/*.py`.

Profile detection rule: any top-level module attribute whose value is a
dict containing the three keys `category`, `metadata`, `pins` is treated
as a profile. Helper functions (`make_header`, …) are ignored; their
materialised products (`PIN_HEADER_2`, …) are picked up like hand-written
profiles. The dossier in `idea-001.components.md` §"Schema registration"
defines the contract.

Type string convention: `{file_stem}/{dict_name.lower()}`. So
`components/mcus.py:esp32` → `"mcu/esp32"` … wait, no — the dossier (§4)
says `components/mcus.py → type: "mcu/<dict_name_lowercase>"` (singular
"mcu"), but the connector / passive / sensor files map cleanly:
`passives.py → passives/<name>`. The MCU singular is special-cased here.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

PROFILE_KEYS = frozenset({"category", "metadata", "pins"})

# `components/mcus.py` registers under the singular `mcu/` prefix per the
# dossier convention; every other file uses its stem directly.
TYPE_PREFIX_OVERRIDES = {
    "mcus": "mcu",
}


@dataclass(frozen=True)
class Profile:
    """One component profile loaded from `components/*.py`."""

    type: str                              # "mcu/esp32", "passives/led", …
    file: str                              # module file stem (for error messages)
    name: str                              # original dict identifier (for error messages)
    pins: frozenset[str]                   # the set of valid pin names on this profile
    category: str = ""                     # category from the source dict, for layout kernel dispatch
    pins_detail: dict | None = None        # raw `pins:` dict from components/*.py (side/type/direction)
    metadata: dict | None = None           # raw `metadata:` dict from components/*.py


def load_profiles(components_dir: Path | None = None) -> dict[str, Profile]:
    """
    Return a mapping `type_string → Profile` covering every profile under
    `components_dir` (default: `circuitsmith/components/` relative to this
    file).
    """
    if components_dir is None:
        components_dir = Path(__file__).resolve().parent.parent / "components"

    profiles: dict[str, Profile] = {}
    for py_file in sorted(components_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        module = _import_module(py_file)
        prefix = TYPE_PREFIX_OVERRIDES.get(py_file.stem, py_file.stem)
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue
            value = getattr(module, attr_name)
            if not _is_profile(value):
                continue
            type_string = f"{prefix}/{attr_name.lower()}"
            profiles[type_string] = Profile(
                type=type_string,
                file=py_file.stem,
                name=attr_name,
                pins=frozenset(value["pins"].keys()),
                category=value.get("category", ""),
                pins_detail=value.get("pins"),
                metadata=value.get("metadata"),
            )
    return profiles


def _is_profile(value: object) -> bool:
    """True if `value` is a dict whose keys are a superset of PROFILE_KEYS."""
    return isinstance(value, dict) and PROFILE_KEYS.issubset(value.keys())


def _import_module(py_file: Path):
    """Import a Python file by path under a unique module name."""
    module_name = f"_circuit_components_{py_file.stem}"
    spec = importlib.util.spec_from_file_location(module_name, py_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load spec for {py_file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
