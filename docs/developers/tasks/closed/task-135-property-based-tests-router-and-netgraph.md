---
id: TASK-135
title: Add property-based tests for the router and NetGraph form-equivalence
status: closed
closed: 2026-06-21
opened: 2026-06-21
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Senior
human-in-loop: No
---

## Description

EPIC-011's router chapter
([`docs/developers/testing/router.md`](../../testing/router.md)) records
the router's headline gap: IDEA-003 anticipated property-based tests over
randomised netlists, but every invariant is currently checked on a
handful of hand-built fixtures. The NetGraph chapter
([`netgraph.md`](../../testing/netgraph.md)) flags the sibling gap: the
three connection forms (`pins` / `path` / `bus`) are asserted equivalent
on fixed fixtures, not generated topologies.

Add a property-based suite (e.g. Hypothesis) covering:

- **Router** — for a generated placed layout: every segment orthogonal,
  every net routable, byte-identical output under input permutation.
  Explicitly out of scope: asymptotic optimality, aesthetic quality.
- **NetGraph** — generated equivalent topologies expressed in different
  connection forms produce the same canonical net membership / hash.

## Acceptance Criteria

- [x] A property-based test module exercises the router invariants over
      generated layouts.
- [x] A property-based test asserts `pins` / `path` / `bus`
      form-equivalence over generated topologies.
- [x] Any new dependency is added to the dev extra; PR-time runs use fast
      strategies, with large-iteration runs deferred to a nightly tier
      (IDEA-014).

## Test Plan

**Host tests** (`pytest`):

- New `tests/layout/test_router_properties.py` plus a NetGraph
  form-equivalence property test.
- Update the coverage matrix + router / netgraph chapters.

## Notes

Surfaced by EPIC-011 (TASK-085 / TASK-086). Coordinates with IDEA-014
(the nightly tier that would host large-iteration property runs).
