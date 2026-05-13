---
id: TASK-021
title: Update docs/layout.md with AI-placer invocation and cost notes
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-renderer-layout
order: 14
prerequisites: [TASK-017, TASK-018, TASK-019, TASK-020]
---

## Description

Update `.claude/skills/circuit/docs/layout.md` to add the Phase 2b
sections that were structurally placeholdered in TASK-016:

- AI-placer invocation: when it fires, what input it receives, what
  output to expect.
- Convergence behaviour: rounds, reason codes, fail-loud paths.
- Cost notes: per-run token cap, accounting via `meta.yml.provenance`.
- `--no-ai` flag: when to use it, what it suppresses.
- The promoted rubric checks (from TASK-019): threshold, rationale.

## Acceptance Criteria

- [x] All four AI-placer sections are added to `docs/layout.md`. _New "AI placer (Phase 2b)" section in [`.claude/skills/circuit/docs/layout.md`](../../../.claude/skills/circuit/docs/layout.md) with sub-sections for Invocation, Input contract, Output contract, Convergence behaviour, Cost notes, `--no-ai` opt-out, and `meta.yml.provenance` fields. The earlier "Phase 2b flags (not in v0.1)" placeholder is replaced with a cheat sheet that points at the live sections._
- [x] A contributor can opt out of AI placer usage purely from this doc. _The `--no-ai` section explains the default-off behaviour, the explicit form, and the ADR-0002 hermetic-CI rationale; the Invocation block gives the copy-pasteable CLI._
- [x] Cost expectations are quantified ("typical run: N tokens; cap: M tokens"). _Cost notes section: iteration cap 5, token cap `DEFAULT_TOKEN_CAP = 50_000`, typical converged run "1–2 LLM calls, ~1–3k input + ~200–500 output tokens per call"; cumulative accounting tracked via `meta.yml.provenance.ai_invocations[].{input_tokens, output_tokens}`._
- [x] The doc cross-references `idea-001.layout-engine-concept.md §7` for design rationale. _The new section opens with a link to `idea-001.layout-engine-concept.md §7` and `ADR-0008`; the `meta.yml.provenance` table links to `meta.schema.json` as the machine-readable contract._

## Implementation notes

The TASK-019 promoted-rubric-checks were already covered in the
rubric table during TASK-019 itself, so this task focused on the
four AI-placer sub-sections plus the `--no-ai` cheat-sheet. The
"v0.1 known limitations" block at the bottom of the doc stays
accurate — the AI placer is now available, but `--reflow` and the
post-v1 router/glyph enhancements are not.

EPIC-002 is now fully closed: 16 of 16 in-scope tasks done.

## Test Plan

No automated tests required — documentation deliverable. Verify cross-references resolve.

## Prerequisites

- **TASK-017** — AI placer behaviour to document.
- **TASK-018** — `--no-ai` flag to document.
- **TASK-019** — promoted rubric checks to document.
- **TASK-020** — `meta.yml.provenance` fields to reference.

## Notes

This closes out EPIC-002 (Phase 2b half).
