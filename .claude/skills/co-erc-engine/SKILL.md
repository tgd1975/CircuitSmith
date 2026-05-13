---
name: co-erc-engine
description: Code-owner reminder for src/circuitsmith/erc_engine.py — invariants surfaced before edit
---

# co-erc-engine

Surfaces the invariants `erc_engine.py` is expected to preserve
before an edit lands. Bound by
[`.claude/codeowners.yaml`](../../codeowners.yaml).

Authoritative source:
[`docs/developers/ideas/archived/idea-001.erc-engine.md`](../../../docs/developers/ideas/archived/idea-001.erc-engine.md).
See also [ADR-0005](../../../docs/developers/adr/0005-erc-pre-layout.md)
and [ADR-0006](../../../docs/developers/adr/0006-rule-catalog-authoritative.md).

## Invariants (checklist, not prose)

- [ ] **ERC runs strictly pre-layout.** Pipeline order is
      `.circuit.yml → NetGraph → ERC → layout → renderer / exporters`
      (ADR-0005). Anything that depends on placement (crosstalk
      estimates, physical-proximity rules) does **not** belong here.
- [ ] **Public check IDs are stable.** S1–S5 structural and E1–E10
      electrical are the public contract that documentation,
      reports, and downstream consumers rely on. Renumbering or
      reusing an ID is a breaking change. Reserve a new ID for new
      checks; deprecate (don't delete) retired ones.
- [ ] **Every check maps to the rule catalog.** Each ERC predicate
      has a matching `id` in `knowledge/rules.json`. Adding a check
      without a catalog entry breaks the
      catalog-is-authoritative invariant (ADR-0006). Removing a
      catalog entry without retiring its check breaks the same way.
- [ ] **Structural and electrical predicates stay segregated.**
      The two tables live in separate modules / dicts and do not
      call each other. Mixing them produces a check whose origin is
      unclear, and the rule-catalog audit gets noisier with each
      cross-call.
- [ ] **No LLM in the check path.** `erc_engine.py` is pure Python.
      No prompts, no API calls, no NL parsing at runtime. The LLM's
      job ended at authoring time (ADR-0002); ERC findings come
      from the catalog (ADR-0006).
- [ ] **Read-only consumption of `NetGraph`.** `erc_engine.py`
      consumes the graph without mutating it (see
      [`co-netgraph`](../co-netgraph/SKILL.md)).
- [ ] **Portability contract holds.** No host-project paths,
      `scripts.*` imports, or `CircuitSmith` references (ADR-0012,
      supersedes ADR-0007; TASK-051).

## Authority

[`idea-001.erc-engine.md`](../../../docs/developers/ideas/archived/idea-001.erc-engine.md) —
ERC engine design, check taxonomy, rule-catalog contract.

## Downstream consumers

A breaking change here affects:

- The release pipeline — ERC failures halt the pipeline before
  layout (ADR-0005). Renumbering checks breaks any CI gate that
  greps for specific IDs.
- The rule catalog (`knowledge/rules.json`) — adding/removing
  checks requires a paired catalog edit.
- The ERC-report renderer (TASK-028) — relies on the public S/E
  numbering for stable section headings.
- The Phase 2b trigger gate (`check_phase2b_trigger.py` —
  TASK-058) — counts escalations keyed by check ID.
