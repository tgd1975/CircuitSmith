---
example: voltage-divider
status: blocked-on-layout-kernel
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

> **v0.1 layout-kernel limitation.** This example does **not** ship a
> rendered SVG yet. The CircuitSmith v0.1 layout kernel's canonical
> rule table covers `R + LED` (status indicator) and `R + pull-up`
> (button pull) but does not yet cover bare `R + R` groupings such as
> a voltage divider. Under `--no-ai` (the CI default per ADR-0002),
> the kernel escalates with `no-canonical-rule` and refuses to place
> the second resistor. Under `--ai`, an Anthropic SDK + API key are
> required and the placer would consume credit per render — not
> appropriate for a committed gallery fixture.
>
> The missing capability is filed as
> [IDEA-008](../../../developers/ideas/open/idea-008-first-class-sub-blocks-and-non-led-kernel-rules.md);
> the SVG, layout sidecar, and meta sidecar will land for this
> example as soon as the kernel canonical-rule additions (Half 1 of
> that idea) ship.

The ERC engine **does** accept the circuit standalone — running
`.venv/bin/python -m circuitsmith.erc_engine --circuit circuit.yml`
on the committed input produces one expected E9 pending-promotion
warning and zero errors. The circuit is electrically sound; only
the layout kernel does not know how to draw it deterministically.

## What makes it interesting

This entry serves two purposes simultaneously:

1. It establishes the **gallery README template** every later
   example follows (the section headings, the
   excerpted-from-disk YAML, the "what makes it interesting"
   pattern).
2. It surfaces the **first concrete v0.1 kernel limitation** a real
   user hits — the voltage divider is, structurally, the
   simplest-possible circuit *the kernel cannot render*. Future
   readers landing here see the gap immediately and know where to
   look for the follow-up (IDEA-008).

The CI regression diff (TASK-101) skips this entry until the SVG
lands.

## Next example

[Common-emitter amplifier](../common-emitter-amplifier/) — first
entry with an active device (transistor) and an analog signal-flow
story. Also blocked on missing component profiles at v0.1; the
gallery's "blocked-on" entries cluster at the front of the reading
order so they are easy to skip past once they unblock.
