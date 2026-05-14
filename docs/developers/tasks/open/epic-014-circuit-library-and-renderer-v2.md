---
id: EPIC-014
name: circuit-library-and-renderer-v2
title: Component library and renderer v2 (sub-blocks, active devices, multi-page)
status: open
opened: 2026-05-14
closed:
assigned:
branch: release/epic-014-circuit-library-and-renderer-v2
---

Seeded by IDEA-008 (First-class sub-blocks and non-LED kernel rules)
and IDEA-009 (Active-device component profiles and multi-page
renderer support).

EPIC-012 (the tutorial and example gallery) closed with five entries
scaffolded but unable to render: the voltage divider blocked on the
v0.1 kernel's missing R+R rule, and TASK-097/098/099/100 blocked on
the absence of active-device profiles plus the renderer's page-break
path. The two follow-up ideas (IDEA-008 and IDEA-009) each carry a
full implementation plan; this epic is the execution layer that
turns those plans into landed code.

The epic bundles three independent capability tracks:

- **IDEA-008 Half 1 — non-LED kernel rules.** Four canonical-slot
  rules (R+C low-pass, R+C high-pass, C+C decoupling pair, R+R
  voltage divider) the layout kernel does not have today. Unblocks
  the voltage-divider gallery entry without requiring sub-block
  syntax.
- **IDEA-008 Half 2 — first-class sub-blocks.** `sub-blocks:` /
  `instances:` schema, netgraph flattener, sub-block ERC, inline-box
  renderer mode. Tutorial step 3's "repeated RC filter" example
  becomes expressible.
- **IDEA-009 — active devices + multi-page renderer.** Three new
  component profiles (`bjt_npn`/`bjt_pnp`, `ic/555`,
  `ic/opamp_dual_supply`), active-device ERC, the `pages:` partition
  in `.layout.yml`, multi-page render driver, cross-page net labels,
  and cross-page ERC. Unblocks the four remaining gallery entries.

The three tracks share Phase 0 (frozen decisions) and converge only
at the gallery re-attempt phase. The two ideas' implementation plans
already enumerate per-task scope, acceptance criteria, dependencies,
and effort estimates — this epic preserves that structure across 24
tasks rather than re-deriving it.

Ordering follows the dependency chain captured in each idea's
mermaid graph: freeze → parallel tracks → ERC → renderer → gallery
re-attempt → docs.

## Tasks

Tasks are listed automatically in the Task Epics section of
`docs/developers/tasks/OVERVIEW.md` and in `EPICS.md` / `KANBAN.md`.
