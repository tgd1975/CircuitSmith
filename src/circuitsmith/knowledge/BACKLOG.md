# Rule Catalog — Educational Backlog

The seeded catalog (`rules.json`) ships one entry per ERC check
(S1–S5 + E1–E10 = 15 rows). The catalog targets **30–50 entries**
total per [`idea-001.rule-catalog.md §Scope`](../../../docs/developers/ideas/archived/idea-001.rule-catalog.md);
this file lists the remaining candidates so the next maintainer can
land them one at a time without re-litigating scope.

Every entry below is **educational** — there is no ERC predicate
behind it. The skill surfaces these proactively when a maker adds a
component whose profile keywords intersect the entry's keywords. They
inform; they do not fail CI.

## Authoring workflow

1. Pick one candidate from the prioritised list below.
2. Open the corresponding source URL (preferring
   `elektronik-kompendium.de`, then `allaboutcircuits.com`, then a
   vendor datasheet, per the source-of-truth policy).
3. Read the article. **Do not copy text** — write a fresh
   English statement of the same fact. The catalog text is original
   work that links to the source.
4. Add a `rules.json` entry with all six required fields. The
   `enforced_by` field is **omitted** (educational entries do not map
   to an ERC code).
5. Run `python -m circuitsmith.knowledge.validate_catalog` locally to
   confirm format, disclaimer, URL reachability.
6. Open a PR with one rule per commit — `feat(catalog): add <ID> <one-line>`.
   Reviewer checks: source attribution accurate; heuristic
   safe-side; precision disclaimer present; keyword overlap with at
   least one component profile under `circuitsmith/components/` (or a
   `topic:<category>` reserved keyword).

The reviewer's job is **prose accuracy**, not redesign. If a
candidate's framing turns out to be wrong, file an ADR rather than
silently rewriting the entry — the catalog is part of the public
contract by ADR-0006.

## Prioritised candidates

Priority reflects "value to a first-time maker following the day-one
ESP32/nRF52840 templates" — high for things authors hit immediately,
low for advanced techniques they would only ask about after building
several boards.

### Power Supply (target 5–7 total; 2 seeded as enforced, 3–5 here)

| ID | Priority | Title |
|---|---|---|
| PS-01 | high   | Bulk capacitor (10–100 µF) at main power entry |
| PS-02 | high   | LDO vs 78xx linear regulator — headroom and efficiency |
| PS-03 | medium | Buck converter basics — when efficiency matters |
| PS-04 | medium | Ground plane — single point of return on small boards |
| PS-05 | low    | Battery selection (LiPo vs alkaline vs coin cell) |

### Digital Inputs (target 7–10 total; 2 seeded as enforced, 5–8 here)

| ID | Priority | Title |
|---|---|---|
| DI-01 | high   | Switch/button debounce — software delay vs RC hardware |
| DI-02 | high   | Voltage divider for resistive sensors (LDR, thermistor) |
| DI-03 | medium | ADC reference voltage selection — internal vs external |
| DI-04 | medium | Schmitt trigger — when GPIO can't accept the slow edge |
| DI-05 | medium | Encoder wiring — quadrature vs simple rotary |
| DI-06 | low    | Hall-effect sensors — open-drain vs ratiometric outputs |
| DI-07 | low    | Capacitive touch — ESP32 native vs MPR121 IC |

### Digital Outputs (target 7–10 total; 2 seeded as enforced, 5–8 here)

| ID | Priority | Title |
|---|---|---|
| DO-01 | high   | PWM as analog-output proxy — hardware vs software PWM |
| DO-02 | high   | MOSFET gate resistor (10–100 Ω) to dampen ringing |
| DO-03 | high   | Flyback diode across inductive loads (relays, motors) |
| DO-04 | medium | Transistor saturation — base resistor sizing |
| DO-05 | medium | Driving RGB LEDs — common-anode vs common-cathode wiring |
| DO-06 | low    | Solenoid drivers — peak-and-hold vs simple on/off |
| DO-07 | low    | Stepper motors — bipolar vs unipolar drivers |

### Communication (target 5–8 total; 1 seeded as enforced, 4–7 here)

| ID | Priority | Title |
|---|---|---|
| COMM-01 | high   | Breakout boards often integrate I2C pull-ups — inspect the PCB |
| COMM-02 | high   | Bidirectional logic-level shifter for 3.3 V ↔ 5 V buses |
| COMM-03 | medium | SPI bus — CS-per-device, MISO/MOSI direction |
| COMM-04 | medium | UART crossover — TX↔RX, ground shared |
| COMM-05 | low    | CAN bus — termination resistors at both ends |
| COMM-06 | low    | RS-485 — differential pair, half-duplex direction control |

### Hardware Specifics (target 5–8 total; 1 seeded as enforced, 4–7 here)

| ID | Priority | Title |
|---|---|---|
| HW-ESP32-01 | high | Native USB on ESP32-S2/S3/C3 obsoletes external CH340 |
| HW-ESP32-02 | high | ADC2 conflicts with WiFi on ESP32 — use ADC1 channels |
| HW-RPI-01   | high | Raspberry Pi has no built-in ADC — use MCP3008 over SPI |
| HW-ARD-01   | medium | Arduino Uno A4/A5 are the I2C pins — cannot be shared |
| HW-NRF-01   | medium | nRF52840 ADC inputs are full-scale at VDD/4, not VDD |
| HW-ESP32-03 | low  | ESP32 deep sleep current — RTC-GPIO pins only retain state |

## Floor count check

The five seeded categories already meet the floor of the 30–50 target
once the high-priority entries above land:

- Power Supply: 2 enforced + 2 high = 4 (target floor 5; 1 short — fill with PS-03)
- Digital Inputs: 2 enforced + 2 high = 4 (target floor 7; fill DI-03/04/05)
- Digital Outputs: 2 enforced + 3 high = 5 (target floor 7; fill DO-04/05)
- Communication: 1 enforced + 2 high = 3 (target floor 5; fill COMM-03/04)
- Hardware Specifics: 1 enforced + 3 high = 4 (target floor 5; fill HW-ARD-01)

Landing every high-priority entry in this file takes the catalog from
15 to 27 rows. The remaining 3 rows from the medium tier complete the
30-row floor.

## Out of scope

Per [`idea-001-circuit-skill.md §What This Idea Deliberately Excludes`](../../../docs/developers/ideas/archived/idea-001-circuit-skill.md):

- **PCB layout rules** — trace width, copper pour, EMI. The catalog
  is for schematic-level decisions only.
- **Audio signal conditioning** — op-amp gain stages, filter design,
  noise analysis. Day-one library has no analog-audio path.
- **Per-component encyclopedia entries** ("what is a resistor?").
  Definitions go to the LLM's narrow-scope Option B (see `idea-001.rule-catalog.md`
  §Follow-up queries), not to the catalog.
- **High-precision design** — temperature derating, tolerance stacking,
  worst-case voltage drops. Catalog heuristics carry a precision
  disclaimer; the precise calculation belongs in the project's
  electrical analysis, not in a curated rule.
