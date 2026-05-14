"""
Active-device profiles (EPIC-014 / TASK-120 — IDEA-009 Phase 4).

Two BJT profiles ship in this file: `bjt_npn` and `bjt_pnp`. They share
the standard schematic-symbol pin convention `B` / `C` / `E` (base /
collector / emitter) and differ only in the schemdraw glyph
(`Bjt` / `BjtPnp`) and the implied direction of the emitter arrow.

Per the EPIC-014 frozen-decisions table (TASK-110), terminal roles are
encoded per-pin via `pins.X.role:` (a literal string from the enum
`{"base", "collector", "emitter"}`) rather than via a separate
`metadata.bjt_terminals:` map. Layout rules read `attrs.get("role")`
directly off the same dict that already carries `side` / `type` /
`direction`, keeping the per-pin annotation surface coherent across
component categories.

Pin sides match the canonical CE-amplifier layout:

- `B` on the **left**  — signal in from a base-drive resistor.
- `C` on the **right** — pulled up to VCC via a collector resistor.
- `E` on the **right** — to GND (NPN) or to VCC (PNP) via emitter
  network.

FET / Darlington / multi-emitter profiles are explicit non-goals in
v1 per IDEA-009 *Out of scope*; they follow the same shape in a
future iteration.
"""

# ── NPN bipolar junction transistor ───────────────────────────────────────
#
# Standard small-signal NPN (2N3904 / BC547 family). The canonical
# common-emitter amplifier sees a base-drive resistor on `B`, the
# collector pulled up to VCC, and the emitter to GND (often via a
# small emitter-degeneration resistor).
bjt_npn = {
    "category": "transistor",
    "metadata": {
        "label": "Q",
        "kind": "transistor",
        "keywords": ["bjt", "npn", "transistor", "active"],
        "symbol": "Bjt",
    },
    "pins": {
        "B": {"side": "left",  "type": "SIGNAL_INPUT",  "direction": "in",
              "role": "base"},
        "C": {"side": "right", "type": "POWER_INPUT",   "direction": "in",
              "role": "collector"},
        "E": {"side": "right", "type": "GROUND_RETURN", "direction": "out",
              "role": "emitter"},
    },
}

# ── PNP bipolar junction transistor ───────────────────────────────────────
#
# Standard small-signal PNP (2N3906 / BC557 family). Mirror of the NPN:
# emitter ties to VCC, collector pulled down through a load to GND,
# base driven low to turn the device on.
bjt_pnp = {
    "category": "transistor",
    "metadata": {
        "label": "Q",
        "kind": "transistor",
        "keywords": ["bjt", "pnp", "transistor", "active"],
        "symbol": "BjtPnp",
    },
    "pins": {
        "B": {"side": "left",  "type": "SIGNAL_INPUT",  "direction": "in",
              "role": "base"},
        "C": {"side": "right", "type": "GROUND_RETURN", "direction": "out",
              "role": "collector"},
        "E": {"side": "right", "type": "POWER_INPUT",   "direction": "in",
              "role": "emitter"},
    },
}
