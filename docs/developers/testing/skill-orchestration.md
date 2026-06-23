---
subsystem: skill-orchestration
covers: .claude/skills/circuit/ + src/circuitsmith/markdown.py
---

# Skill orchestration — test plan

This subsystem is where an LLM agent and deterministic code meet, so the
chapter's first job is to draw a hard line:

- **Out of scope — agent-prompt behaviour.** Whether the
  `.claude/skills/circuit/SKILL.md` system prompt makes Claude author
  good YAML is *not* test-pinnable and is deliberately untested. Model
  output is non-deterministic; asserting on it would produce a flaky,
  low-value suite.
- **In scope — deterministic post-processing.** Everything the skill
  hands to plain Python *is* pinnable: the Markdown ` ```circuit ` block
  rewriter ([`markdown.py`](../../../src/circuitsmith/markdown.py)), its
  content-hash, the image-embed rewrite, the `show_source` rendering, and
  the `--check` staleness mode. That is what this chapter covers.

Covers [`markdown.py`](../../../src/circuitsmith/markdown.py); the
`.claude/skills/circuit/` directory is covered for *portability* (no
host-project leaks) by the portability lint — see
[`ci-gates.md`](ci-gates.md).

Test files covering this subsystem:

```pytest
tests/test_markdown_block.py
```

## Inputs and outputs

- **Input** — a Markdown file containing ` ```circuit ` fenced blocks
  (optionally with a `show_source` flag).
- **Output** — the same file with each block rewritten to an image embed
  pointing at a hash-named SVG (`<doc>.circuits/<hash>.svg`), the SVG
  rendered on disk, and — under `show_source` — a `<details>` wrapper
  carrying the verbatim YAML. `main(["--check", …])` is the staleness
  gate.

## Unit tests

`tests/test_markdown_block.py` (TASK-036/037): `compute_hash` is
deterministic and 8 hex chars; `find_blocks` returns blocks in order
with the `show_source` flag parsed; `rewrite_markdown` produces an
`![circuit](<doc>.circuits/<hash>.svg)` embed and renders the SVG to
disk; the rewrite is idempotent (a second run finds no remaining raw
blocks); `--check` exits non-zero (code 2, `MISSING`) when a block's SVG
is absent and passes after a render; `show_source` wraps the embed in
`<details><summary>circuit source</summary>` with the verbatim YAML in a
fenced block, while its absence yields a plain embed.

## Integration tests

The rewriter invokes the full renderer to produce each block's SVG, so
`test_rewrite_produces_image_embed_with_hash_in_filename` is implicitly
an integration test across markdown → renderer. The dedicated renderer
coverage lives in [`renderer.md`](renderer.md).

## Golden / snapshot tests

**None as committed snapshots.** The content-hash *is* the snapshot
mechanism: a block's hash changes iff its source changes, and `--check`
fails when the on-disk SVG no longer matches the current hash. No golden
file is stored; the hash-named artefact is the source of truth.

## Property / fuzz tests

**None.** Block parsing is asserted on fixed Markdown fixtures.
Rationale: the parser is small and the fixtures cover the flag matrix;
malformed-Markdown fuzzing is low-value.

## Performance budget

**No budget.** Rewriting is dominated by the renderer calls it delegates
to; the rewriter's own work is negligible.

## Known uncovered cases

- **The agent prompt itself.** By design (see the scope boundary above)
  no test asserts the SKILL.md prompt produces correct YAML. Rationale:
  model output is non-deterministic and not a fixture target; this is a
  deliberate non-goal, not a gap to fill.
- **`show_source` round-trip re-render.** Tests confirm the `<details>`
  wrapper and verbatim YAML are emitted, but not that re-running
  `--check` on a `show_source` doc with a drifted SVG flags it.
  Rationale: the plain-embed `--check` path covers the staleness logic;
  the wrapper is presentation-only — a minor follow-up.
- **Multi-block docs with mixed flags.** `find_blocks` is tested with two
  blocks of differing flags, but `rewrite_markdown` end-to-end is tested
  on single-block docs. Rationale: the per-block logic is shared; a
  mixed-doc end-to-end fixture would be belt-and-braces.

## Cadence

| Test file | PR | Nightly | Release |
|---|:--:|:--:|:--:|
| `tests/test_markdown_block.py` | ✓ | | |

Runs at PR-time. Because the agent-behaviour half is out of scope, there
is no nightly LLM-evaluation tier — and adding one would be an
evaluation harness, not a test, so it would live outside this matrix.
