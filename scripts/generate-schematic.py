#!/usr/bin/env python3
"""
Circuit schematic generator.

Draws a documentation-quality SVG schematic showing the full dev-board pinout as
an IC block. Used GPIO pins have their circuits drawn (LED+resistor or button+GND);
unused pins get NC markers; power pins get supply/ground symbols.

Per TASK-006: the dev-board pin tables live in
`.claude/skills/circuit/components/mcus.py` (loaded dynamically below), not
inline in this script. Circuit-role assignment (which silicon pin drives which
LED / button) stays here because it is firmware/config concern, not silicon
profile concern. The script's byte-identical SVG output is the regression
guard for the refactor.

Usage:
    python scripts/generate-schematic.py --target esp32
    python scripts/generate-schematic.py --target nrf52840
    python scripts/generate-schematic.py --target esp32 --output path/to/out.svg
"""

import argparse
import importlib.util
import json
import pathlib

import matplotlib
import schemdraw
import schemdraw.elements as elm

matplotlib.use("Agg")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MCUS_PY = REPO_ROOT / ".claude/skills/circuit/components/mcus.py"

LED_R = 220    # current-limiting resistor, ohms
BTN_PU = 10    # button pull-up resistor, kΩ

# ── Pin-type constants ──────────────────────────────────────────────────────
LED   = "led"    # GPIO output → 220 Ω → LED → GND
BTN   = "btn"    # GPIO input  → push-button → GND
GND   = "gnd"    # GND pin → ground symbol
PWR   = "pwr"    # Power rail → labelled power symbol (3V3, VIN, VBAT, VBUS)
NC    = "nc"     # Unused GPIO → no-connect marker
FLASH = "flash"  # SPI-flash internal pin → no-connect, labelled FLASH
SPEC  = "spec"   # Special (EN, RST, AREF) → no-connect, labelled as-is


# ── Profile loader ──────────────────────────────────────────────────────────

