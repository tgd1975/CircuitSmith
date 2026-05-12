---
id: TASK-059
title: Wire Phase 2b gate into release_snapshot.py with CS_PHASE2B_BYPASS
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Medium
human-in-loop: No
epic: circuit-renderer-layout
order: 17
prerequisites: [TASK-058]
---

## Description

Extend [`scripts/release_snapshot.py`](../../../../scripts/release_snapshot.py)
to consult the Phase 2b trigger report (TASK-058) and refuse to cut a
release when:

- `non_addressable_count > 0` (one or more escalations that a §5.3
  table addition cannot retire — router stalls, slot overflows, or
  rubric blocks), AND
- EPIC-002 Phase 2b tasks (TASK-017 through TASK-021) are still
  `open` in the task system (i.e. the trigger has fired but the
  response is not yet underway).

When the gate fires, the release script:

1. Prints the Markdown summary from the trigger check.
2. Names the next action: "Open EPIC-002 Phase 2b tasks (TASK-017..021)
   via `/ts-task-active TASK-017`, or — if the failure is genuinely
   one-off — re-classify the escalation in the source `meta.yml` and
   re-run."
3. Exits non-zero.

A documented override exists for cases like "we just opened Phase 2b
yesterday and the tasks are not yet `active`":

```bash
CS_PHASE2B_BYPASS="<reason>" ./scripts/release_snapshot.py ...
```

The bypass is appended to `.git/cs-phase2b-bypass.log` with timestamp
and reason, matching the existing `CS_COMMIT_BYPASS` pattern from
[CLAUDE.md](../../../../CLAUDE.md). Reserved for "trigger fired, response
is underway, release should ship anyway" — not for routine release.

## Acceptance Criteria

- [ ] `release_snapshot.py` invokes `scripts/check_phase2b_trigger.py` and parses the JSON.
- [ ] Release refuses to cut when the gate condition is met; the failure message is actionable (names which tasks to activate).
- [ ] The release proceeds when `non_addressable_count == 0` regardless of `no_rule_count`.
- [ ] The release proceeds when one or more Phase 2b tasks (TASK-017..021) are in `active` or `closed` status.
- [ ] `CS_PHASE2B_BYPASS="<reason>"` allows the release to proceed and appends to `.git/cs-phase2b-bypass.log`.
- [ ] `tests/test_release_phase2b_gate.py` covers: gate fires (non_addressable + tasks-open); gate doesn't fire (non_addressable + tasks-active); gate doesn't fire (zero escalations); bypass works and is logged.

## Test Plan

Mock the trigger-check subprocess and the task-system lookup; assert
each branch of the gate logic. Integration test: a fixture repo with a
mocked task system carrying TASK-017 in `open/`, then `active/`, plus
a fixture `meta.yml` with a `router-stall` escalation — confirm the
release script behaves correctly in each combination.

## Prerequisites

- **TASK-058** — the trigger check is the input.

## Notes

This task turns the dossier's "the maintainer evaluates trigger status
at every release-prep review" from policy into mechanism. The
maintainer can still override, but the override is explicit, logged,
and a positive act — not a default that gets skipped when the queue is
busy.

Item 6 of the architecture-review recommendations.
