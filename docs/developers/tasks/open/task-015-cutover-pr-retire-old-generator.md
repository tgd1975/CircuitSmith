---
id: TASK-015
title: Cutover PR — commit full-pedal fixture, retire old generator, retarget CI
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Senior
human-in-loop: Main
epic: circuit-renderer-layout
order: 8
prerequisites: [TASK-014]
---

## Description

The single discrete deliverable that flips the project from the
hand-coded generator to the new renderer. Per `layout §16.1` this is
**one PR**, not a sequence of small PRs — git history is the rollback
path.

Five things land in this PR together:

1. Commit the renderer's SVG + `meta.yml` output for both targets as
   the `full-pedal` fixture's `expected.*` artifacts.
2. Delete `scripts/generate-schematic.py` (the hand-coded generator).
3. Retarget the CI staleness guard from `scripts/generate-schematic.py`
   to the renderer.
4. Remove the existing pre-commit staleness hook (replaced by
   renderer-driven hooks in EPIC-005).
5. Update `docs/builders/wiring/<target>/` to embed the new SVGs.

Pixel-diff against the legacy generator is **not** the acceptance
criterion — different geometric identity, same electrical content,
same readability bar per `layout §16.2`.

## Acceptance Criteria

- [ ] `tests/fixtures/full-pedal/` contains `expected.svg` + `expected.meta.yml` for both targets.
- [ ] `scripts/generate-schematic.py` is deleted and no longer referenced in CI, pre-commit, or docs.
- [ ] CI staleness guard runs the new renderer and `git diff --exit-code` against committed SVGs.
- [ ] Both `docs/builders/wiring/<target>/main-circuit.svg` files are the new renderer's output.

## Test Plan

Run the renderer over both `.circuit.yml` files in CI; the SVG output must match the committed fixture by XML structural comparison (element count + `data-ref` attributes), not pixel diff. Spot-verify both build guides render correctly with the new SVGs embedded.

## Prerequisites

- **TASK-014** — `.circuit.yml` + `.layout.yml` pairs are the renderer's input.

## Notes

This task is intentionally Main HIL — the cutover is irreversible
within the PR (you can't half-cutover) and the maintainer should
review the full diff before merge. Git history is the only rollback.

## Predecessor source

`scripts/generate-schematic.py` and the `docs/builders/wiring/<target>/` build
guides are inherited from
[AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal) — see
[`scripts/generate-schematic.py`](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/scripts/generate-schematic.py)
and
[`docs/builders/wiring/`](https://github.com/tgd1975/AwesomeStudioPedal/tree/main/docs/builders/wiring).
TASK-001 brings them in as the pre-cutover baseline; this task deletes the
generator and retargets the wiring docs at the renderer output.
