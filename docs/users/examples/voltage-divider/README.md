---
example: voltage-divider
status: shipped
---

# Voltage divider

## What it demonstrates

The smallest meaningful CircuitSmith gallery entry: a two-resistor
voltage divider between `VCC` and `GND` with the tap going to one of
the ESP32's ADC-capable inputs (`U1.D34`). No active devices, no
biasing, no exotic components — the simplest "real" circuit a
hobbyist would ever author.

## The input

The committed `circuit.yml`:

```yaml
meta:
  title: Voltage divider
  target: esp32

components:
  U1: { type: mcu/esp32,         label: ESP32 }
  J1: { type: connectors/usb_c,  label: Power }
  R1: { type: passives/resistor, value: 10000 }
  R2: { type: passives/resistor, value: 10000 }

connections:
  - net: VCC
    pins: [J1.VBUS, U1.VIN, R1.1]

  - net: GND
    pins: [J1.GND, U1.GNDL, U1.GNDR, R2.2]

  - net: ADC_IN
    pins: [U1.D34, R1.2, R2.1]
```

Read the source of truth at
[`circuit.yml`](circuit.yml) — the block above is excerpted, not
re-typed.

## The output

![Voltage divider schematic](voltage-divider.svg)

The renderer's structural emit places `U1` in `mcu-center`, the USB-C
jack `J1` on `bottom-row`, and the two divider resistors (`R1`, `R2`)
into a synthetic `divider-ADC_IN` region in rows 0 and 1 — the
canonical-slot signature minted by `RULE_RR_VOLTAGE_DIVIDER`
(TASK-114). The kernel discriminates a divider from a generic R+R
pair via the tap-net-name regex `/^(V?REF|SENSE|ADC|DIV|TAP)/i`;
`ADC_IN` matches the `ADC` prefix and the rule fires deterministically.

The full layout sidecar lives at [`voltage-divider.layout.yml`](voltage-divider.layout.yml);
ERC report at [`erc-report.md`](erc-report.md); provenance and
rubric metrics at [`voltage-divider.meta.yml`](voltage-divider.meta.yml).

## BOM

| Ref | Type                | Value | Notes                  |
|-----|---------------------|-------|------------------------|
| U1  | `mcu/esp32`         | —     | ESP32 dev board        |
| J1  | `connectors/usb_c`  | —     | USB-C power input      |
| R1  | `passives/resistor` | 10 kΩ | Top half of the divider |
| R2  | `passives/resistor` | 10 kΩ | Bottom half of the divider |

For a divider that produces a midpoint between two arbitrary rails,
keep the two resistors equal-valued (10 kΩ each here gives a 50:50
midpoint that lands well inside the ADC's `0 V … VREF` range). For a
non-50% midpoint, scale the bottom resistor's value:
`V_tap = VCC × (R2 / (R1 + R2))`. This is a starting point; for
precision ADC inputs you may want a series-output filter cap to GND
(an RC low-pass — see tutorial step 1's RC filter sub-block).

## What makes it interesting

This entry serves two purposes simultaneously:

1. It establishes the **gallery README template** every later
   example follows (the section headings, the
   excerpted-from-disk YAML, the BOM block).
2. It is the **first canonical-slot rule beyond v0.1's R+LED set**
   that EPIC-014 added — TASK-114's `RULE_RR_VOLTAGE_DIVIDER`. The
   tap-net hint discriminator (`/^(V?REF|SENSE|ADC|DIV|TAP)/i` or
   `role: divider`) is what keeps a "lonely" R+R pair on a power rail
   from being misclassified as a divider. The other branch — flat
   fall-through with a `divider-ambiguous` warning — is covered by
   E15 in the ERC catalogue.

## Next example

[Common-emitter amplifier](../common-emitter-amplifier/) — first
entry with an active device (transistor) and an analog signal-flow
story. Unblocked by EPIC-014 / TASK-120 (BJT canonical slot).
