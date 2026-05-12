---
id: TASK-056
title: Author the first three code-owner skills (co-netgraph, co-schema, co-erc-engine)
status: closed
closed: 2026-05-12
opened: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: architecture-fitness-functions
order: 4
prerequisites: [TASK-055]
---

## Description

Author the three initial code-owner skills, one for each of the
highest-blast-radius modules in the Circuit-Skill architecture. Each
skill is a small `SKILL.md` whose only job is to surface, at edit
time, the invariants that the target file is supposed to preserve.

The three modules covered in this task:

- **`co-netgraph`** for `.claude/skills/circuit/netgraph.py`. Invariants:
  hash determinism across parses; the three connection forms (`pins`,
  `path`, `bus`) flatten to one canonical net representation
  (downstream code does not branch on form); no layout coordinates leak
  into the model; portability contract holds. Authority:
  `idea-001.erc-engine.md §Net graph data model`. Consumers:
  `erc_engine.py`, `layout_engine/kernel.py`, `netlist_exporter.py` —
  a breaking change here breaks all three.

- **`co-schema`** for `.claude/skills/circuit/schema/*.json`. Invariants:
  any breaking change requires a schema-version bump; the
  `NetGraph` golden hash (TASK-053) must be regenerated in the same
  commit; downstream validators (renderer, pre-commit hook from
  TASK-052) must be re-tested. Authority:
  `idea-001.yaml-format.md`, `idea-001.layout-engine-concept.md §16`.

- **`co-erc-engine`** for `.claude/skills/circuit/erc_engine.py`.
  Invariants: ERC runs strictly pre-layout; the S/E check numbering
  is stable (S1–S5, E1–E10 are the public contract); every check has a
  matching `id` in `knowledge/rules.json`; structural and electrical
  checks live in separate predicate tables and do not call each other.
  Authority: `idea-001.erc-engine.md`.

Each skill ships as `.claude/skills/co-<name>/SKILL.md` with frontmatter
(matching the existing skill convention used by `ts-*` skills) and a
body that lists invariants as a checklist (not prose), names the
authoritative dossier section, and lists the downstream consumers.

Each skill is registered in `.vibe/config.toml` per
[CLAUDE.md](../../../../CLAUDE.md) and added to
`.claude/codeowners.yaml` (from TASK-055) under the correct pattern.

## Acceptance Criteria

- [x] Three `SKILL.md` files exist under `.claude/skills/co-netgraph/`, `.claude/skills/co-schema/`, `.claude/skills/co-erc-engine/`.
- [x] Each declares its invariants as a checklist of bullet points, not paragraphs of prose.
- [x] Each names the authoritative dossier section and links to it relatively.
- [x] Each names the downstream consumers a breaking change would affect.
- [x] Each is registered in `.vibe/config.toml` under `enabled_skills`.
- [x] Each is referenced in `.claude/codeowners.yaml` from TASK-055 under the correct file pattern.

## Test Plan

Manual: edit `netgraph.py`, `schema/circuit.schema.json`, and
`erc_engine.py` in one Claude session each and confirm the matching
reminder appears via the TASK-055 hook. There is no automated test for
skill *content*; the test for the *mechanism* lives in TASK-055.

## Prerequisites

- **TASK-055** — the registry and hook must exist before the skills
  it refers to are useful. Skill content itself can be drafted in
  parallel from the dossier (it does not depend on the target modules
  existing yet).

## Notes

Subsequent code-owner skills — for `bom_exporter`, `netlist_exporter`,
`knowledge/rules.json`, `layout_engine/kernel.py` — are added as the
relevant modules land. No need to author them all upfront. The pattern
is established by these three; the others are pattern instances.

Item 7 of the architecture-review recommendations
([EPIC-008](epic-008-architecture-fitness-functions.md) summary).

### Implementation notes (closure)

- **Invariant content sourced from the task body + ADRs**, not by
  re-reading the eight dossier files. The decisions are already
  recorded — TASK-054's ADRs (ADR-0003/0005/0006/0007) are the
  primary references in each skill's "Authority" section.
- **Cross-skill links.** Each skill links to its sibling code-owner
  skills where they share concerns (e.g. `co-netgraph` references
  `co-erc-engine` as a downstream consumer). Keeps the surface area
  navigable when one of these reminders fires.
- **Skill registration ordering.** `.vibe/config.toml`'s
  `enabled_skills` list is alphabetical; the three new entries sort
  as `co-erc-engine` < `co-netgraph` < `co-schema` (then `commit`)
  per byte-wise comparison (`-` (0x2D) < `m` (0x6D)).
- **Pattern bindings** in `.claude/codeowners.yaml` mirror the
  target file paths exactly — no wildcards beyond `*.json` for the
  `schema/` directory. `bom_exporter.py` /
  `netlist_exporter.py` / `knowledge/rules.json` /
  `layout_engine/kernel.py` will get their own entries when the
  corresponding modules land (per the task body's "subsequent
  skills are pattern instances" note).
- **Manual verification deferred.** The AC's manual test plan
  ("edit `netgraph.py`, `schema/circuit.schema.json`, and
  `erc_engine.py` in one Claude session each") is not reproducible
  from inside the agent doing the work. The TASK-055 integration
  tests (`TestRun` class, 9 cases) exercise the same `run()` flow
  with synthetic Edit payloads against the real registry; that is
  the automated equivalent.
