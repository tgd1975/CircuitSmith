---
id: TASK-101
title: CI regression diff — regenerate the tutorial and gallery, fail on drift
status: closed
opened: 2026-05-13
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
epic: tutorial-and-examples
order: 10
prerequisites: [TASK-094, TASK-095, TASK-096, TASK-097, TASK-098, TASK-099, TASK-100]
---

## Description

The tutorial steps and gallery examples commit their generated
artefacts (`layout.yml`, `meta.yml`, SVG) so the docs render
correctly without a CI build step. That commitment also doubles as
a regression net: a CI job re-runs the skill against every committed
`.circuit.yml` and fails the build if any generated artefact drifts
from what's checked in.

Implementation shape:

- New script `scripts/check_gallery_regression.py`.
- Walks `docs/users/tutorial/` and `docs/users/examples/` for
  `*.circuit.yml`.
- For each, runs the skill (or its programmatic entry point —
  prefer the latter so the script does not depend on the
  Claude-skill harness) and diffs the output against the committed
  artefacts.
- Failure modes:
  - **Output differs from committed** → exit non-zero with the
    file path and a `diff -u` of the changed file(s).
  - **`.circuit.yml` cannot be parsed** → exit non-zero.
  - **Skill / renderer errors** → exit non-zero with the renderer's
    error surfaced verbatim.
- Wired into the same CI workflow as the erc-report staleness check
  and the test-plan staleness check (TASK-091).

Local-dev integration:

- Add `Bash(python scripts/check_gallery_regression.py:*)` to
  `.claude/settings.json` allow list.
- The script must run cleanly from the project root.

Renderer drift tolerance:

- **Default: byte-exact.** Any difference is a regression.
- **Configurable allowance**: a small set of "known acceptable
  drift" classes (font metric changes from a Schemdraw bump, for
  example) gets a CLI flag (`--allow-drift=font`). Disabled by
  default; only set by the contributor opening the PR that
  intentionally re-baselines.
- The renderer chapter (TASK-087) documents the drift-tolerance
  policy; this script enforces it.

Re-baselining workflow:

- Contributor runs the script locally with `--rebaseline` flag,
  which writes the new artefacts in place of the committed ones.
- They review the diff, commit if intended, push.
- CI then sees no drift and passes.

## Acceptance Criteria

- [x] `scripts/check_gallery_regression.py` exists, is executable,
      and exits 0 on the current repo state.
- [x] The script supports both check-only and `--rebaseline` modes.
- [x] CI runs the check on every PR. (New step added to `ci.yml`
      between the existing exporter staleness gate and the catalog
      validation step; scoped to `ubuntu-latest` like its
      neighbours.)
- [x] `.claude/settings.json` allow list updated. (Added
      `Bash(python scripts/check_gallery_regression.py:*)` to the
      script-allow block.)
- [x] `scripts/README.md` updated. (Regenerated via
      `scripts/update_scripts_readme.py`; the script row appears
      under the existing `check_*` cluster.)
- [~] The drift-tolerance policy documented. **Partial — a short
      prose section is in the script's module docstring (visible
      via `--help`'s description argument inheritance). The
      renderer-chapter matrix (TASK-087, EPIC-011) is the
      authoritative drift-tolerance home; cross-link added there
      will follow when TASK-087 lands.**

## Outcome

The CI regression guard is live: every push and pull request runs
[`scripts/check_gallery_regression.py`](../../../scripts/check_gallery_regression.py)
on `ubuntu-latest`, re-rendering every committed
`*.circuit.yml` under `docs/users/{tutorial,examples}/` and
diffing the four artefact kinds (`.svg`, `.layout.yml`,
`.meta.yml`, `.erc-report.md`) against the committed copies. Drift
exits non-zero with a unified diff per affected file; the
`--rebaseline` flag overwrites the committed artefacts when the
drift is intentional.

Implementation choices worth recording:

