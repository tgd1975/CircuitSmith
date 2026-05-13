---
id: TASK-016
title: Write docs/circuit-yaml.md and docs/layout.md
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: circuit-renderer-layout
order: 9
prerequisites: [TASK-012, TASK-015]
---

## Description

Author the two reference documents for the renderer + layout engine:

- `.claude/skills/circuit/docs/circuit-yaml.md` — the full
  `.circuit.yml` format reference: top-level sections, the three
  connection forms with worked examples, schema invocation,
  Markdown ` ```circuit ` block syntax preview (full integration is
  EPIC-005), staleness detection.
- `.claude/skills/circuit/docs/layout.md` — the layout engine user
  guide: slot vocabulary, canonical-slot table excerpt, rubric checks,
  `meta.yml` sidecar, overflow response ladder, position overrides,
  known limitations, `--no-ai`/`--reflow` flags (the flags ship in
  Phase 2b; document the v0.1 absence explicitly).

## Acceptance Criteria

- [x] `circuit-yaml.md` documents all three connection forms with at least one worked example each. _`.claude/skills/circuit/docs/circuit-yaml.md` has dedicated sections per form (`pins`, `path`, `bus`) with worked YAML examples, plus the segment-naming flattener walkthrough and a complete circuit at the end._
- [x] `layout.md` documents the slot vocabulary, the rubric checks, and the overflow response ladder. _`.claude/skills/circuit/docs/layout.md` covers the nine canonical slot regions, the §5.3 dispatch table, the rubric (blocking + advisory), the meta.yml escalations enum, and the §8.3 overflow ladder (with rung 2/3 explicitly marked post-v0.1)._
- [x] Both docs cross-reference the relevant companion files in `docs/developers/ideas/archived/` for design rationale. _The task body cited `docs/developers/ideas/open/` but the IDEA-001 dossier was archived on conversion to EPIC-001..006; both new docs link to the `archived/` paths plus the relevant ADRs (`ADR-0001`, `ADR-0003`, `ADR-0007`, `ADR-0008`)._
- [x] A new contributor can author a minimal `.circuit.yml` using only these two docs. _`circuit-yaml.md` ends with a complete worked example (ESP32 + LED + button + USB-C) that a reader can paste-and-edit; `layout.md` walks the pipeline so the reader knows what the renderer will do with their YAML. A live smoke-read by a fresh contributor is the test plan's open item; the docs are otherwise complete._

## Implementation notes

The two docs land in `.claude/skills/circuit/docs/` per the task body
(skill-internal, portable to the standalone extraction). The
escalations stub written under `docs/layout.md` during TASK-057 was
relocated here; nothing else in the repo references the old root path.
The dossier link path was updated from `docs/developers/ideas/open/`
to `docs/developers/ideas/archived/` because the IDEA-001 dossier was
archived on conversion to its child epics — that's a stale reference
in the task body, not a doc change.

## Test Plan

No automated tests required — documentation deliverables. Spot-verify GitHub-Markdown rendering and that all cross-references resolve.

## Prerequisites

- **TASK-012** — the renderer behaviour these docs describe must exist.
- **TASK-015** — the cutover establishes the canonical pipeline these docs document.

## Notes

`docs/layout.md` is updated again in Phase 2b (TASK-021) to add the AI
placer section — design the doc structure with that future section in
mind so the addition is non-invasive.
