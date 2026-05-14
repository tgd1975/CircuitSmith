---
id: TASK-119
title: Tutorial step 3 rewrite + sub-block docs
status: open
opened: 2026-05-14
effort: Medium (2-8h)
complexity: Junior
human-in-loop: Clarification
epic: circuit-library-and-renderer-v2
order: 10
prerequisites: [TASK-118]
---

## Description

Closes the IDEA-008 side of EPIC-014. Three docs updates:

- **Tutorial step 3 rewrite** —
  [`docs/users/tutorial/03-sub-blocks.md`](../../users/tutorial/03-sub-blocks.md)
  currently demonstrates the "repeated R+LED" workaround because
  the kernel's R+C low-pass rule did not exist. With TASK-111 and
  TASK-116 landed, the tutorial replaces the workaround with the
  intended RC-pair example using sub-block syntax. The "filed as
  IDEA-008" note becomes "implemented in EPIC-014" (or is
  removed). Golden SVG diff regenerated.
- **Schema chapter update** —
  [`.claude/skills/circuit/docs/circuit-yaml.md`](../../../.claude/skills/circuit/docs/circuit-yaml.md)
  gains a section covering `sub-blocks:` / `instances:` / `ports:`
  grammar with end-to-end YAML examples.
- **Renderer chapter update** —
  [`.claude/skills/circuit/docs/layout.md`](../../../.claude/skills/circuit/docs/layout.md)
  covers inline-box mode and cross-references the future
  hierarchical-port mode gated on multi-page rendering.

## Acceptance Criteria

- [ ] Tutorial step 3 re-rendered SVG diffs cleanly against the new golden.
- [ ] `circuit-yaml.md` documents the sub-blocks/instances/ports grammar with at least one full YAML example.
- [ ] `layout.md` describes inline-box mode and names the hierarchical-port follow-up (without claiming it ships in this epic).
- [ ] `markdownlint-cli2` passes on every edited file.

## Test Plan

No automated tests required for the docs themselves. Tutorial
artefact regeneration uses the existing renderer entry point.

Manual verification:

1. Re-run the renderer against `03-sub-blocks.circuit.yml`;
   confirm the new SVG matches the committed golden.
2. Walk a contributor through the tutorial step 3 prose — the
   "what just happened" section should reflect the actual
   flattener + placer behaviour, not the workaround story it
   replaces.
3. `markdownlint-cli2` passes.

## Documentation

- `docs/users/tutorial/03-sub-blocks.md` — rewrite to use
  first-class sub-block syntax; replace the IDEA-008 "filed as a
  follow-up" pointer with an EPIC-014 implementation note.
- `.claude/skills/circuit/docs/circuit-yaml.md` — adds the
  sub-blocks/instances/ports section.
- `.claude/skills/circuit/docs/layout.md` — covers inline-box
  renderer mode.

## Prerequisites

- **TASK-118** — inline-box renderer must work end-to-end before
  the tutorial can demonstrate it.

## Notes

- This task is `complexity: Junior` because the engineering work
  is already done in TASK-111..118; the work here is technical
  writing against a working pipeline. Don't introduce new YAML
  examples beyond what the schema already accepts — every example
  in this doc is a contract.
