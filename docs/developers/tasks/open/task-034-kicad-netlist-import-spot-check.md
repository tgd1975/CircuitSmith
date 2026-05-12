---
id: TASK-034
title: Spot-check main-circuit.net imports into KiCad without errors
status: open
opened: 2026-05-12
effort: XS (<30m)
complexity: Medium
human-in-loop: Main
epic: circuit-exporters
order: 4
prerequisites: [TASK-033]
---

## Description

Manual spot check: open both `main-circuit.net` files in KiCad
(`Schematic Editor → File → Import → Netlist`) and confirm KiCad
imports them with no errors or warnings about malformed format.

This is a Main-HIL acceptance step — the netlist is the bridge to
IDEA-011 (PCB design), so the format must be right before downstream
work begins.

## Acceptance Criteria

- [ ] Both `main-circuit.net` files import into KiCad without format errors.
- [ ] Component count and net count in KiCad match the source `.circuit.yml`.
- [ ] If KiCad warns about unknown footprints, document the warning in `idea-001.exporters.md` — footprint assignment is downstream of IDEA-011 and not blocking here.
- [ ] The structural assertions in TASK-049 (parser-level grammar test) pass on the same `.net` files — this manual import only catches what the structural test cannot (KiCad-version-specific warnings, schematic-symbol mismatches), not the inverse.

## Test Plan

Manual verification only (KiCad import is GUI-driven and not scriptable in CI without significant infrastructure). Document the steps and the observed KiCad version in the task closure note.

## Prerequisites

- **TASK-033** — `.net` files must exist to import.

## Notes

KiCad version matters — note which version was used so future
regressions can be reproduced. If KiCad updates change the import
format, this task may need a follow-up.

## Predecessor source

[IDEA-011 (PCB design)](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-011-pcb-board-design.md)
is an AwesomeStudioPedal idea — its landing status and footprint conventions
are tracked there, not here.