- **The script walks the file tree, not a hard-coded target
  list.** Mirrors EPIC-012's "one example per directory" gallery
  shape rather than the `data/<target>/` shape that
  `regenerate_circuit_artefacts.py` walks.
- **`REPO_ROOT` is derived from `cwd` when the expected
  `docs/users/` shape is present.** Lets the test suite stage a
  temp gallery and exercise the script end-to-end via
  `subprocess.run` without monkey-patching paths. The script also
  works correctly from the real repo root via the script-anchored
  fallback.
- **The `meta.yml` diff normalises the `sources:` block.** The
  renderer records its input/output paths verbatim, which would
  otherwise produce a false-positive diff every run from a
  different invocation directory. The normaliser strips the
  block before comparing; the rest of `meta.yml` (rubric scores,
  provenance, escalations) is compared as-is.
- **Circuits without a committed SVG are skipped.** EPIC-012
  closed five gallery entries (TASK-096..100) as
  blocked-on-IDEA-008/009 with no committed SVG; the guard prints
  one skip line per entry and exits 0. The guard auto-activates
  for each entry as soon as its prerequisites land and an SVG is
  committed.
- **Tests live in
  [`tests/test_check_gallery_regression.py`](../../../tests/test_check_gallery_regression.py).**
  Five tests cover the four task-body scenarios (clean / drifted
  / rebaselined / skipped) plus an empty-gallery sanity case.

Documentation hooks:

- [`scripts/README.md`](../../../scripts/README.md) regenerated.
- [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml)
  — new "Tutorial + gallery regression gate" step.
- [`docs/developers/CI_PIPELINE.md`](../CI_PIPELINE.md) — new row
  in the steps-in-order table for the `ci.yml` workflow.
- [`docs/users/examples/README.md`](../../users/examples/README.md)
  — new "CI regression guard" section near the bottom, naming
  the script and the local-reproduction command.

## Test Plan

**Host tests**:

- `tests/test_check_gallery_regression.py`:
  - Construct a temp gallery with one example whose committed SVG
    matches the regenerated SVG. Expect exit 0.
  - Construct a temp gallery where the SVG drifts. Expect exit
    non-zero and the diff in stderr.
  - Construct a temp gallery with `--rebaseline`: confirm the
    committed artefacts get rewritten and the script then exits 0
    on the second run.

Manual verification:

1. Run the script against the current repo state; exit 0 after
   all TASK-094 through TASK-100 close.
2. Edit one example's `circuit.yml` so the SVG would drift; run
   the script; confirm the failure surfaces the affected file.
3. Run with `--rebaseline`; confirm the artefacts update and the
   subsequent check passes.

## Prerequisites

- **TASK-094, TASK-095** — tutorial steps must exist for the
  script to find their committed artefacts.
- **TASK-096 through TASK-100** — gallery examples must exist.

## Documentation

- `scripts/README.md` — add the new script row.
- `docs/users/examples/README.md` — add a short "CI regression
  guard" paragraph at the bottom.
- `docs/developers/CI_PIPELINE.md` — add the new gate to the
  required-checks inventory.
- `docs/developers/testing/renderer.md` (TASK-087) — already
  documents the drift-tolerance policy; this script enforces it.
  Cross-link.

## Notes

- Coordinate naming with TASK-091 (test-plan staleness check) so
  the CI dashboard shows the related guards adjacent rather than
  scattered. Suggested names: `check-test-plan` and
  `check-gallery`.
- The programmatic entry point preference (not running through the
  full skill harness) is important. The CI job must not depend on
  Claude or any LLM — it's a pure regenerate-and-diff over the
  deterministic pipeline. If the renderer pipeline currently
  *requires* an LLM call (e.g. for AI-placer steps), the
  `--no-ai` fallback from TASK-018 must be honoured.
- Don't try to share parsing code with TASK-091's plan-staleness
  script. They walk different file trees with different shapes;
  one combined script would over-couple.
