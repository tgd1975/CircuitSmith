---
id: ADR-0013
title: Build-guide BOM embed is a link, not a literal include — until MkDocs lands
status: Accepted
date: 2026-05-13
dossier-section: idea-001.exporters.md §BOM Exporter
---

## Context

TASK-032 ("Embed BOM table in build guide") inherits the
`docs/builders/wiring/<target>/` convention from AwesomeStudioPedal,
where a parent build-guide Markdown page would include the BOM table
via `pymdownx.snippets` once MkDocs (AwesomeStudioPedal IDEA-022) is
in place. In this repo, the upstream parent build guides do not yet
exist — only the per-target generated artefacts (`bom.md`,
`bom.csv`, `erc-report.md`, `main-circuit.svg`) live here. Three
options:

1. Inline the BOM table content into a hand-maintained per-target
   build guide (risks drift; every renderer run would touch the
   parent page).
2. Wait for MkDocs to land before adding any per-target index
   (leaves the per-target folders without a human entry point).
3. Add a thin `README.md` per target that **links** to the
   generated artefacts; the BOM table itself stays in its own
   `bom.md` file, ready to be `pymdownx.snippets`-included once
   MkDocs arrives.

## Decision

Option 3. Each `docs/builders/wiring/<target>/` ships a small
`README.md` that links to the four generated artefacts (`bom.md`,
`bom.csv`, `erc-report.md`, `main-circuit.svg`). The BOM Markdown
table content stays in `bom.md` verbatim — that file *is* the
embeddable artefact, ready for a literal include the day a MkDocs
build guide page lands and replaces the README.

## Consequences

**Easier:**

- The renderer (and TASK-035's CI staleness guard) owns the BOM
  table content in exactly one place — `bom.md` — with no
  duplicated copy in a parent page.
- The MkDocs migration is a search-and-replace: replace each
  `README.md`'s artefact list with the appropriate
  `--8<-- "bom.md"` include directives.

**Harder:**

- GitHub's web view of `docs/builders/wiring/<target>/` shows the
  README's link-list rather than the BOM table inline. Readers
  click through one extra hop to see the parts list. This is
  judged acceptable for the v0.1 documentation surface; the build
  guide proper (with embedded tables) lands with MkDocs.

## See also

- [TASK-032](../tasks/closed/task-032-embed-bom-table-in-build-guide.md) — the task this resolves.
- `docs/developers/ideas/archived/idea-001.exporters.md` §BOM Exporter — `bom.md` format spec.
- AwesomeStudioPedal [IDEA-022](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-022-mkdocs-documentation-site.md) — the MkDocs migration whose landing flips this ADR's "until" clause.
