---
id: ADR-0003
title: `NetGraph` is the single shared contract for ERC, layout, and netlist export
status: Accepted
date: 2026-05-12
dossier-section: idea-001.erc-engine.md §Net graph data model
---

## Context

Three downstream stages need a *connectivity-aware* view of the
circuit:

- ERC engine — to check that every signal has a driver, no floating
  inputs, no shorts.
- Layout engine — to route nets between component pins.
- Netlist exporter — to emit a KiCad-compatible netlist.

If each stage re-parses `.circuit.yml` and constructs its own internal
representation, three things rot independently: each adds a connection
form (`pins`, `path`, `bus`) and three implementations diverge; each
makes a different decision about what counts as "the same net"; each
re-derives node naming, and the names drift across stages.

## Decision

A single in-memory model — `NetGraph` — is the **shared contract**
between `.circuit.yml` and the three downstream consumers. It is
constructed once by `netgraph.py` and consumed read-only by
`erc_engine.py`, `layout_engine/`, and `netlist_exporter.py`. Its
shape is hash-stable across parses (TASK-053 golden-hash contract).

The three connection forms allowed in `.circuit.yml` (`pins`, `path`,
`bus`) all *flatten* into the same canonical net representation
inside `NetGraph`. Downstream code never branches on which form the
human wrote — by the time the data reaches them, the form is gone.

`bom_exporter.py` is deliberately **not** a `NetGraph` consumer; it
walks the `components` list directly (see [ADR-0004](0004-exporter-decoupling.md)).

## Consequences

**Easier:**

- Adding a new connection form requires one edit (the `NetGraph`
  constructor); downstream code is unchanged.
- ERC, layout, and netlist export all agree on what "the same net"
  means by construction.
- A hash-stability test (TASK-053) catches accidental
  serialiser-output drift across the whole pipeline.

**Harder:**

- Any change to `NetGraph`'s public shape is breaking by design;
  the `co-netgraph` code-owner skill (TASK-056) surfaces this at
  edit time.
- Stages that need information not in `NetGraph` (e.g. component
  values for BOM) have to source it elsewhere — they do not get to
  extend the graph as a convenience.

## See also

[`idea-001.erc-engine.md §Net graph data model`](../ideas/archived/idea-001.erc-engine.md)
for the data structure and traversal contract.
