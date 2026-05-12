---
id: ADR-0006
title: The rule catalog is authoritative; the LLM does NL understanding only
status: Accepted
date: 2026-05-12
dossier-section: idea-001.rule-catalog.md §Hallucination policy
---

## Context

ERC needs to know *what to check*. Two extremes:

- **LLM-as-checker** — Claude reads `.circuit.yml` and reports "the
  3V3 rail looks underdecoupled, you should add a 10 µF cap". Easy
  to prototype; impossible to audit; the rule fired today may not
  fire tomorrow. Hallucinations are indistinguishable from genuine
  rules and the false-positive cost is high (the engineer learns to
  ignore output).
- **Hand-coded catalog** — every rule is a function in Python with
  an `id`, a docstring, and a test. No LLM in the check path.
  Auditable; rules ship with the repo; new rules are PR-reviewable.

Neither extreme is workable on its own: the LLM-only path drifts;
the hand-coded path is bad at *understanding what the engineer meant*
when their description is ambiguous.

## Decision

The **rule catalog is authoritative**. Every ERC rule is a Python
predicate in `knowledge/rules.json` (the catalog) backed by a
function in `erc_engine.py`. Rules have stable IDs (S1–S5
structural, E1–E10 electrical) that form the public contract.

The LLM's job is restricted to **natural-language understanding at
authoring time**: translating a human description into a
`.circuit.yml` that the catalog can check. Once the YAML lands, the
catalog is the only voice that fires ERC findings. The LLM never
invents a rule, never silently relaxes a rule, and never adds a
finding outside the catalog.

If an engineer's prose mentions a constraint the catalog cannot
express, the skill either asks for clarification (and the human
chooses how to encode it) or records the constraint as a free-text
note on the relevant component — not as an ERC finding.

## Consequences

**Easier:**

- Every ERC finding has a stable ID, a reproducible source, and a
  test. Reading a CI failure is "rule E7 fired" not "the AI thinks
  this might be a problem".
- New rules go through a normal PR review with a test fixture,
  exactly the same as any other code change.
- Audit trails are clean: a CI failure five years from now can be
  reproduced by reading the catalog at that commit.

**Harder:**

- A genuinely novel pattern the engineer wants to flag has to be
  formalised as a catalog rule before it can fire. The "let me just
  ask Claude" shortcut is closed.
- The catalog's coverage is the floor of what ERC can find.
  Anything outside it passes silently; the catalog has to be
  curated proactively, not retroactively.

## See also

[`idea-001.rule-catalog.md §Hallucination policy`](../ideas/archived/idea-001.rule-catalog.md)
for the full hallucination policy and the catalog format.
