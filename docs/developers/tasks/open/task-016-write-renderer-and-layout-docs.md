---
id: TASK-016
title: Write docs/circuit-yaml.md and docs/layout.md
status: open
opened: 2026-05-12
effort: Medium (2-8h)
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

- [ ] `circuit-yaml.md` documents all three connection forms with at least one worked example each.
- [ ] `layout.md` documents the slot vocabulary, the rubric checks, and the overflow response ladder.
- [ ] Both docs cross-reference the relevant companion files in `docs/developers/ideas/open/` for design rationale.
- [ ] A new contributor can author a minimal `.circuit.yml` using only these two docs (validate with a contributor smoke-read).

## Test Plan

No automated tests required — documentation deliverables. Spot-verify GitHub-Markdown rendering and that all cross-references resolve.

## Prerequisites

- **TASK-012** — the renderer behaviour these docs describe must exist.
- **TASK-015** — the cutover establishes the canonical pipeline these docs document.

## Notes

`docs/layout.md` is updated again in Phase 2b (TASK-021) to add the AI
placer section — design the doc structure with that future section in
mind so the addition is non-invasive.
