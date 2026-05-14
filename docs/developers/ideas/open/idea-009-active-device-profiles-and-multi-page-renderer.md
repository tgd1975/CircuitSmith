---
id: IDEA-009
title: Active-device component profiles (BJT, 555, op-amp) and multi-page renderer support
description: Unblock the EPIC-012 gallery's analog examples by adding active-device profiles + the renderer's page-break path
category: 🛠️ tooling
---

## Motivation

EPIC-012's example gallery shipped four entries that the v0.1
pipeline cannot render:

- **TASK-097** common-emitter amplifier — needs a `bjt_npn`
  component profile and analog signal-path layout rules.
- **TASK-098** 555 monostable timer — needs a `ic/555` profile
  with the pin/role conventions matching standard 555 schematics.
- **TASK-099** op-amp non-inverting buffer — needs an
  `ic/opamp_dual_supply` profile with `V+`, `V-`, `OUT`, and dual
  power rails.
- **TASK-100** multi-page split — needs a renderer page-break
  path the v0.1 codebase does not yet expose. Even with the
  profiles above, this task needs renderer work to span pages.

Each of those tasks closed with a `blocked-on-component-profile`
outcome and a pointer to this idea. The gallery's `circuit.yml`
files are not committed because authoring them against
non-existent profiles would produce S5 errors at schema time and
mislead future contributors about what the library supports.

## Two halves of the fix

### Half 1 — active-device component profiles

The minimum profile additions to unblock the four gallery tasks:

- **`bjt_npn`** (and `bjt_pnp`) — three terminals (`B`, `C`, `E`).
  Profile needs to carry the role/direction metadata the kernel
  uses to decide which terminal is signal-in vs signal-out, since
  BJT topology is direction-sensitive (CE amp, CC follower, CB
  amp). The metadata fields likely look like
  `metadata.bjt_terminals: {base: B, collector: C, emitter: E}`
  so layout rules can consume them by name.
- **`ic/555`** — eight pins, conventional names (`GND`, `TRIG`,
  `OUT`, `RESET`, `CTRL`, `THRES`, `DISCH`, `VCC`). Symbol box
  with pins labelled, layout treated as a small DIP package.
- **`ic/opamp_dual_supply`** — five pins (`IN+`, `IN-`, `OUT`,
  `V+`, `V-`). Power pins on one side, signal pins on the other.
  The triangle symbol Schemdraw already supports.

Each profile adds entries to `src/circuitsmith/components/<file>.py`
and corresponding rows to `.claude/skills/circuit/docs/components.md`.

### Half 2 — multi-page renderer support

TASK-100 explicitly stresses the renderer's page-break path. v0.1
ships single-page rendering only — there's no exposed mechanism to
split a circuit across multiple sheets, no `page:` slot vocabulary,
no inter-sheet net-label connector.

What lands here:

- A `pages:` field in `.layout.yml` (or, alternatively, a
  per-component `page: N` on each placement) that the kernel
  honours when deciding the slot layout. Components on different
  pages render to different SVGs.
- A net-label convention for nets that span pages (the same name
  appears on the boundary of both sheets, with a "see page N"
  annotation).
- Schemdraw's existing multi-figure support is the rendering
  primitive; the work is plumbing it through the kernel's region
  vocabulary and exposing the `--out` flag in a multi-file form
  (`--out main-circuit-p1.svg --out main-circuit-p2.svg`, or a
  single `--out main-circuit.svg` that produces `-p1`/`-p2`
  suffixes automatically).

## Acceptance shape

A future epic that closes this idea probably splits into:

- One task per active-device profile (Half 1, three tasks).
- One task per gallery entry that the profile unblocks
  (TASK-097/098/099, reopened — actually probably new tasks that
  reference the closed ones).
- One task for the renderer page-break path (Half 2).
- One task for TASK-100's re-attempt under the multi-page
  renderer.

## Related

- [IDEA-008](idea-008-first-class-sub-blocks-and-non-led-kernel-rules.md)
  — kernel canonical rules for non-LED groupings. Half 1 of this
  idea (active-device profiles) is independent, but Half 1 of
  IDEA-008 (non-LED kernel rules, esp. `R + R`) blocks
  TASK-096 in the same gallery; the two ideas are likely worked
  in tandem.
- [TASK-096](../tasks/closed/task-096-example-voltage-divider.md),
  [TASK-097](../tasks/closed/task-097-example-common-emitter-amplifier.md),
  [TASK-098](../tasks/closed/task-098-example-555-monostable.md),
  [TASK-099](../tasks/closed/task-099-example-opamp-non-inverting-buffer.md),
  [TASK-100](../tasks/closed/task-100-example-multi-page-split.md)
  — the gallery tasks that closed with the
  blocked-on-this-idea outcome.
