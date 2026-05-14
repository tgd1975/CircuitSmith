# ERC Report — Tutorial step 4 — broken circuit (deliberately floating button input) — 2026-05-13

| Severity | Ref | Pin | Check | Net | Message |
|---|---|---|---|---|---|
| ⚠️ WARNING | U1 | D13 | E1 Floating input | BTN_USER | signal input U1.D13 on net 'BTN_USER' could not be classified (unresolved `role:`); downgraded from ERROR to WARNING. |
| ⚠️ WARNING | J1 | VBUS | E9 Reverse-polarity unprotected | VCC | power input pin J1.VBUS on net 'VCC' has no diode or P-MOSFET protection element. (WARNING at v0.1 pending the `diode` category.) |

0 error(s), 2 warning(s).

## ⚠️ U1.D13 — E1 Floating input

**Why.** An MCU input pin that is neither driven nor pulled floats. Its measured voltage swings on capacitive coupling from neighbouring traces and the input reads as random bits. Pull-up or pull-down resistors define the idle state when no external source is driving the pin; firmware pulls (the chip's internal weak resistors enabled via `INPUT_PULLUP`) do the same job for inputs the firmware owns. A floating input is rarely the intent and almost always a bug.

**Senior's tip.** For a typical button-to-GND wired on an MCU GPIO, enable `INPUT_PULLUP` in firmware and declare `pull: firmware` on the net — that is the cheapest defined idle state. If the boot-time level matters (strapping pins, level-set inputs), use an external 10 kΩ pull-up to VCC or pull-down to GND. This is a starting point; for precision applications, calculate the exact value or consult the datasheet.

**Source.** <https://www.elektronik-kompendium.de/sites/slt/0204302.htm>

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
