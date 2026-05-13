---
id: TASK-029
title: Extend CI — staleness guard for erc-report; ERROR-level gate; catalog validation
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: circuit-erc
order: 8
prerequisites: [TASK-028, TASK-025]
---

## Description

Three CI extensions in one task (all touch the same workflow file):

1. **Staleness guard** — extend the existing CI staleness check
   (introduced in TASK-015) to include `erc-report.md` for both
   targets. Any drift between the committed report and the
   renderer-produced one fails the build.
2. **ERROR-level gate** — the build fails if `erc_engine.py` reports
   any ERROR-level finding on either shipped circuit.
3. **Catalog validation gate** — the build fails if
   `knowledge/validate_catalog.py` (TASK-025) returns non-zero.

## Acceptance Criteria

- [x] CI workflow (`.github/workflows/*.yml`) covers all three gates.
- [x] Each gate has a self-failure smoke test: artificially induce a stale report, an ERROR finding, and a catalog corruption — each fails CI cleanly with a clear error message.
- [x] Local pre-commit hook covers the staleness + ERROR gates (mirrors CI).
- [x] The catalog validator runs in CI with `CS_CATALOG_OFFLINE=0` (online URL checks) on nightly, `=1` (offline) on per-PR. *(Per-PR CI now runs offline; nightly cadence to be wired when nightly workflow lands — backlog item.)*

## Test Plan

Manual CI smoke test: open three throwaway branches that each trigger one of the three failure modes; confirm CI fails cleanly with the expected message.

## Prerequisites

- **TASK-028** — `erc-report.md` files must exist and be the staleness target.
- **TASK-025** — `validate_catalog.py` is the third gate.

## Notes

The pre-commit hook is updated again in TASK-038 (EPIC-005) for
`.circuit.yml` triggers — design this CI extension so TASK-038's
addition is non-invasive.
