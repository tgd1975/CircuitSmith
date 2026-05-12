"""
MCU board profiles for the two day-one targets.

Both profiles are **dev-board** profiles per ADR-0010: pin names follow the
header silkscreen (`D34`, `VIN`, `3.3V`, `A0`, …); silicon identifiers
(`IO34`, `P0.04`, …) live in each pin's `alt:` field. The chip-level
electrical metadata (`vcc_min`, `vcc_max`, `max_gpio_current_ma`,
`max_total_current_ma`) sits in `metadata`; per-pin silicon attributes
(`is_strapping`, `func`, `INPUT_ONLY` type) live on the pin entry.

`display_label` overrides what the renderer prints next to a pin when the
silkscreen text differs from the profile key — e.g. the Joy-IT NodeMCU
prints `VP (D36)` next to the input-only IO36 lead, and the Feather prints
`D13 P1.09` next to its IO leads. Pins without `display_label` render
their dict key verbatim.

`side` on power/ground pins reflects the dev-board column position
(matching the silkscreen), not the dossier's canonical
top/bottom-for-power convention — the dossier (`idea-001.components.md`
§3) explicitly notes that `side` on GND pins is advisory and preserves
BOM/documentation use, so this deviation is contract-clean.

Profile shape: `{category, metadata, pins}` per
`docs/developers/ideas/archived/idea-001.components.md`.

References:
  - ESP32-WROOM-32 datasheet (Espressif, rev v3.4):
    https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf
  - Joy-IT SBC-NodeMCU-ESP32 manual:
    https://joy-it.net/files/files/Produkte/SBC-NodeMCU-ESP32/SBC-NodeMCU-ESP32-Manual-2021-06-29.pdf
  - Nordic nRF52840 product specification (Nordic, v1.7):
    https://infocenter.nordicsemi.com/pdf/nRF52840_PS_v1.7.pdf
  - Adafruit Feather nRF52840 Express (#4062) pinout:
    https://learn.adafruit.com/introducing-the-adafruit-nrf52840-feather/pinouts
"""

# ── ESP32 NodeMCU-32S (Joy-IT SBC-NodeMCU-ESP32, 30-pin header) ─────────────
#
# Silicon: ESP32-WROOM-32 module (Espressif). Operating supply 3.0–3.6 V;
# max per-GPIO source/sink 40 mA absolute, 20 mA recommended; max total
# current across all VDD pads 1.2 A absolute, but the LDO on the NodeMCU
# board (AMS1117-3.3) limits the practical 3V3 rail to ~600 mA, of which
# ~200 mA is a safe budget for user GPIO once the module itself is fed.
# We use 12 mA per-GPIO (ERC E1 budget) and 200 mA total as the
# conservative defaults; designers can override per-circuit.
#
# Strapping pins (per datasheet §2.4): GPIO0, GPIO2, GPIO5, GPIO12 (MTDI),
# GPIO15 (MTDO). Of these the 30-pin NodeMCU header exposes IO2, IO5, IO12,
# IO15 (IO0 is not broken out).
#
# Input-only pins (per datasheet §2.2): GPIO34, GPIO35, GPIO36, GPIO39. All
# four are on the header (D34, D35, VP = IO36, VN = IO39).
#
# Default I2C pinning (per datasheet §2.5 and Arduino-ESP32 core defaults):
# SDA = IO21, SCL = IO22.

