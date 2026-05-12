# Architecture Decision Records

This folder is the decision log for CircuitSmith. Each file is one
record of one decision: why it was taken, what it commits us to, and
what it costs.

## What an ADR is in this project

An ADR (Architecture Decision Record) is a **short, immutable note**
describing a single architectural decision and its rationale, in the
four-section format popularised by Michael Nygard's
[original 2011 memo](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
The format here is intentionally minimal:

- **Context** — the constraint, problem, or trade-off the decision
  addresses. Two or three sentences.
- **Decision** — what was decided. One declarative paragraph.
- **Consequences** — what this commits us to (pro and con), and which
  downstream things become easier or harder.
- **Status** — `Accepted`, `Superseded by ADR-NNNN`, or `Deprecated`.
- **See also** — a link to the dossier section that owns the depth.

The dossier
([`docs/developers/ideas/archived/idea-001-*.md`](../ideas/archived/))
remains authoritative for the *details* of every decision. ADRs are
the **index**: read the ADR to understand which constraints are
load-bearing; follow the link to the dossier when you need the full
argument.

## How to add an ADR

1. Pick the next free number (`docs/developers/adr/` files are named
   `NNNN-<kebab-case-summary>.md`).
2. Copy [`0000-template.md`](0000-template.md) — the maintained
   blank ADR — and fill in each section. (Alternatively, copy the
   structure of an existing accepted ADR.)
3. Frontmatter: `id`, `title`, `status`, `date` (ISO-8601), `dossier-section` (path + anchor when applicable).
4. Append a line to the index in this file under the matching section.
5. Run `/commit` per the project's commit policy.

## How to supersede an ADR

ADRs are immutable once `Accepted`. A revisit lands as a **new** ADR.
The new ADR's frontmatter carries `supersedes: ADR-NNNN`; the prior
ADR's status is updated to `Superseded by ADR-NNNN` (the only
permitted edit to an accepted ADR). Never edit the prior ADR's body —
the original reasoning stays as historical record.

## Index

### Accepted

| ADR | Title | Source |
|---|---|---|
| [0001](0001-slots-not-coordinates.md) | Slots, not raw coordinates, in `layout.yml` | `idea-001.layout-engine-concept.md §4` |
| [0002](0002-ai-only-at-authoring-time.md) | AI runs only at authoring time; output is committed data | `idea-001-circuit-skill.md §Architecture` |
| [0003](0003-netgraph-shared-contract.md) | `NetGraph` is the single shared contract for ERC, layout, and netlist export | `idea-001.erc-engine.md §Net graph data model` |
| [0004](0004-exporter-decoupling.md) | `bom_exporter` walks `components`; `netlist_exporter` walks `NetGraph`; they never cross | `idea-001-circuit-skill.md §Architecture` |
| [0005](0005-erc-pre-layout.md) | ERC runs strictly pre-layout | `idea-001.erc-engine.md §Pipeline ordering` |
| [0006](0006-rule-catalog-authoritative.md) | The rule catalog is authoritative; the LLM does NL understanding only | `idea-001.rule-catalog.md §Hallucination policy` |
| [0007](0007-skill-directory-is-the-library.md) | The skill directory is the library; portability contract holds | `idea-001.skill-packaging.md` |
| [0008](0008-phase-2b-trigger-on-evidence.md) | Phase 2b opens on evidence (escalation count), not calendar | `idea-001-circuit-skill.md §Phase 2b trigger gate` |
| [0009](0009-autonomous-implementation-mode.md) | Autonomous-implementation mode — protocol + driver skill | `docs/developers/AUTONOMY.md` |
| [0010](0010-mcu-profile-is-dev-board-shape.md) | MCU profiles describe the dev-board pinout, with silicon metadata at the chip level | `idea-001.components.md` |
| [0011](0011-content-identity-not-byte-identity.md) | SVG regression test uses content-identity (matplotlib non-determinism normalised), not literal byte-identity | TASK-006 |

### Superseded

(none yet)

### Deprecated

(none yet)
