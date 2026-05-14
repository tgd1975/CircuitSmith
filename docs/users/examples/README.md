# Example gallery

Worked `.circuit.yml` projects, each ready to read cold. Every entry
in the table below points at its own subdirectory containing the
input YAML, the layout sidecar, the meta sidecar, the rendered SVG,
the generated BOM, and a short README explaining what makes the
example worth studying.

## Gallery

| Example | What it demonstrates | Source |
|---|---|---|
| [Voltage divider](voltage-divider/) | The smallest practical circuit; reference for two-component net basics. | [TASK-128](../../developers/tasks/closed/task-128-gallery-reattempt-voltage-divider.md) |
| [Common-emitter amplifier](common-emitter-amplifier/) | A small-signal BJT amplifier — biasing, coupling, and gain. | [TASK-129](../../developers/tasks/closed/task-129-gallery-reattempt-common-emitter-amplifier.md) |
| [555 monostable](555-monostable/) | One-shot timer using the 555 in monostable mode; introduces multi-pin IC profiles. | [TASK-130](../../developers/tasks/closed/task-130-gallery-reattempt-555-monostable.md) |
| [Op-amp non-inverting buffer](opamp-non-inverting-buffer/) | Unity-gain buffer with feedback path; introduces op-amp pin conventions and dual-rail supply. | [TASK-131](../../developers/tasks/closed/task-131-gallery-reattempt-opamp-non-inverting-buffer.md) |
| [Multi-page split](multi-page-split/) | A circuit partitioned across two sheet pages — exercises the renderer's page-break logic and cross-page net-label glyphs. | [TASK-132](../../developers/tasks/closed/task-132-gallery-reattempt-multi-page-split.md) |

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

All five gallery entries ship with committed SVGs as of EPIC-014's
close. The guard checks every committed `<dirname>/<dirname>.svg`
(or `<dirname>/<dirname>-p<N>.svg` for multi-page entries) for
byte-identical regeneration; any drift fails CI. Entries without a
committed SVG (none today) would be silently skipped.

## See also

- [Tutorial](../tutorial/) — if you want a guided walkthrough rather
  than a finished circuit to read.
- [`circuit-yaml.md`](../../developers/circuit-yaml.md) —
  authoritative format reference.
