---
id: TASK-136
title: Walk the IDEA-001 YAML-format dossier against the shipped circuit.schema.json
status: open
opened: 2026-05-15
effort: Medium (2-8h)
complexity: Medium
human-in-loop: No
epic: dossier-gap-analysis
order: 3
prerequisites: [TASK-134]
---

## Description

Walk
[`idea-001.yaml-format.md`](../../ideas/archived/idea-001.yaml-format.md)
against the shipped schema at
[`src/circuitsmith/schema/circuit.schema.json`](../../../../src/circuitsmith/schema/circuit.schema.json).
The dossier's vocabulary is the ancestor of the shipped schema, not
the source of truth — flag every field that shipped under a
different name.

For each schema construct named in the dossier, write one row into
the **YAML format** sub-table of
`docs/developers/_dossier-gap-analysis.md`:

- **Top-level keys** — `circuit`, `components`, `connections`,
  `meta` (and any others the dossier names). For each: shipped /
  shipped-with-renamed-key / not-shipped.
- **Component-block fields** — `type`, `ref`, `label`, `value`,
  `meta`, `inputs`/`outputs`, etc. Cross-reference EPIC-014's
  frozen-decisions table: the dossier's `inputs:`/`outputs:`
  pin-alias form was explicitly **not** shipped (a sub-block-only
  port-naming convention won). Bucket 2 with verdict + ADR-link.
- **Connection grammar** — net authoring rules, the
  `pin: ref.port` syntax, any of the dossier's connection shapes
  that drifted at implementation.
- **Sub-blocks (post-EPIC-014).** Dossier's original sketch
  pre-dates the EPIC-014 first-class `sub-blocks:` / `instances:`
  schema. Cross-reference the archived
  [IDEA-008](../../ideas/archived/idea-008-first-class-sub-blocks-and-non-led-kernel-rules.md)
  before spawning anything new here — the sub-block work already
  landed, so most rows in this section will be bucket-1 with a
  link to EPIC-014.
- **`meta:` block keys** — `erc.severity-overrides`,
  `erc.cross-page-threshold`, any others the dossier names.

For each row, **read the schema JSON itself** (not just docs) to
confirm the shipped contract. If a field's `description` in the
schema differs from the dossier's wording, prefer the schema as
source of truth — the dossier is rationale, not contract.

## Acceptance Criteria

- [ ] One analysis row per dossier-named schema construct;
      bucket assigned.
- [ ] Rows that shipped under a renamed field carry the rename in
      the verdict column (dossier-name → shipped-name).
- [ ] Sub-block rows link to EPIC-014 TASK-115..119 rather than
      re-deriving the contract.
- [ ] The dossier's `inputs:`/`outputs:` pin-alias form is recorded
      as bucket 2 (not shipped, sub-block ports won instead).
- [ ] Any bucket-4 row has a spawned IDEA-NNN file linked from the
      verdict.

## Test Plan

No automated tests required — change is documentation / analysis.

Manual verification:

1. Open `circuit.schema.json` and confirm every top-level
   `properties.*` key is mentioned in at least one row of the YAML
   sub-table.
2. Spot-check three random schema constructs: the verdict column
   matches what the JSON actually constrains.

## Notes

- The dossier predates the EPIC-014 sub-block landing, so this walk
  is the most likely place to surface "dossier-says-A,
  shipped-as-B" rename rows. The renames aren't bucket-4 candidates
  unless they actually broke something — most are just rename-only
  bucket-2 notes.
- The `meta.erc.*` keys are the place to confirm whether the
  dossier's "ERC severity tunable" promise actually shipped or was
  partially deferred. Severity overrides shipped per EPIC-003;
  cross-page-threshold shipped per EPIC-014's TASK-127.