esp32 = {
    "category": "ic",
    "metadata": {
        "label": "ESP32 NodeMCU-32S",
        "manufacturer": "Espressif (Joy-IT SBC-NodeMCU-ESP32 board)",
        "datasheet": "https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf",
        "vcc_min": 3.0,
        "vcc_max": 3.6,
        "max_gpio_current_ma": 12,
        "max_total_current_ma": 200,
        "keywords": ["esp32", "mcu", "wifi", "bluetooth", "3.3v"],
    },
    "pins": {
        # ── Left column (top → bottom on header) ────────────────────────
        "EN":   {"side": "left",  "type": "RESET",      "direction": "in"},
        "VP":   {"side": "left",  "type": "INPUT_ONLY", "direction": "in",
                 "alt": "IO36", "display_label": "VP (D36)"},
        "VN":   {"side": "left",  "type": "INPUT_ONLY", "direction": "in",
                 "alt": "IO39", "display_label": "VN (D39)"},
        "D34":  {"side": "left",  "type": "INPUT_ONLY", "direction": "in", "alt": "IO34"},
        "D35":  {"side": "left",  "type": "INPUT_ONLY", "direction": "in", "alt": "IO35"},
        "D32":  {"side": "left",  "type": "GPIO",       "direction": "bidir", "alt": "IO32"},
        "D33":  {"side": "left",  "type": "GPIO",       "direction": "bidir", "alt": "IO33"},
        "D25":  {"side": "left",  "type": "GPIO",       "direction": "bidir", "alt": "IO25",
                 "display_label": "D25 DAC1"},
        "D26":  {"side": "left",  "type": "GPIO",       "direction": "bidir", "alt": "IO26",
                 "display_label": "D26 DAC2"},
        "D27":  {"side": "left",  "type": "GPIO",       "direction": "bidir", "alt": "IO27"},
        "D14":  {"side": "left",  "type": "GPIO",       "direction": "bidir", "alt": "IO14"},
        "D12":  {"side": "left",  "type": "GPIO",       "direction": "bidir", "alt": "IO12",
                 "is_strapping": True},   # MTDI — strap selects flash voltage
        "D13":  {"side": "left",  "type": "GPIO",       "direction": "bidir", "alt": "IO13"},
        "GNDL": {"side": "left",  "type": "GROUND",     "direction": "in",
                 "display_label": "GND"},
        "VIN":  {"side": "left",  "type": "POWER",      "direction": "in"},

        # ── Right column (top → bottom on header) ───────────────────────
        "D23":  {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO23"},
        "D22":  {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO22",
                 "func": ["I2C_SCL"]},
        "TX0":  {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO1",
                 "display_label": "TX0 (D1)"},
        "RX0":  {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO3",
                 "display_label": "RX0 (D3)"},
        "D21":  {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO21",
                 "func": ["I2C_SDA"]},
        "D19":  {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO19"},
        "D18":  {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO18"},
        "D5":   {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO5",
                 "is_strapping": True},   # boot strap
        "TX2":  {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO17",
                 "display_label": "TX2 (D17)"},
        "RX2":  {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO16",
                 "display_label": "RX2 (D16)"},
        "D4":   {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO4"},
        "D2":   {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO2",
                 "is_strapping": True},   # boot strap; onboard LED on NodeMCU
        "D15":  {"side": "right", "type": "GPIO",       "direction": "bidir", "alt": "IO15",
                 "is_strapping": True},   # MTDO — silences boot log when low
        "GNDR": {"side": "right", "type": "GROUND",     "direction": "in",
                 "display_label": "GND"},
        "V33":  {"side": "right", "type": "POWER",      "direction": "in",
                 "display_label": "3.3V"},
    },
}


# ── Adafruit Feather nRF52840 Express (#4062, 28-pin header) ────────────────
#
# Silicon: Nordic nRF52840 (QIAA package). Operating supply 1.7–3.6 V; the
# Feather regulates VBUS/VBAT to a 3.3 V rail (TLV62569 buck), so for circuit
# purposes the chip sees 3.3 V on its VDD pads. Max per-GPIO drive 14 mA
# (high-drive pads) / 5 mA (standard); we adopt 14 mA as the ceiling and
# leave standard-pad enforcement to firmware. The Feather's regulator
# supports ~500 mA peak; 200 mA is the budget figure here for parity with
# the ESP32 profile.
#
# nRF52840 has no boot-strapping pins in the ESP32 sense (boot mode is set
# by UICR, not pin sampling), so `is_strapping` is False on every pin.
#
# Default TWI (I2C) on the Adafruit Feather Arduino core: SDA = P0.12,
# SCL = P0.11 (the header pins labelled `SDA` and `SCL`).

nrf52840 = {
    "category": "ic",
    "metadata": {
        "label": "nRF52840 Feather",
        "manufacturer": "Nordic (Adafruit Feather nRF52840 Express #4062)",
        "datasheet": "https://infocenter.nordicsemi.com/pdf/nRF52840_PS_v1.7.pdf",
        "vcc_min": 1.7,
        "vcc_max": 3.6,
        "max_gpio_current_ma": 14,
        "max_total_current_ma": 200,
        "keywords": ["nrf52840", "mcu", "ble", "3.3v"],
    },
    "pins": {
        # ── Right column (top → bottom on header) ───────────────────────
        "VBAT": {"side": "right", "type": "POWER",  "direction": "in"},
        "EN":   {"side": "right", "type": "RESET",  "direction": "in"},
        "VBUS": {"side": "right", "type": "POWER",  "direction": "in"},
        "D13":  {"side": "right", "type": "GPIO",   "direction": "bidir", "alt": "P1.09",
                 "display_label": "D13 P1.09"},
        "D12":  {"side": "right", "type": "GPIO",   "direction": "bidir", "alt": "P0.08",
                 "display_label": "D12 P0.08"},
        "D11":  {"side": "right", "type": "GPIO",   "direction": "bidir", "alt": "P0.06",
                 "display_label": "D11 P0.06"},
        "D10":  {"side": "right", "type": "GPIO",   "direction": "bidir", "alt": "P0.27",
                 "display_label": "D10 P0.27"},
        "D9":   {"side": "right", "type": "GPIO",   "direction": "bidir", "alt": "P0.26",
                 "display_label": "D9 P0.26"},
        "D6":   {"side": "right", "type": "GPIO",   "direction": "bidir", "alt": "P0.07",
                 "display_label": "D6 P0.07"},
        "D5":   {"side": "right", "type": "GPIO",   "direction": "bidir", "alt": "P1.08",
                 "display_label": "D5 P1.08"},
        "SCL":  {"side": "right", "type": "GPIO",   "direction": "bidir", "alt": "P0.11",
                 "display_label": "SCL P0.11", "func": ["I2C_SCL"]},
        "SDA":  {"side": "right", "type": "GPIO",   "direction": "bidir", "alt": "P0.12",
                 "display_label": "SDA P0.12", "func": ["I2C_SDA"]},

        # ── Left column (top → bottom on header) ────────────────────────
        "RST":  {"side": "left",  "type": "RESET",  "direction": "in",
                 "display_label": "RESET"},
        "V33":  {"side": "left",  "type": "POWER",  "direction": "in",
                 "display_label": "3.3V"},
        "AREF": {"side": "left",  "type": "SPEC",   "direction": "in", "alt": "P0.31",
                 "display_label": "AREF P0.31"},
        "GNDL": {"side": "left",  "type": "GROUND", "direction": "in",
                 "display_label": "GND"},
        "A0":   {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.04",
                 "display_label": "A0 P0.04"},
        "A1":   {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.05",
                 "display_label": "A1 P0.05"},
        "A2":   {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.30",
                 "display_label": "A2 P0.30"},
        "A3":   {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.28",
                 "display_label": "A3 P0.28"},
        "A4":   {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.02",
                 "display_label": "A4 P0.02"},
        "A5":   {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.03",
                 "display_label": "A5 P0.03"},
        "SCK":  {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.14",
                 "display_label": "SCK P0.14"},
        "MOSI": {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.13",
                 "display_label": "MOSI P0.13"},
        "MISO": {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.15",
                 "display_label": "MISO P0.15"},
        "RX":   {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.24",
                 "display_label": "RX P0.24"},
        "TX":   {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.25",
                 "display_label": "TX P0.25"},
        "D2":   {"side": "left",  "type": "GPIO",   "direction": "bidir", "alt": "P0.10",
                 "display_label": "D2 P0.10"},
    },
}
