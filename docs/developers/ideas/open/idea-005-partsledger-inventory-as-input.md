---
id: IDEA-005
title: Use PartsLedger inventory as additional input to prefer on-hand parts
description: Treat PartsLedger inventory as a constraint/preference source so generated circuits favour on-hand parts
category: 🛠️ tooling
---

Investigate how much adaptation is required to feed
[PartsLedger](https://github.com/tgd1975/PartsLedger)'s inventory
(`$CS_PARTSLEDGER_PATH`) into CircuitSmith as a **soft preference**
during component selection — so generated circuits default to parts
the user already owns, instead of always picking the canonical part
the schema suggests.

## Motivation

Today the CircuitSmith ↔ PartsLedger relationship is **one-way and
downstream**: CircuitSmith generates a BOM, PartsLedger ingests it.
The motto on the tin — *"CircuitSmith forges schematics. PartsLedger
keeps the record CircuitSmith reads."* — already gestures at the
reverse direction, but nothing in the codebase implements it.

The personal motivation is practical: I have a bin of components
already. When the generator picks a "1k 1% 0805" resistor for a
divider, and I have a stack of 1.2k 5% through-hole resistors on
the bench, the schematic is technically correct but operationally
annoying — I either order parts I don't need or hand-edit the BOM
afterwards. A small amount of inventory awareness would convert a
lot of those order/edit cycles into "build it from the bin."

## Rough approach

The adaptation lives in three layers; each is independently shippable.

### 1. Read PartsLedger's inventory format

- Point at `$CS_PARTSLEDGER_PATH`, locate the canonical inventory
  artefact (`inventory.yml` / SQLite / whatever PartsLedger settles on).
- Build a thin Python adapter in
  `.claude/skills/circuit/partsledger_inventory.py` that returns a
  dict `{ part_class: [InventoryEntry...] }`, keyed on the same
  taxonomy CircuitSmith's schema uses (resistor, capacitor, LED,
  IC by family, …).
- No coupling to PartsLedger's internal storage — only its declared
  export format. If that format is unstable, file an issue on the
  PartsLedger side first.

### 2. Soft-prefer on-hand parts in component selection

- During the existing component-resolution pass, after the schema
  has decided "this branch needs a 1k resistor," consult the
  inventory adapter.
- If the inventory contains a part that **meets the schema's
  constraints** (tolerance, package, voltage rating), prefer it
  over the canonical default.
- "Meets the constraints" is the load-bearing phrase: a 5% 1.2k
  resistor is not a substitute for a 1% 1k resistor in a precision
  divider — the ERC engine has to remain the source of truth.
- Soft, not hard: the user can always override. If nothing on hand
  fits, fall back to the canonical default and flag it in `meta.yml`
  so the BOM reflects "needs to be ordered."

### 3. Surface the inventory awareness in artefacts

- `meta.yml` grows a `parts_used_from_inventory:` and
  `parts_to_order:` section.
- BOM export distinguishes the two lists so the user knows what to
  pull from the bin vs. what to add to the next order.
- Optional later step: feed deductions back to PartsLedger so the
  inventory drops when a built circuit "consumes" its parts. That
  closes the loop but introduces write-back coupling — out of scope
  for the initial exploration.

## Open questions

- **Effort estimate.** This is the whole point of the idea — before
  committing to an epic, spike the adapter (layer 1) against the
  current PartsLedger format and write down what broke. Layers 2
  and 3 only make sense if layer 1 is cheap.
- **Format stability.** PartsLedger is also early-stage. Does it
  expose a stable export, or do we depend on internal storage?
  Either way, the integration should be **read-only and tolerant**
  — never crash CircuitSmith because the inventory file is missing
  or malformed.
- **Single-user vs multi-user.** The current model assumes one user,
  one bin. Multi-bin / multi-location stocking can come later.
- **Substitution policy.** When is a "close enough" part acceptable?
  Tolerance bands, package compatibility, value-tree (E12 vs E96)
  rules. This may want a small declarative substitution-policy
  file rather than hard-coded heuristics.
- **Relationship to** [[idea-004-tutorial-and-examples-to-show-capabilities]]
  — the tutorial's "Export the BOM" step is the natural place to
  demonstrate the inventory-aware version once it lands.
- **Test plan coverage.** Cross-link from
  [[idea-003-detailed-test-plan-for-every-part-of-circuitsmith]] —
  inventory-aware selection is a new subsystem and needs its own
  matrix entry (golden fixtures with a stubbed inventory).
