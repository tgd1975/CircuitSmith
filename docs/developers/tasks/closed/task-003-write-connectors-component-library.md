---
id: TASK-003
title: Write components/connectors.py
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-components
order: 3
---

## Description

Author `.claude/skills/circuit/components/connectors.py` with the
day-one connector library: USB-C, DC barrel jack 2.1 mm, mono jack
6.35 mm, stereo jack 6.35 mm, pin headers (2/3/4/6/8-pin, templated
via `make_header(n)`), screw terminals (2/3-pin, templated).

Templating via `make_header(n)` keeps the file from accumulating one
profile per pin count.

## Acceptance Criteria

- [x] `connectors.py` defines `usb_c`, `dc_jack_2_1mm`, `mono_jack_6_35mm`, `stereo_jack_6_35mm` profiles.
- [x] `make_header(n)` and `make_screw_terminal(n)` factories return valid profiles for any supported pin count.
- [x] Every profile declares `metadata.keywords` (lowercase NFKC tokens).
- [x] Power-bearing pins (USB-C VBUS, DC jack tip) declare `type: power`. Uppercase `POWER` per the dossier convention in `idea-001.components.md` §3 (the AC's lowercase is colloquial; the dossier's schema-enforced implication table keys on the uppercase literal).

## Test Plan

No automated tests required — header/terminal factories are exercised by the schema validator (TASK-005) and the renderer (TASK-012).

## Notes

USB-C CC pins are wired but not assigned signal semantics — they exist
so E9 (polarity protection) can document the "USB-C cable provides
protection" suppression rationale at the connector level.