def _load_mcus():
    """Import .claude/skills/circuit/components/mcus.py by path."""
    spec = importlib.util.spec_from_file_location("_cs_mcus", MCUS_PY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {MCUS_PY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _column_pins(profile: dict, side: str) -> list[tuple[str, dict]]:
    """Return (pin_name, pin_data) pairs on the given side in declaration order."""
    return [(name, data) for name, data in profile["pins"].items()
            if data["side"] == side]


def _display_label(name: str, data: dict) -> str:
    """The label printed on the pin lead."""
    return data.get("display_label", name)


# ── Board definitions ───────────────────────────────────────────────────────
# Each pin: (anchor_name, outside_label, pin_type, circuit_label_or_None)

def _esp32_pins(profile: dict, cfg: dict) -> tuple[list, list]:
    """
    Joy-IT SBC-NodeMCU-ESP32 (30-pin, 15 per side).
    Source: https://joy-it.net/files/files/Produkte/SBC-NodeMCU-ESP32/SBC-NodeMCU-ESP32-Manual-2021-06-29.pdf

    Used pins (from data/config.json):
      Outputs: D2=STATUS (onboard blue LED), D26=BT_LED, D5/D18/D19=SEL_1/2/3
      Inputs:  D21=SELECT, D13/D12/D27/D14=BTN_A/B/C/D

    Note on STATUS: the firmware drives `ledPower` for boot-mismatch,
    delayed-action and load-error signals. On NodeMCU-style boards GPIO 2
    carries an onboard blue LED, so the schematic labels that pin STATUS
    rather than PWR_LED — the panel "power" LED is hardwired to VCC and
    is not firmware-controlled.
    """
    used_leds = {
        cfg["ledPower"]:     "STATUS",
        cfg["ledBluetooth"]: "BT_LED",
    }
    for i, g in enumerate(cfg["ledSelect"]):
        used_leds[g] = f"SEL_{i + 1}"

    used_btns = {cfg["buttonSelect"]: "SELECT"}
    for i, g in enumerate(cfg["buttonPins"]):
        used_btns[g] = f"BTN_{chr(ord('A') + i)}"

    def classify(name: str, data: dict) -> tuple:
        label = _display_label(name, data)
        ptype = data["type"]

        if ptype == "GROUND":
            return (name, label, GND, None)
        if ptype == "POWER":
            return (name, label, PWR, label)
        if ptype == "RESET":
            return (name, label, SPEC, name)

        # GPIO and INPUT_ONLY pins follow the circuit-role map keyed by
        # silicon GPIO number. Pin names like "D34" map to int 34;
        # non-Dxx-form pins (VP, VN, TX0, …) have no numeric index and
        # therefore never match the used_leds / used_btns config.
        num = _gpio_number(name)
        if num is not None and num in used_leds:
            return (name, label, LED, used_leds[num])
        if num is not None and num in used_btns:
            return (name, label, BTN, used_btns[num])
        return (name, label, NC, None)

    left  = [classify(n, d) for n, d in _column_pins(profile, "left")]
    right = [classify(n, d) for n, d in _column_pins(profile, "right")]
    return left, right


def _gpio_number(name: str) -> int | None:
    """Extract a numeric GPIO index from a Dxx-style pin name."""
    if not name.startswith("D"):
        return None
    suffix = name[1:]
    return int(suffix) if suffix.isdigit() else None


# nRF52840 firmware-driven role assignments. Hardcoded — the predecessor
# inlined them too. Preserved verbatim for byte-identical SVG output.
_NRF52840_ROLES: dict[str, tuple[str, str | None]] = {
    "D5":   (LED, "BT_LED"),
    "D6":   (LED, "PWR_LED"),
    "D9":   (LED, "SEL_1"),
    "D10":  (LED, "SEL_2"),
    "D11":  (LED, "SEL_3"),
    "D12":  (BTN, "SELECT"),
    "A0":   (BTN, "BTN_A"),
    "A1":   (BTN, "BTN_B"),
    "A2":   (BTN, "BTN_C"),
    "A3":   (BTN, "BTN_D"),
    "EN":   (SPEC, "EN"),
    "RST":  (SPEC, "RST"),
    "AREF": (SPEC, "AREF"),
}


def _nrf52840_pins(profile: dict) -> tuple[list, list]:
    """
    Adafruit Feather nRF52840 Express (#4062) pinout.
    Source: https://github.com/adafruit/Adafruit-nRF52-Bluefruit-Feather-PCB

    Used pins (from lib/hardware/nrf52840/include/builder_config.h):
      Outputs: D5(P1.08)=BT_LED, D6(P0.07)=PWR_LED,
               D9(P0.26)=SEL_1, D10(P0.27)=SEL_2, D11(P0.06)=SEL_3
      Inputs:  D12(P0.08)=SELECT, A0(P0.04)=BTN_A, A1(P0.05)=BTN_B,
               A2(P0.30)=BTN_C, A3(P0.28)=BTN_D
    """

    def classify(name: str, data: dict) -> tuple:
        label = _display_label(name, data)
        ptype = data["type"]

        if ptype == "GROUND":
            return (name, label, GND, None)
        if ptype == "POWER":
            return (name, label, PWR, label)
        if name in _NRF52840_ROLES:
            kind, clabel = _NRF52840_ROLES[name]
            return (name, label, kind, clabel)
        return (name, label, NC, None)

    left  = [classify(n, d) for n, d in _column_pins(profile, "left")]
    right = [classify(n, d) for n, d in _column_pins(profile, "right")]
    return right, left


# ── Drawing ─────────────────────────────────────────────────────────────────

def _draw(mcu_label: str, right_pins: list, left_pins: list, output: str) -> None:
    ic_right = [elm.IcPin(name=a, side="right", pin=lbl) for a, lbl, *_ in right_pins]
    ic_left  = [elm.IcPin(name=a, side="left",  pin=lbl) for a, lbl, *_ in left_pins]

    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=9, unit=3)

        mcu = d.add(elm.Ic(
            pins=ic_right + ic_left,
            edgepadW=3.0,
            edgepadH=0.5,
            pinspacing=2.0,
            leadlen=1.5,
            label=mcu_label,
        ))

        def draw_side(pins: list, direction: str) -> None:
            for anchor, _lbl, ptype, clabel in pins:
                pt = getattr(mcu, anchor)
                if ptype == LED:
                    d.add(elm.Resistor().at(pt).theta(180 if direction == "left" else 0)
                          .label(f"{LED_R} Ω", loc="top"))
                    d.add(elm.LED().theta(180 if direction == "left" else 0)
                          .label(clabel, loc="top"))
                    d.add(elm.Ground())
                elif ptype == BTN:
                    theta = 180 if direction == "left" else 0
                    lead = d.add(elm.Line().at(pt).theta(theta).length(0.6))
                    d.add(elm.Dot().at(lead.end))
                    pullup = d.add(elm.Resistor().up().at(lead.end).length(1.0)
                                   .label(f"{BTN_PU} kΩ", loc="right", ofst=(0.1, 0)))
                    d.add(elm.Label().at(pullup.end).label("3V3", loc="top"))
                    d.add(elm.Button().at(lead.end).theta(theta)
                          .label(clabel, loc="bot"))
                    d.add(elm.Ground())
                elif ptype == GND:
                    d.add(elm.Ground().at(pt))
                elif ptype == PWR:
                    d.add(elm.Dot().at(pt))
                    d.add(elm.Label().at(pt).label(clabel,
                          loc="left" if direction == "left" else "right"))
                elif ptype in (NC, FLASH, SPEC):
                    d.add(elm.NoConnect().at(pt))

        draw_side(right_pins, "right")
        draw_side(left_pins, "left")

        d.save(output)

    svg_path = pathlib.Path(output)
    svg = svg_path.read_text()
    svg = svg.replace(
        '<g id="figure_1">',
        '<rect width="100%" height="100%" fill="white"/>\n <g id="figure_1">',
    )
    svg_path.write_text(svg)
    print(f"Saved: {output}")


# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate circuit schematic SVG.")
    parser.add_argument("--target", choices=["esp32", "nrf52840"], required=True)
    parser.add_argument("--output",
                        help="Output path (default: docs/builders/wiring/<target>/main-circuit.svg)")
    args = parser.parse_args()

    default_out = str(REPO_ROOT / "docs/builders/wiring" / args.target / "main-circuit.svg")
    output = args.output or default_out

    mcus = _load_mcus()

    if args.target == "esp32":
        cfg = json.loads((REPO_ROOT / "data/config.json").read_text())
        left, right = _esp32_pins(mcus.esp32, cfg)
        _draw("ESP32 NodeMCU-32S", right, left, output)
    else:
        right, left = _nrf52840_pins(mcus.nrf52840)
        _draw("nRF52840 Feather", right, left, output)


if __name__ == "__main__":
    main()
