---
id: TASK-036
title: Implement Markdown ```circuit block rewrite (workflow or superfences formatter)
status: open
opened: 2026-05-12
effort: Medium (2-8h)
complexity: Senior
human-in-loop: No
epic: circuit-markdown-integration
order: 1
prerequisites: [TASK-012]
---

## Autonomy

`Clarification` → `No` per TASK-060 sweep. Markdown block syntax
has a defensible default (mkdocs superfences-style); file an ADR
for any edge-case parsing decision rather than pausing.

## Description

Implement the ` ```circuit ` Markdown block rewrite. The block holds a
`.circuit.yml` snippet; on build, the snippet renders to SVG and the
block is replaced (or wrapped) by an image embed. The SVG filename
includes a hash of the source for staleness detection.

**Ordering with IDEA-022 (MkDocs).** Per `idea-001-circuit-skill.md
§Phase 5`:

- If IDEA-022 has landed, implement as a `pymdownx.superfences`
  custom formatter that runs at MkDocs build time.
- If this epic ships first, implement as a GitHub Actions workflow
  (`.github/workflows/generate-circuits.yml`) that rewrites blocks on
  push. The workflow retires when IDEA-022 lands.

The block contract is identical in both implementations — only the
build-time mechanism differs.

## Acceptance Criteria

- [ ] A Markdown file containing a ` ```circuit ` block renders to a page with the embedded SVG.
- [ ] SVG filename includes an 8-char hex hash of the source YAML.
- [ ] Stale SVGs (hash mismatch) are detected and regenerated (or the build fails on staleness in CI).
- [ ] Implementation matches whichever mechanism is current per the IDEA-022 ordering.

## Test Plan

Add `tests/test_markdown_block.py` (host) covering: block-to-image rewrite produces the expected file path, hash determinism across two builds, stale-hash detection fires when expected.

## Prerequisites

- **TASK-012** — the renderer must exist to be invoked from the block formatter.

## Notes

Whichever mechanism is shipped first, document the swap procedure in
`docs/index.md` so the future transition is mechanical.

## Predecessor source

[IDEA-022 (MkDocs site)](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-022-mkdocs-documentation-site.md)
is an AwesomeStudioPedal idea — its landing status is tracked there. The
"IDEA-022 ordering" branch in this task keys on whichever site framework
the consumer project (AwesomeStudioPedal or another) is running.
