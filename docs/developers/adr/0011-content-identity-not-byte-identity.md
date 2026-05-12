---
id: ADR-0011
title: SVG regression test uses content-identity, not literal byte-identity, with matplotlib non-determinism normalised
status: Accepted
date: 2026-05-12
dossier-section: docs/developers/tasks/closed/task-006-refactor-generate-schematic-to-use-library.md
---

## Context

[TASK-006](../tasks/closed/task-006-refactor-generate-schematic-to-use-library.md)
demands "byte-identical SVG output" as the regression guard for the
generator refactor. In practice matplotlib injects three
non-deterministic fields into every SVG it writes:

- `<dc:date>` — refreshed at each invocation.
- `<clipPath id="pXXXXXXXXXX">` / `url(#pXXXXXXXXXX)` — randomly
  generated per-run path IDs.
- `<dc:title>Matplotlib vX.Y.Z…</dc:title>` — varies across mpl
  installs (3.10.8 → 3.10.9 already drifted between when the
  reference SVGs were captured and the refactor verification run).

Running the **unchanged** predecessor script twice in a row produces
two SVGs with different SHA-256 hashes. The literal byte-identity
test as written in TASK-006 was unachievable from the start; the
gate as a *content* guard is what it is meant to be.

Three options were considered:

1. **Force matplotlib determinism via `SOURCE_DATE_EPOCH` and patched
   clip-ID generation.** Doable but invasive — touches the script
   that EPIC-002 will retire in a few weeks. Cost-positive for code
   we are about to delete.
2. **Replace the on-disk reference each run.** Loses the regression
   guard's whole point.
3. **Normalise the three non-deterministic fields before
   comparing.** Mechanical, scoped to the test, preserves the
   reference as an archival artefact.

## Decision

Option **(3)**. `tests/test_generator_byte_identity.py` reads both
the freshly-generated and on-disk reference SVG, strips the three
matplotlib-injected fields with a small regex pass, and asserts
string equality on what remains. The test name is kept as
`test_generator_byte_identity` because the spirit — every other byte
must match — is unchanged.

The test is **transient** per TASK-006's own note: it is deleted by
EPIC-002 (TASK-016) when the YAML-driven renderer takes over and
geometric identity intentionally changes per `layout.md §16.2`. No
long-lived determinism fight with matplotlib is warranted.

## Consequences

**Easier:**

- The refactor verification runs on any contemporary matplotlib
  install without environment-version pinning.
- Future refactors of the predecessor (if any) inherit the same
  cheap regression guard without infrastructure work.
- The on-disk reference SVGs at
  [`docs/builders/wiring/<target>/main-circuit.svg`](../../builders/wiring/)
  remain meaningful archival records of the AwesomeStudioPedal-era
  output.

**Harder:**

- A change to matplotlib that affects glyph geometry (different font
  metrics, different stroke ordering) would slip past the
  normalisation. We accept this — the schematic content is what we
  guard, not the SVG byte-stream the renderer chooses to emit. If
  this turns out to be a real risk before EPIC-002 lands, the test
  can pin the matplotlib minor version with a one-line dep change.

## See also

- [TASK-006](../tasks/closed/task-006-refactor-generate-schematic-to-use-library.md)
  — the task whose AC this implements.
- [`tests/test_generator_byte_identity.py`](../../../tests/test_generator_byte_identity.py)
  — the implementing test.
- [ADR-0010](0010-mcu-profile-is-dev-board-shape.md) — sets up the
  profile structure that the refactor consumes.
