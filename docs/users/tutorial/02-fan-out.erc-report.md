# ERC Report — Tutorial step 2 — a second branch (fan-out) — 2026-05-13

| Severity | Ref | Pin | Check | Net | Message |
|---|---|---|---|---|---|
| ⚠️ WARNING | J1 | VBUS | E9 Reverse-polarity unprotected | VCC | power input pin J1.VBUS on net 'VCC' has no diode or P-MOSFET protection element. (WARNING at v0.1 pending the `diode` category.) |

0 error(s), 1 warning(s).

## ⚠️ J1.VBUS — E9 Reverse-polarity unprotected

**Why.** A barrel jack inserted with the wrong polarity, a battery clipped on backwards, or a non-compliant USB-C cable that mis-asserts CC can deliver negative voltage to the board's supply rail. Without a protection element the MCU sees the reverse voltage on its substrate diodes and the chip dies within milliseconds. A Schottky diode in series with the input absorbs ~0.3 V at the cost of one diode drop; a P-MOSFET pulled to GND through its gate gives lower drop at higher currents. USB-C compliant cables mitigate this but not universally — protection at the board is the safer baseline.

**Senior's tip.** For 5 V USB-C or DC barrel inputs feeding a 3.3 V regulator, a 1N5819 Schottky in series with VBUS gives bullet-proof protection at minimal cost. For battery-powered designs at higher currents, a P-MOSFET with its gate tied to GND through a 100 kΩ pull-down is the next step up. This is a starting point; for precision applications, calculate the exact value or consult the datasheet.

**Source.** <https://www.elektronik-kompendium.de/sites/slt/0201113.htm>

## Pending promotions

**E9 — Reverse-polarity unprotected.** Surfaces as WARNING in v0.1.
The check's intended severity is ERROR (a missing protection diode on
a barrel jack or USB-C power input destroys the MCU on a wiring
mistake), but the `diode` component category is still on the backlog.
Without a way to semantically distinguish a protection diode from any
other 2-terminal passive, every USB-C / barrel-jack circuit would
fail E9 by construction. E9 auto-promotes to ERROR once the `diode`
category lands; see `idea-001.components.md` §Backlog.
