---
id: IDEA-011
title: Prefer on-hand parts from PartsLedger via --prefer-inventory adapter
description: Read PartsLedger's inventory as a soft preference during component selection, biasing generated circuits toward parts already on the bench; defines the cross-repo contract and the three-column BOM output.
category: 🛠️ tooling
---

> *Merges the former IDEA-005 (the **why** — bias toward on-hand parts)
> and IDEA-010 (the **contract** with PartsLedger) into one dossier.
> Both predecessors are archived; this is the canonical version.*

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

## Direction — one-way only

```text
PartsLedger              CircuitSmith
  INVENTORY.md  ───────►  --prefer-inventory mode
  parts/*.md    ───────►  (this repo, read-only consumer)
```

CircuitSmith **reads** PartsLedger's MDs. CircuitSmith does **not**
write back into the inventory. Two reasons:

1. **PartsLedger has prose, CircuitSmith has profiles.** PartsLedger's
   reference pages are hobbyist prose; this repo's component profiles
   are SPICE-style structured data. The schemas don't round-trip
   without lossy parsing.
2. **PartsLedger's source-of-truth invariant.** PartsLedger's
   [`co-inventory-master-index` skill](https://github.com/tgd1975/PartsLedger/blob/main/.claude/skills/co-inventory-master-index/SKILL.md)
   guard says only the human and PartsLedger's own skills write to
   `INVENTORY.md`. CircuitSmith automating writes would violate that
   invariant.

If this repo *wants* to push enrichments back (e.g. a SPICE-derived
`vcc_min`), the path is the same as any other contributor to
PartsLedger: emit a diff or a suggestion, let the maker apply it via
PartsLedger's `/inventory-add` skill or by hand.

## The contract

### What CircuitSmith reads

In order of priority:

1. **`$CS_PARTSLEDGER_PATH/inventory/INVENTORY.md`** — must read.
   The Part column + Qty column give CircuitSmith the *"what is in
   stock and how many"* view.
2. **`$CS_PARTSLEDGER_PATH/inventory/parts/<id>.md` Pinout tables** —
   best-effort. If a page exists and contains a Pinout section
   (recognisable by the DIP-N ASCII block + a pin/function table),
   the adapter lifts the pin-aliasing into the component-profile
   layer.
3. **Everything else** — ignored. Prose, ELI5, sample circuits,
   *"Pairs naturally with"* — all human-oriented and out of scope
   for the adapter.

Repo discovery follows `$CS_PARTSLEDGER_PATH` (env var pointing at
the PartsLedger repo root, per the project's `.envrc` convention),
with a CLI flag override.

### Field mapping

| PartsLedger | CircuitSmith profile field |
|---|---|
| `INVENTORY.md` Part column (e.g. `LM358N`) | `mpn` |
| `INVENTORY.md` Qty | `inventory.qty` |
| `INVENTORY.md` Description | (hint only — overridden by the profile if present) |
| `INVENTORY.md` Datasheet URL | `datasheet_url` |
| `parts/<id>.md` Pinout table | `pin_aliases` (per [IDEA-027 vocabulary](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-027-circuit-skill.md)) |

Fields the profile layer already had (`vcc_min`, `vcc_max`,
`pin_count`, `package`) stay in this repo's `components/*.py` — the
adapter does **not** invent them.

### Family-page handling

When `INVENTORY.md` has two rows that *"Share page with …"* (e.g.
`PIC16F628` and `PIC16F628A`), the adapter treats them as **two
distinct MPNs** with stock summed at family level for the *"in
stock"* check, but keeps the rows separate in the BOM output. The
maker still chooses which variant the schematic targets.

## Soft-prefer policy

The contract above tells CircuitSmith *what's on hand*. The selection
policy turns that into a build decision:

- During the existing component-resolution pass, after the schema has
  decided "this branch needs a 1k 1% resistor," consult the inventory
  adapter.
- If the inventory contains a part that **meets the schema's
  constraints** (tolerance, package, voltage rating), prefer it over
  the canonical default.
- *"Meets the constraints"* is the load-bearing phrase: a 5% 1.2k
  resistor is not a substitute for a 1% 1k resistor in a precision
  divider — the ERC engine remains the source of truth.
- Soft, not hard: the maker can always override. If nothing on hand
  fits, fall back to the canonical default and flag it in `meta.yml`
  so the BOM reflects "needs to be ordered."

## What the maker sees — BOM with `--prefer-inventory`

The BOM gets three columns instead of two:

```text
| Designator | Part        | Needed | In stock | To order |
|------------|-------------|--------|----------|----------|
| U1         | LM358N      | 1      | 1        | 0        |
| U2         | TL082CP     | 2      | 1        | 1        |
| R1..R8     | 10kΩ 1/4W   | 8      | (bulk)   | 0        |
```

`meta.yml` mirrors the split into `parts_used_from_inventory:` and
`parts_to_order:` sections so downstream tooling (and the maker's
"what do I need to buy" workflow) has a structured handle.

Bulk / kits show as `(bulk)` in the *In stock* column rather than a
numeric count — PartsLedger's inventory doesn't track individual
values inside a resistor kit (see [PartsLedger IDEA-004 § INVENTORY.md](https://github.com/tgd1975/PartsLedger/blob/main/docs/developers/ideas/open/idea-004-markdown-inventory-schema.md)).

## What we build vs. what we use

| Component | Source | Status |
|---|---|---|
| Inventory loader (~50 LOC) | This repo | ⏳ planned |
| Pin-aliasing lifter | This repo, reads PartsLedger Pinout tables | ⏳ planned |
| BOM column extension | This repo | ⏳ planned |
| `meta.yml` `parts_used_from_inventory` / `parts_to_order` split | This repo | ⏳ planned |
| MD schema | [PartsLedger IDEA-004](https://github.com/tgd1975/PartsLedger/blob/main/docs/developers/ideas/open/idea-004-markdown-inventory-schema.md) | ✅ stable on the PartsLedger side |
| Pin-aliasing vocabulary | [AwesomeStudioPedal IDEA-027](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-027-circuit-skill.md) | ✅ stable |

PartsLedger ships nothing for this; the whole adapter is a
CircuitSmith-side change. This dossier exists so the contract is
agreed in writing before either repo writes a line of code against
it.

## Layering and shipability

Three layers, each independently shippable:

1. **Adapter (read-only).** Implement *What CircuitSmith reads* +
   *Field mapping* above. Spike this against the current PartsLedger
   format first and write down what broke — layers 2 and 3 only make
   sense if layer 1 is cheap.
2. **Soft-prefer in selection.** Wire the adapter into the
   component-resolution pass per *Soft-prefer policy*.
3. **Surface in artefacts.** Three-column BOM + `meta.yml` split.

The integration must be **tolerant** at every layer — a missing or
malformed inventory file must degrade to "no preference," never
crash CircuitSmith.

## Open questions to hone

- **Effort estimate (layer-1 spike).** Before committing to an epic,
  spike the adapter against the current PartsLedger format and record
  what broke. Layers 2 and 3 are gated on that.
- **Pinout-table parser robustness.** The ASCII-DIP + table pattern
  is consistent across the existing PartsLedger pages, but it's a
  convention, not a spec — and PartsLedger IDEA-004 codifies that
  the Pinout section's shape *adapts to the part class*: TO-92
  sketch for 3-pin small-signal parts, one-line polarity note for
  2-pin parts, header diagram for modules. Only the DIP-N ASCII
  shape is structurally regular enough for an automated lifter.
  Likely partition: tighten a regex for the DIP-N shape and declare
  TO-92 / polarity-note / header-diagram pinouts **out of scope for
  automated pin-alias lifting** — the adapter skips them rather
  than guessing. PartsLedger IDEA-004 has closed out the
  *"add a structured `<!-- pin-aliases: yaml -->` block to
  `parts/*.md`"* alternative (parts pages stay prose-only), so any
  fallback richer than regex-over-DIP-prose lives on this side —
  e.g. an MPN-keyed pin-alias overlay file in this repo, which would
  also be the home for any aliases the maker wants to attach to a
  TO-92 transistor or a module header.
- **Substitution policy.** When is a "close enough" part acceptable?
  Tolerance bands, package compatibility, value-tree (E12 vs E96)
  rules. This may want a small declarative substitution-policy file
  rather than hard-coded heuristics.
- **Quantity reservation.** During BOM composition, if two designs
  are open and both want the single LM358N, who reserves it?
  Probably out-of-scope (the maker resolves by hand), but worth
  naming.
- **Family-page semantics in BOM.** Family-summed stock for
  feasibility check, per-row in the BOM — is that the right balance?
  Or always per-row?
- **Single-user vs multi-user.** The current model assumes one user,
  one bin. Multi-bin / multi-location stocking can come later.
- **Versioning.** What happens when PartsLedger's schema gains a
  `schema_version` ([PartsLedger IDEA-004 open questions](https://github.com/tgd1975/PartsLedger/blob/main/docs/developers/ideas/open/idea-004-markdown-inventory-schema.md))
  and this repo pins a version it understands? Add to the contract
  now, before either side has a v2.
- **Round-trip enrichment path.** Even though writes are one-way, a
  CircuitSmith *suggestion* mode (*"I derived `vcc_min=3.0 V` from
  the profile; want me to add a Notes line in INVENTORY.md?"*) might
  be useful. Worth specifying?
- **Test plan coverage.** Inventory-aware selection is a new
  subsystem and will need its own matrix entry (golden fixtures with
  a stubbed inventory) when the broader test-plan epic picks it up.

## Related

- [PartsLedger IDEA-004](https://github.com/tgd1975/PartsLedger/blob/main/docs/developers/ideas/open/idea-004-markdown-inventory-schema.md)
  — defines what the adapter reads.
- [PartsLedger IDEA-003](https://github.com/tgd1975/PartsLedger/blob/main/docs/developers/ideas/open/idea-003-external-inventory-tool-integration.md)
  — the InvenTree integration; if InvenTree becomes a parallel
  inventory source on PartsLedger's side, this adapter should be
  able to read it via the same pattern.
- [AwesomeStudioPedal IDEA-027](https://github.com/tgd1975/AwesomeStudioPedal/blob/main/docs/developers/ideas/open/idea-027-circuit-skill.md)
  — the canonical pin-aliasing vocabulary this repo carries upstream.
- Predecessor (archived): [IDEA-005](../archived/idea-005-partsledger-inventory-as-input.md)
  — the original *"use PartsLedger inventory as input"* dossier; this
  IDEA-011 supersedes it. (A second draft, *"IDEA-010 — `--prefer-inventory`
  adapter, contract with PartsLedger,"* existed on this branch but was
  folded in before landing, so it has no archive entry.)
