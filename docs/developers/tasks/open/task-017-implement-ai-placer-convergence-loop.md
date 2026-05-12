---
id: TASK-017
title: Implement layout_engine/ai_placer.py — convergence loop and reason codes
status: open
opened: 2026-05-12
effort: Large (8-24h)
complexity: Senior
human-in-loop: Main
epic: circuit-renderer-layout
order: 10
prerequisites: [TASK-015]
---

## Description

Phase 2b deliverable — opens only when Phase 2a accumulates concrete
kernel-failure modes that a `§5.3` canonical-slot table addition cannot
retire. Implement `.claude/skills/circuit/layout_engine/ai_placer.py`
with the convergence loop, structured input contract, reason-code set,
and per-run token cap + cost accounting.

The AI placer is invoked by the kernel only when a `no-canonical-rule`
escalation fires — it is not the default path. The convergence loop
calibrates against the failure corpus accumulated during v0.1
operation (per the Phase 2b trigger gate in
`idea-001-circuit-skill.md`).

## Acceptance Criteria

- [ ] `ai_placer.py` implements the full input contract from `idea-001.layout-engine-concept.md §7`.
- [ ] Convergence loop terminates within the per-run token cap; over-cap runs fail-loud with an `ai-cap-exceeded` reason code.
- [ ] Reason-code set matches the spec; every AI invocation logs reason, attempt count, and total cost to `meta.yml.provenance`.
- [ ] AI placer falls through to a `free`-slot hand-authored layout entry if it cannot converge — no silent failure.

## Test Plan

Add `tests/test_ai_placer.py` with mock Anthropic-API responses covering: successful convergence in one round, convergence in two rounds, cap-exceeded fail-loud path, and unrecoverable fail-through to manual layout.

## Prerequisites

- **TASK-015** — Phase 2a cutover must be complete and the failure corpus accumulated.

## Sizing rationale

Sized Large because the convergence loop, the reason-code set, the cost accounting, and the fail-loud paths must all be in place. Splitting "loop without reason codes" is shippable as a placeholder but does not satisfy the Phase 2b acceptance bar.

## Notes

This task is contingent — it opens only when the Phase 2b trigger gate
fires (see `idea-001-circuit-skill.md §Phase 2b`). The epic stays open
with this task in the backlog until the trigger fires.
