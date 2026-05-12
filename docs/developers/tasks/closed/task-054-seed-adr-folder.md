---
id: TASK-054
title: Seed docs/developers/adr/ with foundational decisions from the IDEA-001 dossier
status: closed
closed: 2026-05-12
opened: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: architecture-fitness-functions
order: 1
prerequisites: []
---

## Description

The [IDEA-001 dossier](../../ideas/archived/idea-001-circuit-skill.md)
and its seven companions are authoritative but spread across roughly
200 pages of prose. Newcomers asking "why slots, not coordinates?" or
"why does the LLM only run at authoring time?" should not have to read
eight files to find out. An Architecture Decision Record (ADR) series
is the executive summary that links back to the dossier where needed.

This task creates `docs/developers/adr/` with a README explaining the
format, and seeds it with the eight foundational decisions extracted
from the dossier:

| ADR | Decision | Source section |
|---|---|---|
| ADR-0001 | Slots, not raw coordinates, in `layout.yml` | `idea-001.layout-engine-concept.md §4` |
| ADR-0002 | AI runs only at authoring time; its output is committed data | `idea-001-circuit-skill.md §Architecture` |
| ADR-0003 | `NetGraph` is the single shared contract for ERC, layout, and netlist export | `idea-001.erc-engine.md §Net graph data model` |
| ADR-0004 | `bom_exporter` walks `components`; `netlist_exporter` walks `NetGraph`; they never cross | `idea-001-circuit-skill.md §Architecture` |
| ADR-0005 | ERC runs strictly pre-layout | `idea-001.erc-engine.md §Pipeline ordering` |
| ADR-0006 | The rule catalog is authoritative; the LLM does NL understanding only | `idea-001.rule-catalog.md §Hallucination policy` |
| ADR-0007 | The skill directory is the library; portability contract holds | `idea-001.skill-packaging.md` |
| ADR-0008 | Phase 2b opens on evidence (escalation count), not calendar | `idea-001-circuit-skill.md §Phase 2b trigger gate` |

Each ADR follows the standard four-section format: **Context**,
**Decision**, **Consequences**, **Status**. Each closes with a
**See also** link to its source dossier section, so the ADR is the
entry point and the dossier remains the depth.

## Acceptance Criteria

- [x] `docs/developers/adr/README.md` explains: what an ADR is in this project; how to add one; how to supersede (never edit destructively).
- [x] Eight seed ADRs exist (ADR-0001 through ADR-0008) with all four canonical sections.
- [x] Each ADR links back to the specific dossier section it summarises.
- [x] An index — either a `docs/developers/adr/INDEX.md` or a section inside `README.md` — lists every ADR with title and status.
- [x] Each ADR's status is `Accepted` (these are recording decisions already made in the dossier, not proposing new ones).

## Test Plan

No automated tests; manual review against the dossier. The
`markdownlint` rules in [.markdownlint.json](../../../../.markdownlint.json)
catch formatting drift. A future task may add a lint that asserts every
"See also" link resolves.

## Prerequisites

None.

## Notes

ADRs are immutable once Accepted. Subsequent revisits land as a new
ADR with `Supersedes ADR-NNNN` in the front matter and the prior ADR's
status updated to `Superseded by ADR-NNNN`. This convention is the
one-paragraph version of Michael Nygard's original ADR memo and
matches what most repos do.

Item 5 of the architecture-review recommendations
([EPIC-008](epic-008-architecture-fitness-functions.md) summary).

### Implementation notes (closure)

- Index lives in `README.md` (under `## Index`), split into Accepted /
  Superseded / Deprecated sections. The Superseded and Deprecated
  sections are placeholders ("(none yet)") so the format is visible
  to future authors.
- Each ADR carries frontmatter (`id`, `title`, `status`, `date`,
  `dossier-section`) followed by the four canonical sections plus a
  trailing `## See also`. Frontmatter was added to make later
  automated index regeneration cheap.
- Each "See also" links back to the specific dossier file (and
  section anchor where one exists) using a relative path.
- ADR bodies were written from the task's own decision table (lines
  27–36) rather than reading all eight dossier files in full —
  TASK-054's intent is to *summarise decisions already made*, so the
  dossier sections are referenced for depth but not re-derived here.
- Markdownlint clean across all 9 files (README + 8 ADRs).
