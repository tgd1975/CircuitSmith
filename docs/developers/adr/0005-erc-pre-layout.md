---
id: ADR-0005
title: ERC runs strictly pre-layout
status: Accepted
date: 2026-05-12
dossier-section: idea-001.erc-engine.md §Pipeline ordering
---

## Context

ERC (Electrical Rule Check) verifies invariants about the circuit's
*connectivity* — every input has a driver, no power short, no
unconnected required pin. Layout assigns physical positions and
routes nets between them.

Two orderings are possible:

- **ERC after layout** — natural if ERC is conceived as "final
  validation before manufacture". But layout failures (routing
  congestion, untraceable nets) then mask connectivity defects, and
  fixing an ERC error after layout often invalidates the placement.
- **ERC before layout** — connectivity is verified against the
  `NetGraph` directly; if ERC fails, layout never runs. The author
  fixes connectivity first and only then asks where the parts go.

The dossier's framing: connectivity defects are *modelling errors*,
placement decisions are *engineering choices*. Modelling errors
should fail loudly before any choice depends on them.

## Decision

ERC runs **strictly pre-layout**. The pipeline is:

```text
.circuit.yml → NetGraph → ERC → layout → renderer / exporters
                            └─ stops here on failure
```

`erc_engine.py` consumes `NetGraph` (per [ADR-0003](0003-netgraph-shared-contract.md))
and emits a pass/fail plus a list of findings keyed to the rule
catalog (S1–S5 structural, E1–E10 electrical). On failure the
pipeline halts; no SVG, BOM, or netlist is produced.

## Consequences

**Easier:**

- ERC findings are reported in terms of the model the author wrote,
  not in terms of placement decisions they did not make.
- Layout can assume a valid `NetGraph` and does not need its own
  defensive checks for unconnected pins or net collisions.
- The rendering / export stages are downstream of *two* gates
  (`.circuit.yml` schema validation in TASK-052, then ERC), which
  bounds the failure modes they have to handle.

**Harder:**

- ERC rules that depend on physical placement (e.g. crosstalk
  estimates, EMI proximity) cannot live here. They have to be a
  separate, post-layout stage if introduced later.
- A future "preview the layout even though ERC fails" debug mode
  has to be opt-in and explicitly marked as non-production.

## See also

[`idea-001.erc-engine.md §Pipeline ordering`](../ideas/archived/idea-001.erc-engine.md)
for the full pipeline diagram and the ERC rule taxonomy.
