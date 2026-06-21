---
id: TASK-134
title: Add triggering fixtures for untriggered ERC and schema checks
status: open
opened: 2026-06-21
effort: Medium (2-8h)
complexity: Medium
human-in-loop: No
---

## Description

EPIC-011's per-subsystem test plan surfaced a set of check codes that
ship in `CHECK_TABLE` (or the post-schema validator) but have **no
fixture that actually triggers them**. The coverage table in
[`docs/developers/testing/erc-engine.md`](../../testing/erc-engine.md)
and [`schema.md`](../../testing/schema.md) flags:

- **S1** (single-pin / floating net) — only *avoided* by other fixtures.
- **S6** (slash-form sub-block name collision) — the structural
  type-regex path is tested; S6 itself is not.
- **E4** (INPUT_ONLY pin driven) — the predicate is wired but has no
  clean isolated trigger (an S-class error masks it).
- **E6** (IC VCC pin undecoupled) — dormant; needs a non-MCU IC profile
  with a VCC pin.
- **E8** — no minimal fixture authored.

Add one targeted fixture per code so every check has a triggering case.

## Acceptance Criteria

- [ ] S1, S6, E6, and E8 each have a fixture that produces the finding.
- [ ] E4 has a fixture that triggers it without being masked by an
      S-class error.
- [ ] The coverage table in `erc-engine.md` / `schema.md` is updated to
      mark these as covered.

## Test Plan

**Host tests** (`pytest`):

- Extend `tests/test_erc_engine.py` (E4, E6, E8) and
  `tests/schema/test_sub_blocks_schema.py` / `tests/test_schema_validation.py`
  (S1, S6).
- Each new test asserts the specific check code fires on a minimal
  fixture.

## Notes

Surfaced by EPIC-011 (TASK-087). Backlog (no epic) until a maintenance
epic adopts it. E6 likely needs a fixture-only IC profile or reuse of
the 555 / op-amp profiles' VCC pins.
