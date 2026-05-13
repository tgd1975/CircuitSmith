"""
Day-one connector component library.

Connectors ride on two layout categories: `jack` (USB-C, DC barrel, audio
jacks) and `header` (pin headers, screw terminals). `make_header(n)` and
`make_screw_terminal(n)` are factories — declared sizes are materialised
as top-level module names at import time (`PIN_HEADER_2`, …,
`PIN_HEADER_8`; `SCREW_TERMINAL_2`, `SCREW_TERMINAL_3`) so the
component-library walker in the schema validator picks them up alongside
hand-written profiles.

USB-C CC pins are declared but carry no signal-flow semantics — they exist
so ERC E9 (polarity protection) can attach the "USB-C cable provides
protection" suppression rationale at the connector level. See the dossier
note in `idea-001.components.md` (footnote on USB-C CC pins).
"""

# ── USB-C receptacle (24-pin → 16-net subset for power/data) ────────────────
usb_c = {
    "category": "jack",
    "metadata": {
        "label": "USB-C",
        "kind": "power-connector",
        "keywords": ["usb", "usb-c", "power", "5v"],
    },
    "pins": {
        # 5 V power bus (paired pins on USB-C, modelled as a single VBUS net).
        "VBUS": {"side": "right", "type": "POWER",  "direction": "in"},
        "GND":  {"side": "right", "type": "GROUND", "direction": "in"},
        # Data pairs (one of each — the schema does not model the dual-role
        # mirroring of the spec; both reverse-orientation pairs collapse to
        # one D+/D- net at this level).
        "DP":   {"side": "right", "type": "SIGNAL", "direction": "bidir"},
        "DN":   {"side": "right", "type": "SIGNAL", "direction": "bidir"},
        # Configuration channels. No `direction` semantics in the profile
        # because they are negotiated at runtime; ERC E9 attaches its
        # "cable provides protection" rationale here.
        "CC1":  {"side": "right", "type": "SIGNAL", "direction": "bidir"},
        "CC2":  {"side": "right", "type": "SIGNAL", "direction": "bidir"},
    },
}

# ── 2.1 mm centre-positive DC barrel jack ───────────────────────────────────
dc_jack_2_1mm = {
    "category": "jack",
    "metadata": {
        "label": "DC 2.1 mm",
        "kind": "power-connector",
        "keywords": ["dc", "barrel", "power", "9v"],
    },
    "pins": {
        # Tip is power per centre-positive convention; sleeve is GND.
        "TIP":    {"side": "left", "type": "POWER",  "direction": "in"},
        "SLEEVE": {"side": "left", "type": "GROUND", "direction": "in"},
    },
}

# ── 6.35 mm mono audio jack ─────────────────────────────────────────────────
mono_jack_6_35mm = {
    "category": "jack",
    "metadata": {
        "label": "Mono 1/4\" jack",
        "kind": "signal-connector",
        "keywords": ["jack", "audio", "mono"],
    },
    "pins": {
        # Edge-mounted: both terminals face the same side. `.circuit.yml`
        # narrows tip direction via a net-level `role:` override (audio-in
        # vs audio-out).
        "TIP":    {"side": "left", "type": "SIGNAL", "direction": "bidir"},
        "SLEEVE": {"side": "left", "type": "GROUND", "direction": "in"},
    },
}

# ── 6.35 mm stereo (TRS) audio jack ─────────────────────────────────────────
stereo_jack_6_35mm = {
    "category": "jack",
    "metadata": {
        "label": "Stereo 1/4\" jack",
        "kind": "signal-connector",
        "keywords": ["jack", "audio", "stereo", "trs"],
    },
    "pins": {
        "TIP":    {"side": "left", "type": "SIGNAL", "direction": "bidir"},
        "RING":   {"side": "left", "type": "SIGNAL", "direction": "bidir"},
        "SLEEVE": {"side": "left", "type": "GROUND", "direction": "in"},
    },
}


# ── Header / terminal factories ─────────────────────────────────────────────
#
# Per the day-one library footnote ² in `idea-001.components.md`: every
# pin declares `side: bottom` (interior-facing), and the kernel handles
# the geometric flip when the header lands in `bottom-row`. Templated
# profiles are schema-validated individually after import; the factory is a
# deduplication convenience, not a schema shortcut.

def make_header(n: int) -> dict:
    """Return a `PIN_HEADER_<n>` profile with n pins on `side: bottom`."""
    if n < 1:
        raise ValueError(f"make_header requires n >= 1, got {n}")
    return {
        "category": "header",
        "metadata": {
            "label": f"HDR{n}",
            "kind": "header",
            "keywords": ["header", "breakout"],
        },
        "pins": {
            str(i): {"side": "bottom", "type": "TERMINAL", "direction": "bidir"}
            for i in range(1, n + 1)
        },
    }


def make_screw_terminal(n: int) -> dict:
    """Return a `SCREW_TERMINAL_<n>` profile with n terminals on `side: bottom`."""
    if n < 1:
        raise ValueError(f"make_screw_terminal requires n >= 1, got {n}")
    return {
        "category": "header",
        "metadata": {
            "label": f"ST{n}",
            "kind": "header",
            "keywords": ["screw-terminal", "wiring"],
        },
        "pins": {
            str(i): {"side": "bottom", "type": "TERMINAL", "direction": "bidir"}
            for i in range(1, n + 1)
        },
    }


# Materialise the day-one header / terminal sizes at module import time, so
# the schema validator's `components/*.py` walker sees them as ordinary
# top-level dicts. Adding a new size is a one-line append below.
PIN_HEADER_2 = make_header(2)
PIN_HEADER_3 = make_header(3)
PIN_HEADER_4 = make_header(4)
PIN_HEADER_6 = make_header(6)
PIN_HEADER_8 = make_header(8)

SCREW_TERMINAL_2 = make_screw_terminal(2)
SCREW_TERMINAL_3 = make_screw_terminal(3)
