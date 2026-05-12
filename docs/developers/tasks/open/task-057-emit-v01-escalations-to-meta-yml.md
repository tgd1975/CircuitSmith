---
id: TASK-057
title: Emit v0.1 kernel fail-loud events to meta.yml.provenance.escalations
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Medium
human-in-loop: No
epic: circuit-renderer-layout
order: 15
prerequisites: [TASK-011, TASK-012, TASK-013]
---

## Description

The Phase 2b trigger gate (TASK-058, TASK-059) needs a corpus to read.
The dossier's
[layout-engine concept §17.2](../../ideas/archived/idea-001.layout-engine-concept.md)
defines "fail-loud events" in the v0.1 kernel — these must land in
`meta.yml.provenance.escalations` so the gate can count them, not just
appear in stderr where they vanish after the build.

This task extends `meta.yml.provenance` with an `escalations` array of
objects, populated by the v0.1 kernel and the structural rubric
whenever a fail-loud event occurs:

```yaml
provenance:
  escalations:
    - circuit: full-pedal
      category: no-canonical-rule
      component: bme280
      slot_requested: left-column
      detail: "no §5.3 entry for (sensor, i2c-block)"
```

The `category` field is an enum that drives the trigger logic:

| Category | Meaning | §5.3-addressable? |
|---|---|---|
| `no-canonical-rule` | Kernel could not find a §5.3 entry for (category, shape) | yes |
| `slot-overflow` | A region's capacity was exceeded | no — topology problem |
| `router-stall` | Manhattan router could not route a net | no — topology problem |
| `rubric-fail-overlap` | Rubric blocked emission on `overlaps` | no — rendering problem |
| `rubric-fail-labels-fit` | Rubric blocked emission on `labels_fit` | no |
| `rubric-fail-wire-crossings` | Rubric blocked emission on `wire_crossings` | no |

The `escalations` array is empty on a clean kernel-only run. The field
is the contract TASK-058 reads.

## Acceptance Criteria

- [ ] `meta.yml.provenance.escalations` is written on every renderer run (`[]` on a clean run, never absent).
- [ ] The v0.1 kernel emits one entry with the correct `category` and `detail` on every fail-loud event.
- [ ] The structural rubric (TASK-011) emits one entry with the `rubric-fail-*` category per blocking-check failure.
- [ ] Schema for an `escalations` entry is defined alongside `layout.schema.json` (or in a sibling `meta.schema.json`).
- [ ] `tests/test_meta_yml_escalations.py` covers each category being emitted on a deliberately-failing fixture.
- [ ] `docs/layout.md` documents the category enum and its meaning.

## Test Plan

For each category: construct or load a fixture that triggers it
deterministically, run the renderer, parse the resulting `meta.yml`,
assert one `escalations` entry with the expected `category`. The
"clean run produces `[]`" path is covered against the `full-pedal`
fixture from TASK-014.

## Prerequisites

- **TASK-011** — the structural rubric is one of the emitters.
- **TASK-012** — the renderer is what writes `meta.yml`.
- **TASK-013** — `layout.schema.json` is where (or where alongside which) the entry shape lives.

## Notes

This task **precedes**
[TASK-020](task-020-extend-meta-yml-provenance.md) in the
meta.yml-provenance authoring chain. TASK-020 builds on the
`escalations` field this task introduces by adding `ai_invoked` and
AI-placer-specific reason codes for Phase 2b. The two tasks together
produce the unified provenance format the dossier specifies.

The `category` enum is the contract that
[TASK-058](task-058-implement-check-phase2b-trigger.md) reads to
decide whether the Phase 2b trigger has fired.
