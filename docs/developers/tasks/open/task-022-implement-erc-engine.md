---
id: TASK-022
title: Implement erc_engine.py with structural S1–S3 and electrical E1–E10
status: open
opened: 2026-05-12
effort: Large (8-24h)
complexity: Senior
human-in-loop: No
epic: circuit-erc
order: 1
prerequisites: [TASK-008]
---

## Autonomy

`Clarification` → `No` per TASK-060 sweep. ERC engine internals
are bounded by the rule catalog (ADR-0006) and the public S/E IDs
(`co-erc-engine` invariants); file an ADR for predicate-organisation
choices rather than pausing.

## Description

Implement `.claude/skills/circuit/erc_engine.py` with the full v0.1
check set: structural checks `S1–S3` (graph-shape errors that
schema validation does not catch) and electrical checks `E1–E10`
(topology-keyed safety rules). Every check is a pure predicate against
the `NetGraph` — no geometry, no `layout.yml` reads.

`S4` (unknown component reference) and `S5` (unknown pin reference)
are detected by schema validation in TASK-005, but their codes are
defined alongside `S1–S3` in `erc_engine.py`'s constant table so
schema-validation findings surface in the ERC report under the same
severity column and the same catalog-lookup pipeline.

`E6` (decoupling cap), `E7` (I2C pull-up), and `E10` (pin conflict)
ship dormant on the current circuits — they activate when a
qualifying component (non-MCU IC, I2C device, duplicate pin) appears.
`E9` (polarity protection) ships as WARNING on v0.1 because the
`diode` component category is backlogged.

## Acceptance Criteria

- [ ] `erc_engine.py` implements all 13 checks (S1–S3, E1–E10) per the predicates in `idea-001.erc-engine.md`.
- [ ] All 15 check codes (S1–S5 + E1–E10) are defined in a constant table that the report writer (TASK-027) and catalog validator (TASK-025) can introspect.
- [ ] Engine is CLI-invokable standalone and importable from `renderer.py` — both code paths produce identical findings on the same input.
- [ ] Both shipped circuits produce ERC-green output on v0.1 (E9 surfaces as WARNING, not ERROR).

## Test Plan

Add `tests/test_erc_engine.py` with one fixture per check covering: green path on a clean circuit, each check fires on a targeted broken fixture, dormant checks (E6/E7/E10) emit no findings without qualifying components, E9 emits WARNING (not ERROR) on the shipped circuits.

## Prerequisites

- **TASK-008** — `NetGraph` is the engine's input.

## Sizing rationale

Sized Large because the 13 predicates are tightly coupled by the shared `NetGraph` traversal patterns. Splitting per-check produces 13 tiny tasks with redundant setup overhead — not the user's idea of "well-defined."

## Notes

See `idea-001.erc-engine.md` for the per-check predicates, severity
defaults, and report format. The three-level configuration system
(global / per-circuit / per-component overrides) lands as part of
this task.
