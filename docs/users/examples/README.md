# Example gallery

Worked `.circuit.yml` projects, each ready to read cold. Every entry
in the table below points at its own subdirectory containing the
input YAML, the layout sidecar, the meta sidecar, the rendered SVG,
the generated BOM, and a short README explaining what makes the
example worth studying.

## Gallery

| Example | What it demonstrates | Source |
|---|---|---|
| [Voltage divider](voltage-divider/) | The smallest practical circuit; reference for two-component net basics. | [TASK-096](../../developers/tasks/open/task-096-example-voltage-divider.md) |
| [Common-emitter amplifier](common-emitter-amplifier/) | A small-signal BJT amplifier — biasing, coupling, and gain. | [TASK-097](../../developers/tasks/open/task-097-example-common-emitter-amplifier.md) |
| [555 monostable](555-monostable/) | One-shot timer using the 555 in monostable mode; introduces IC profiles. | [TASK-098](../../developers/tasks/open/task-098-example-555-monostable.md) |
| [Op-amp non-inverting buffer](opamp-non-inverting-buffer/) | Unity-gain buffer with feedback path; introduces op-amp pin conventions. | [TASK-099](../../developers/tasks/open/task-099-example-opamp-non-inverting-buffer.md) |
| [Multi-page split](multi-page-split/) | A circuit large enough to span multiple sheet pages — exercises the renderer's page-break logic. | [TASK-100](../../developers/tasks/open/task-100-example-multi-page-split.md) |

## How to use the gallery

- Each example's directory is self-contained. Copy it elsewhere,
  open the `.circuit.yml`, and run the pipeline — the output should
  match the committed SVG byte-for-byte.
- The gallery doubles as a regression net. CI re-renders every
  example on every PR and fails the build on drift, per
  [TASK-101](../../developers/tasks/closed/task-101-ci-regression-diff-for-gallery.md).

## CI regression guard

The script
[`scripts/check_gallery_regression.py`](../../../scripts/check_gallery_regression.py)
walks this directory plus `../tutorial/`, re-runs the renderer
against every committed `*.circuit.yml`, and diffs the output
against the committed `*.svg` / `*.layout.yml` / `*.meta.yml` /
`*.erc-report.md`. CI invokes it on every PR; locally, run it the
same way:

```bash
python scripts/check_gallery_regression.py            # check-only
python scripts/check_gallery_regression.py --rebaseline   # overwrite committed artefacts
```

Gallery entries that ship without a committed SVG (the entries
blocked on
[IDEA-008](../../developers/ideas/open/idea-008-first-class-sub-blocks-and-non-led-kernel-rules.md)
or
[IDEA-009](../../developers/ideas/open/idea-009-active-device-profiles-and-multi-page-renderer.md))
are skipped with a one-line note; the guard activates for each
example as soon as its prerequisites land and an SVG is committed.

## See also

- [Tutorial](../tutorial/) — if you want a guided walkthrough rather
  than a finished circuit to read.
- [`circuit-yaml.md`](../../developers/circuit-yaml.md) —
  authoritative format reference.

> Status: example content is filled in across TASK-096 through
> TASK-100 of EPIC-012. Until those land, the example
> sub-directories are placeholders.
