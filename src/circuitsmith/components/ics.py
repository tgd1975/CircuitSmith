"""
General-purpose IC profiles (EPIC-014 / TASK-121 — IDEA-009 Phase 4).

Ships the NE555 / LM555 timer under `ic/555`. The op-amp dual-supply
profile under `ic/opamp_dual_supply` rides on TASK-122 and extends
this file.

Per ADR-0010, pin keys follow the silkscreen-pin convention — for an
8-pin DIP, keys are `"1"` through `"8"`, with silicon names in
`alt:` so users can write `U1.TRIG` and have the validator resolve
the reference to the same electrical pin as `U1.2`. The renderer
prints `display_label` (e.g. `"TRIG"`) next to the pin glyph.

Pin-side allocation follows the standard schematic-symbol layout
for an 8-pin DIP timer: GND / TRIG / OUT / RESET on the **left**,
CTRL / THRES / DISCH / VCC on the **right**. Schemdraw's generic
`Ic` element is chosen for the symbol so the renderer draws a
labelled rectangle with stub pins.

The 555 pin-naming-drift ERC rule (TASK-123) catches inconsistent
mixing of silkscreen-pin and silicon-name forms within a single
`.circuit.yml`.
"""

# ── NE555 / LM555 timer ───────────────────────────────────────────────────
#
# Standard monostable / astable RC timer. Pin 5 (CTRL) is normally
# left floating or tied to GND through a 10 nF capacitor; both
# topologies are valid and ERC must tolerate the floating case.
#
# Pin direction conventions:
#   - GND (1), VCC (8): power.
#   - TRIG (2), RESET (4), THRES (6): inputs.
#   - CTRL (5): bidirectional analog (signal input *or* small-cap
#     bypass to GND).
#   - OUT (3): output.
#   - DISCH (7): open-collector discharge — modelled as `out` here
#     because it actively sinks current when the internal flip-flop
#     is reset.
ic_opamp_dual_supply = {
    "category": "ic_opamp",
    "metadata": {
        "type": "ic/opamp_dual_supply",  # registry-pin override
        "label": "U",
        # Semantic discriminator the ERC engine reads (TASK-123's E17
        # power-pin-floating rule). `category` keys layout, never
        # semantics, per the project's category-lint contract.
        "kind": "opamp",
        "keywords": ["opamp", "amplifier", "dual-supply", "ic"],
        "symbol": "Opamp",
    },
    "pins": {
        # Non-inverting input on the schematic-symbol top-left;
        # inverting input on the bottom-left. The triangle symbol does
        # not show pin numbers (ADR-0010 doesn't bite), so symbolic
        # keys are canonical here, no `alt:` aliases.
        "IN+": {"side": "left",   "type": "SIGNAL_INPUT",  "direction": "in"},
        "IN-": {"side": "left",   "type": "SIGNAL_INPUT",  "direction": "in"},
        "OUT": {"side": "right",  "type": "SIGNAL_OUTPUT", "direction": "out"},
        # Power pins. `direction: "in"` (never `bidir`) — an op-amp
        # supply pin is unconditionally a power input; the
        # power-pin-floating ERC rule (TASK-123) relies on this
        # invariant to fire deterministically.
        "V+": {"side": "top",     "type": "POWER_INPUT",   "direction": "in"},
        "V-": {"side": "bottom",  "type": "POWER_INPUT",   "direction": "in"},
    },
}


ic_555 = {
    "category": "ic_timer",
    "metadata": {
        "type": "ic/555",  # registry-pin per registry.py override mechanism
        "label": "U",
        # Semantic discriminator the ERC engine reads (TASK-123's E18
        # pin-naming-drift rule). `category` keys layout, never
        # semantics, per the project's category-lint contract.
        "kind": "timer",
        "keywords": ["555", "ne555", "lm555", "timer", "ic"],
        "symbol": "Ic",
    },
    "pins": {
        "1": {"side": "left",  "type": "GROUND_RETURN", "direction": "in",
              "alt": ["GND"],   "display_label": "GND"},
        "2": {"side": "left",  "type": "SIGNAL_INPUT",  "direction": "in",
              "alt": ["TRIG"],  "display_label": "TRIG"},
        "3": {"side": "left",  "type": "SIGNAL_OUTPUT", "direction": "out",
              "alt": ["OUT"],   "display_label": "OUT"},
        "4": {"side": "left",  "type": "SIGNAL_INPUT",  "direction": "in",
              "alt": ["RESET"], "display_label": "RESET"},
        "5": {"side": "right", "type": "SIGNAL_INPUT",  "direction": "bidir",
              "alt": ["CTRL"],  "display_label": "CTRL"},
        "6": {"side": "right", "type": "SIGNAL_INPUT",  "direction": "in",
              "alt": ["THRES"], "display_label": "THRES"},
        "7": {"side": "right", "type": "SIGNAL_OUTPUT", "direction": "out",
              "alt": ["DISCH"], "display_label": "DISCH"},
        "8": {"side": "right", "type": "POWER_INPUT",   "direction": "in",
              "alt": ["VCC"],   "display_label": "VCC"},
    },
}
