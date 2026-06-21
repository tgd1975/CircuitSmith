---
id: IDEA-014
title: Nightly and release CI test tiers
description: Stand up the missing nightly/release CI tiers EPIC-011 surfaced — catalog online URL check, cross-version render matrix, live-LLM placer smoke, KiCad-import and PartsLedger round-trip.
category: 🛠️ tooling
---

EPIC-011's coverage matrix
([`docs/developers/testing/README.md`](../../testing/README.md)) shows
every one of the 59 test files running at **PR-time** — the nightly and
release columns are entirely empty. Several checks genuinely belong in
slower tiers but have nowhere to run today:

- **Nightly** — the rule-catalog *online* URL-reachability check
  (designated nightly in `ci.yml` comments, but no workflow exists); a
  cross-version matplotlib / Schemdraw render matrix to catch SVG drift
  before a dependency bump forces a full re-baseline; large-iteration
  property runs (see TASK-135).
- **Release** — a live-LLM AI-placer smoke test (costs tokens; kept off
  PR CI per ADR-0002); automated KiCad `.net` import acceptance
  (currently the manual TASK-034 spot-check); a PartsLedger BOM
  round-trip fixture (currently manual; strengthens once EPIC-012 ships
  the round-trip example).

## Rough approach

1. Add a scheduled `nightly.yml` workflow; move the online catalog check
   and the render matrix there.
2. Add a release-time job (or extend the release workflow) for the
   live-LLM smoke and the KiCad / PartsLedger acceptance checks.
3. Backfill the matrix's nightly / release columns as each lands.

## Why an idea, not a task

The exact tier boundaries — and which checks are worth their CI minutes —
are judgment calls best made as a batch. This groups the cadence-tier
gaps EPIC-011 surfaced rather than spawning one task each.
