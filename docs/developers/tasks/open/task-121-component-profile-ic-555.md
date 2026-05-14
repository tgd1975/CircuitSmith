---
id: TASK-121
title: Component profile — ic/555
status: open
opened: 2026-05-14
effort: Small (<2h)
complexity: Medium
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 12
prerequisites: [TASK-110]
---

## Description

Adds the 555 timer profile to a new file
`src/circuitsmith/components/ics.py` (or extends if TASK-122 lands
first).

Per ADR-0010 and the IDEA-009 frozen-decisions, pin keys follow the
silkscreen-pin convention — `"1"` through `"8"` — with silicon
names in `alt:`:

- `pins["1"].alt: ["GND"]`
- `pins["2"].alt: ["TRIG"]`
- `pins["3"].alt: ["OUT"]`
- `pins["4"].alt: ["RESET"]`
- `pins["5"].alt: ["CTRL"]`
- `pins["6"].alt: ["THRES"]`
- `pins["7"].alt: ["DISCH"]`
- `pins["8"].alt: ["VCC"]`

The renderer reads `display_label` for the printed pin label.
`metadata.symbol: "Ic"` for Schemdraw's generic IC element.
`.circuit.yml` connections may reference either form (`U1.1` or
`U1.GND`); the silicon-name form emits a warning under TASK-123's
"555 pin-naming drift" rule (suggestion, not error).

## Acceptance Criteria

- [ ] `ic/555` profile validates; `circuit.yml` referencing it (via either pin form) parses without S5 errors.
- [ ] Golden SVG fixture for a minimal 555 monostable (RC timing network, output to GPIO) renders.
- [ ] `.claude/skills/circuit/docs/components.md` gains an "ICs" table with a row for `ic/555`.
- [ ] No regression on existing fixtures.

## Test Plan

**Host tests** (`pytest tests/`):

- Add `tests/components/test_555_profile.py`.
- Cover: profile auto-discovery, silkscreen-pin (`U1.1`) reference
  resolves, silicon-name (`U1.GND`) reference resolves, golden-SVG
  byte-identity for the monostable.

## Documentation

- `.claude/skills/circuit/docs/components.md` — new "ICs" table
  with the `ic/555` row.

## Prerequisites

- **TASK-110** — frozen decisions: 555 follows ADR-0010
  silkscreen convention.

## Notes

- Pin `5` (CTRL) is usually left floating or tied through a small
  capacitor to GND in monostable applications. ERC will need to
  tolerate the floating-CTRL case — that's TASK-123's
  pin-naming-drift rule territory, not this task's. Document the
  expected wiring in the profile's metadata comment.
