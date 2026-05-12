---
id: TASK-003
title: Write components/connectors.py
status: open
opened: 2026-05-12
effort: Medium (2-8h)
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

- [ ] `connectors.py` defines `usb_c`, `dc_jack_2_1mm`, `mono_jack_6_35mm`, `stereo_jack_6_35mm` profiles.
- [ ] `make_header(n)` and `make_screw_terminal(n)` factories return valid profiles for any supported pin count.
- [ ] Every profile declares `metadata.keywords` (lowercase NFKC tokens).
- [ ] Power-bearing pins (USB-C VBUS, DC jack tip) declare `type: power`.

## Test Plan

No automated tests required — header/terminal factories are exercised by the schema validator (TASK-005) and the renderer (TASK-012).

## Notes

USB-C CC pins are wired but not assigned signal semantics — they exist
so E9 (polarity protection) can document the "USB-C cable provides
protection" suppression rationale at the connector level.
