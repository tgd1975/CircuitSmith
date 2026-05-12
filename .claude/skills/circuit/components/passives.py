"""
Day-one passive component library.

Five profiles: resistor, capacitor, LED (unified with v_forward_by_color),
pushbutton, piezo buzzer. The LED follows the component-level
variant-selection pattern from `idea-001.components.md`: one profile, one
`v_forward_by_color` table; `.circuit.yml` selects a colour via
`{ type: passives/led, color: green }`.

The piezo deliberately rides on `category: resistor` (identical 2-pin
inline layout shape) — `category` keys layout, not semantics. See the
design invariant note in `idea-001.components.md` §1.
"""

resistor = {
    "category": "resistor",
    "metadata": {
        "label": "R",
        "keywords": ["resistor", "passive"],
    },
    "pins": {
        "1": {"side": "left",  "type": "TERMINAL", "direction": "bidir"},
        "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
    },
}

capacitor = {
    "category": "capacitor",
    "metadata": {
        "label": "C",
        "keywords": ["capacitor", "passive", "decoupling"],
    },
    "pins": {
        # Two-pin non-polarised default; polar caps are a variant axis we
        # do not encode yet (capacitor dielectric is *not* a clean variant
        # axis per the dossier § "Pattern: component-level variant selection").
        "1": {"side": "left",  "type": "TERMINAL", "direction": "bidir"},
        "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
    },
}

# Unified LED profile with colour-indexed forward-voltage table. ERC check
# E3 reads `v_forward_by_color[color]`; an omitted or unrecognised colour
# falls back to `v_forward_default`. The earlier LED_RED/GREEN/BLUE/WHITE
# dict-spread is retired — one profile + one variant table is simpler and
# carries the colour through to BOM grouping.
LED = {
    "category": "led",
    "metadata": {
        "label": "LED",
        "keywords": ["led", "indicator"],
        "v_forward_by_color": {
            "red":    2.0,
            "green":  2.1,
            "amber":  2.0,
            "yellow": 2.1,
            "blue":   3.2,
            "white":  3.2,
        },
        "v_forward_default": 2.0,
        "symbol": "LED",
    },
    "pins": {
        "A": {"side": "left",  "type": "ANODE",   "direction": "in"},
        "K": {"side": "right", "type": "CATHODE", "direction": "out"},
    },
}

pushbutton = {
    "category": "button",
    "metadata": {
        "label": "BTN",
        "keywords": ["button", "switch"],
    },
    "pins": {
        # Two electrically symmetric contacts on opposite sides so the
        # canonical button routing (MCU column ↔ GND) works for both
        # placement orientations.
        "1": {"side": "left",  "type": "CONTACT", "direction": "bidir"},
        "2": {"side": "right", "type": "CONTACT", "direction": "bidir"},
    },
}

# Piezo: layout-identical to a 2-pin inline passive on a GPIO path, so it
# rides on `category: resistor`. `metadata.symbol: "Speaker"` keeps
# rendering distinct (schemdraw picks the speaker element); `category` is
# never consulted directly for symbol choice — see the day-one library
# footnote ¹ in `idea-001.components.md`.
piezo = {
    "category": "resistor",
    "metadata": {
        "label": "PIEZO",
        "keywords": ["piezo", "buzzer", "alert"],
        "symbol": "Speaker",
    },
    "pins": {
        "1": {"side": "left",  "type": "TERMINAL", "direction": "bidir"},
        "2": {"side": "right", "type": "TERMINAL", "direction": "bidir"},
    },
}
