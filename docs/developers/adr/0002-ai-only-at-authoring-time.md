---
id: ADR-0002
title: AI runs only at authoring time; output is committed data
status: Accepted
date: 2026-05-12
dossier-section: idea-001-circuit-skill.md §Architecture
---

## Context

CircuitSmith uses an LLM (Claude) to translate natural-language
component descriptions into structured `.circuit.yml`. Two ways to
wire that in:

- **Runtime AI** — the renderer / ERC / exporters invoke the LLM at
  each invocation. Output may drift between runs; reproducing a build
  requires reproducing the LLM call (with all its temperature,
  version, and prompt-context entropy).
- **Authoring-time AI** — the LLM produces `.circuit.yml` once, the
  output is committed to git, and from that point onward only
  deterministic Python touches it.

Determinism is a hard requirement for circuit design: a BOM that
shifts between renders is a manufacturing defect. CI gates and
golden-hash contract tests (TASK-053) rely on byte-stable artefacts.

## Decision

The LLM runs **only at authoring time**, when a human invokes the
skill to translate a description into `.circuit.yml`. Its output is
committed as a file in the repository. All downstream stages —
renderer, ERC engine, BOM exporter, netlist exporter, markdown
integration — are pure Python and do not call any LLM.

If LLM output is unsatisfactory, the human re-invokes the skill and
commits a corrected file. The diff between the old and new
`.circuit.yml` is the audit trail.

## Consequences

**Easier:**

- Reproducibility is a property of the repository, not of the
  environment. Anyone who clones the repo gets the same renders,
  netlists, and BOMs as the author.
- Determinism gates (golden-hash tests, ERC stability checks) are
  trivially enforceable.
- LLM cost is bounded by authoring frequency, not by build
  frequency.

**Harder:**

- `.circuit.yml` is a permanent artefact; bad LLM output that lands
  has to be cleaned up explicitly rather than self-correcting on
  the next build.
- No "live" features that adapt at render time (e.g. an LLM
  rationale for an ERC escalation). Such features have to be
  authored once and committed, then merely retrieved at render time.

## See also

[`idea-001-circuit-skill.md §Architecture`](../ideas/archived/idea-001-circuit-skill.md)
for the full pipeline diagram and the authoring vs. build split.
