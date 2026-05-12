---
name: co-netgraph
description: Code-owner reminder for .claude/skills/circuit/netgraph.py — invariants surfaced before edit
---

# co-netgraph

Surfaces the invariants `netgraph.py` is expected to preserve before
an edit lands. Bound by [`.claude/codeowners.yaml`](../../codeowners.yaml).
Source of truth:
[`docs/developers/ideas/archived/idea-001.erc-engine.md §Net graph data model`](../../../docs/developers/ideas/archived/idea-001.erc-engine.md).
See also [ADR-0003](../../../docs/developers/adr/0003-netgraph-shared-contract.md).

## Invariants (checklist, not prose)

- [ ] **Hash determinism across parses.** Two parses of the same
      `.circuit.yml` produce a `NetGraph` whose canonical hash is
      byte-identical. The golden-hash CI contract (TASK-053) gates
      this; do not change serialisation order, dict iteration, or
      net-naming without regenerating the golden.
- [ ] **One canonical net representation.** The three connection
      forms in `.circuit.yml` (`pins`, `path`, `bus`) flatten into a
      single canonical net inside `NetGraph`. Downstream code never
      branches on which form the human wrote — by the time it sees
      the data, the form is gone.
- [ ] **No layout coordinates in the model.** `NetGraph` is purely
      topological. Anything carrying `(x, y)` or a slot name is a
      layout concern and belongs in `layout_engine/`, not here.
- [ ] **Read-only contract for consumers.** ERC, layout, and the
      netlist exporter consume `NetGraph` without mutating it. A
      consumer that needs to "annotate" the graph is a sign the
      annotation belongs in a sibling structure, not as a member.
- [ ] **Portability contract holds.** No host-project paths, no
      imports of `scripts.*` / `data.*`, no `CircuitSmith` references
      (per ADR-0007 and the portability lint, TASK-051).

## Authority

[`idea-001.erc-engine.md §Net graph data model`](../../../docs/developers/ideas/archived/idea-001.erc-engine.md) —
data model definition.
[`ADR-0003`](../../../docs/developers/adr/0003-netgraph-shared-contract.md) —
why this is the single shared contract.

## Downstream consumers

A breaking change to `NetGraph`'s public shape silently rots
**all three** of these — bump the schema-version (per
[`co-schema`](../co-schema/SKILL.md)) and re-test before landing:

- `.claude/skills/circuit/erc_engine.py` — runs ERC predicates
  against `NetGraph` (see [`co-erc-engine`](../co-erc-engine/SKILL.md)).
- `.claude/skills/circuit/layout_engine/kernel.py` — routes nets
  between component pins.
- `.claude/skills/circuit/netlist_exporter.py` — emits KiCad netlist
  by walking `NetGraph` (see [ADR-0004](../../../docs/developers/adr/0004-exporter-decoupling.md)).

`bom_exporter.py` is **not** a consumer — it walks `components`, not
`NetGraph`, on purpose (ADR-0004).
