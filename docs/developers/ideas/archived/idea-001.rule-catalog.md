# Rule Catalog (Knowledge Base)

> Sub-note of [IDEA-001](idea-001-circuit-skill.md). Predecessor references
> (e.g. IDEA-011/018/019/022) resolve via the
> [Provenance anchor map](idea-001-circuit-skill.md#provenance).

The ERC checks (S1–S5, E1–E10) are the **enforcement** layer — pass/fail predicates
encoded in `erc_engine.py` that block CI on violations. The rule catalog is the
**knowledge** layer that sits alongside: a curated, source-linked JSON database that
enriches the ERC report with explanations, heuristics, and further reading, and that
the skill consults to offer proactive advice when a maker adds a new component.

This turns the circuit skill from a strict linter into a "senior designer" mentor — the
framing the skill's system prompt already adopts (see
[AI Skill Prompt](idea-001-circuit-skill.md#ai-skill-prompt-skillmd-summary)).
The catalog is what makes that framing reliable instead of free-form LLM guessing.

## Why separate the catalog from the check code

An ERC check is a predicate. A catalog entry is a teaching artifact: plain-language
explanation, a safe starting value ("heuristic"), and a link to a trustworthy source.
Keeping them in separate files has three benefits:

- the check code stays focused on graph analysis; prose does not bloat `erc_engine.py`;
- the catalog can contain **educational rules with no ERC check** — e.g. choosing between
  an LDO and a switching regulator, or how to debounce a switch — which the skill surfaces
  proactively but does not fail CI on;
- text edits to explanations and heuristics require no code review and cannot break the
  linter.

## Catalog format

`.claude/skills/circuit/knowledge/rules.json` is an array of entries:

```json
{
  "id": "E2",
  "category": "Digital Outputs",
  "keywords": ["led", "resistor", "gpio", "current limiting"],
  "rule": "A standard LED always requires a current-limiting resistor.",
  "explanation": "An LED has very little internal resistance. Connecting it directly to a microcontroller's GPIO pin will draw excessive current, which can permanently destroy the LED and damage the pin.",
  "heuristic": "For a 3.3 V supply (ESP32, Raspberry Pi), start with a 220 Ω resistor. For a 5 V supply (Arduino Uno), start with 330 Ω. A higher value is always safer and just makes the LED dimmer. For precision applications, calculate the exact value or consult the datasheet.",
  "source_of_truth": "https://www.elektronik-kompendium.de/sites/bau/0201111.htm",
  "enforced_by": "E2"
}
```

Field notes:

- `id` matches the ERC check code when the rule maps 1:1 to a check. Educational-only
  entries use category-prefixed IDs (`PS-01`, `DI-03`, `HW-ESP32-02`, …) and omit
  `enforced_by`. IDs are **unique across the whole catalog** — ERC-mapped and
  educational entries share one namespace, so `validate_catalog.py` rejects duplicates.
- `keywords` drive contextual surfacing by the skill — when the maker adds a component
  whose profile declares matching keywords, the skill pulls the entry into the
  conversation before running the ERC. The vocabulary is shared with
  [`metadata.keywords`](idea-001.components.md#2-metadata--human-readable-identity-and-electrical-constraints)
  on component profiles.
  The validator enforces four invariants on this vocabulary:
  - **Normalisation.** `validate_catalog.py` lowercases and NFKC-normalises keywords
    before comparison, so spelling drift (`I2C` vs `i2c` vs `I²C`) cannot silently
    cause an empty intersection.
  - **Authored form.** Keywords are written in their normalised lowercase form (see
    the example above) so the file matches the comparison form and diffs stay clean.
  - **Profile membership.** The validator rejects any catalog keyword that does not
    appear in at least one shipped component profile. The profile source of truth
    it scans is `.claude/skills/circuit/components/*.py`, the path pinned by
    [components.md §4](idea-001.components.md#4-schema-registration). Rules whose
    natural surfacing target is a topic rather than a specific component (e.g.
    PS-01 bulk-cap advice that applies to the board as a whole, not to any one
    part) use the reserved keyword `topic:<category>` — e.g. `topic:power-supply`
    — which the validator accepts without a profile-membership check. Reserved
    `topic:*` tokens are surfaced by category context rather than keyword
    intersection.
  - **Same-PR introduction.** A new non-`topic:*` catalog keyword must land in a
    component profile under that directory in the same PR, not a follow-up.
- `heuristic` is the "safe starting point" — what an experienced designer offers when
  asked informally. Three recognised shapes, useful for consistent authoring:
  - **Rule of thumb** — a concrete value that works for the common case ("220 Ω for a
    3.3 V LED", "330 Ω for a 5 V LED").
  - **Safe starting point** — a value that can be tuned if needed but is safe as a
    default ("10 kΩ for a button pull-up; drop to 4.7 kΩ for faster I2C").
  - **Warning heuristic** — a defensive value that prevents a failure mode even if not
    strictly required ("10–100 Ω MOSFET gate resistor to dampen ringing").
- Every `heuristic` must be chosen so that the value errs on the **safe side**: a
  higher-than-needed LED resistor makes the LED dim but cannot destroy it; a
  higher-than-needed pull-up draws less current but still defines the level. If the
  safe direction is ambiguous for a given rule, pick the failure mode that degrades
  performance rather than the one that damages hardware.
- Every `heuristic` also ends with the boilerplate **precision disclaimer**: *"For
  precision applications, calculate the exact value or consult the datasheet."* This
  is enforced by `validate_catalog.py` (substring match) so no entry silently presents
  a heuristic as an exact answer.
- `heuristic` is prose-only at v0.1; values like "220 Ω" inside the text are not
  cross-checked against the ERC's own ranges (E3 enforces 100 Ω–1 kΩ independently).
  The current range is wide enough that the two cannot realistically disagree, but
  `# TODO(v0.2): structured heuristic_value` — adding a parallel machine-readable
  field would let the validator assert consistency between catalog prose and check
  bounds.
- `source_of_truth` is a direct URL to the canonical explanation of the underlying
  principle. The `validate_catalog.py` script checks reachability in CI.

## Source-of-truth policy and licensing

The primary source for general electronics rules is
[elektronik-kompendium.de](https://www.elektronik-kompendium.de/), the most comprehensive
German-language online reference for electronics fundamentals. Hardware-specific entries
link to vendor documentation (Espressif for ESP32, Arduino reference, Raspberry Pi docs).

Where EK is thin or absent, the English fallback hierarchy is:

1. **[All About Circuits](https://www.allaboutcircuits.com/textbook/)** — a
   comprehensively structured online textbook, used for rules where the EK article is
   terse or missing. Didactic quality is high; the tradeoff is that it is not as
   densely cross-referenced as EK.
2. **[Wikibooks Circuit Theory](https://en.wikibooks.org/wiki/Circuit_Theory)** — used
   only when neither EK nor All About Circuits has usable coverage. Quality and depth
   vary by chapter; treat as a last-resort source.

Catalog entries should prefer the highest-quality source for the specific rule, not a
blanket project-wide choice — the rule is a user-facing artifact and the link is a
promise that the reader will find the explanation useful.

**Licensing boundary.** Elektronik-kompendium.de content is under standard copyright
(© Patrick Schnabel). The catalog respects this strictly:

- rules are **read, understood, and then reformulated in English** — no copy-paste of
  text, no machine translation of protected passages,
- every entry **links** to the original article as the source of truth (linking is
  permitted and encouraged — it respects copyright and drives traffic back to the author),
- no images, diagrams, or long passages are reproduced.

This transformative approach is compatible with the project's MIT license: the catalog
text is our original work, the underlying facts are not copyrightable, and attribution
is preserved via the `source_of_truth` field. (This is an engineering judgement informed
by standard copyright principles, not legal advice — the author agreed to this model
after weighing the trade-offs during the concept discussion.)

The same licensing regime applies to skill **runtime output** to users, not only
to authored catalog entries. See [How the skill uses the catalog](#how-the-skill-uses-the-catalog)
below (the "Follow-up queries" paragraph) for the Option A paraphrase rule that
bounds what the skill may emit in response to definitional questions.

## Scope — 30 to 50 rules, not a textbook

The catalog targets **30–50 entries** covering the common cases in maker projects. It is
deliberately not a comprehensive electronics textbook; completeness is a non-goal.

| Category | Focus | Target count |
|---|---|---|
| Power Supply | Decoupling, bulk caps, LDO selection, voltage headroom | 5–7 |
| Digital Inputs | Button/switch wiring, pull-up/-down, debounce, voltage dividers | 7–10 |
| Digital Outputs | LED resistors, PWM, inductive loads, flyback diodes | 7–10 |
| Communication | I2C pull-ups, SPI logic levels, level shifting | 5–8 |
| Hardware Specifics | ESP32 ADC2/WiFi, strapping pins, Arduino A4/A5 = I2C, Pi has no ADC | 5–8 |

Category targets sum to 29–43; the 30–50 envelope leaves 1 slot of headroom at
the low end (30 − 29) and 7 at the high end (50 − 43) for rules that surface
during real use without forcing a category to go above its own ceiling.

Explicitly **not** in the catalog:

- PCB layout rules (trace width, grounding, EMI) — belong to IDEA-011.
- Audio signal conditioning — no analog audio path in the first iteration.
- Per-component encyclopedia entries ("what is a resistor?") — answered by the
  `source_of_truth` link or by an LLM's short definition, not authored here.

## How the skill uses the catalog

**During ERC reporting.** `erc_engine.py` looks up each finding's rule `id` in
`rules.json` and appends the `explanation`, `heuristic`, and `source_of_truth` to the
Markdown report under each non-OK finding (see the enriched format above).

**During authoring (proactive surfacing).** When the skill processes a request like
"add a BME280 over I2C", it intersects the component's profile keywords with the
catalog's `keywords` arrays before writing YAML. ERC-enforced entries surface alongside
their educational companions so the maker sees both the hard rule and the practical
nuance. For BME280 on an ESP32:

- `E7` (enforced): I2C SDA/SCL require pull-ups — the YAML must wire them or the
  breakout must provide them.
- `COMM-01` (educational): Most BME280 breakout boards already integrate 4.7 kΩ
  pull-ups — inspect the PCB before adding externals, which is how `E7` is satisfied
  in practice.
- `COMM-02` (educational): Logic-level check — BME280 is 3.3 V, ESP32 is 3.3 V, no
  level shifter needed. (Would surface with a different recommendation if the target
  were an Arduino Uno at 5 V.)
- `E6` (enforced): Missing decoupling cap — add 100 nF close to the BME280 VCC pin.

This is the behaviour
[AI Skill Prompt](idea-001-circuit-skill.md#ai-skill-prompt-skillmd-summary) rule 4
("applies best practices automatically") is grounded in. Without the catalog, rule 4
would rely on the LLM's latent knowledge — plausible but unverifiable. With the
catalog, every "senior tip" is a lookup against a curated, linked source.

**Follow-up queries ("what is X?").** When the maker asks a definitional question
about a keyword surfaced by the catalog ("what is a pull-up resistor?", "what is PWM?"),
the skill resolves it with one of two strategies:

- **Option A — deterministic lookup.** Open the `source_of_truth` URL from the matching
  catalog entry and present the user with the direct link. The single bar that applies
  across all sources is the **catalog-authoring bar**: read, understood, and reformulated
  in the author's own words — not a close paraphrase of the original paragraph, and
  not a translation. Whether reformulation is *permitted at all* depends on the source:
  - **elektronik-kompendium.de** — proprietary. Runtime output is **link-only**:
    page title and URL may be quoted as standard citation, no paraphrase of the
    article body, to stay clear of the licensing boundary stated above.
  - **All About Circuits** — proprietary. Same as EK: link-only at runtime.
  - **Wikibooks** (CC BY-SA 3.0) — reformulation permitted at the catalog-authoring
    bar, provided the `source_of_truth` link is visible; the `enforced_by` →
    rule-text pipeline is considered transformative reuse.
  - **Vendor documentation** — reformulation permitted at the catalog-authoring bar
    when the vendor's terms explicitly allow reproduction or paraphrase of
    engineering docs; otherwise link-only.

  Authoritative and verifiable; preferred default.
- **Option B — narrow LLM query.** For terms with no catalog entry (and only then),
  issue a tight prompt to the LLM: *"Explain X in one sentence for a beginner."* The
  narrow scope keeps the hallucination surface small — a one-sentence definition of a
  basic component is low-risk compared to free-form design advice.

Option A is always tried first; Option B is the fallback. Rules, values, and design
guidance never come from Option B — those require a catalog entry or an ERC check.

## Niche — where this sits relative to existing tools

The catalog-plus-ERC combination fills a gap between two existing tool classes:

- **Professional EDA AI assistants** (CELUS, Flux Copilot, Quilter) target PCB-layout
  automation for experienced engineers. They assume the user already knows the
  fundamentals this catalog teaches.
- **Generic LLM chatbots** (GPT Store electronics bots, etc.) answer electronics
  questions but give no verifiable guarantee of correctness — they can hallucinate
  plausible-sounding but dangerous advice.

This skill is neither. It is a focused, verifiable mentor for makers, grounded in a
small curated rule set with source links. The deliberate narrowness (30–50 rules, no
PCB, no audio) is the point, not a limitation.

## Catalog authoring workflow

1. Pick a rule from `knowledge/BACKLOG.md` (see seed list below).
2. Read the corresponding elektronik-kompendium.de article (or vendor doc for
   HW-specific entries). The semiconductor index at
   <https://www.elektronik-kompendium.de/sites/index.php?dir=slt> is the recommended
   entry point for Power Supply, Digital I/O, and Communication rules; it gives a
   hierarchical view of the relevant sections without requiring free-text search.
3. Reformulate the rule, explanation, and heuristic in English — not a translation of
   the source, a fresh statement of the same fact.
4. Fill the JSON entry with keywords that match the component profile fields the skill
   will query.
5. If the rule maps to an ERC check, set `enforced_by` to the check code and verify the
   check logic in `erc_engine.py` matches the rule as written.
6. Run `python .claude/skills/circuit/knowledge/validate_catalog.py` to check format,
   link reachability, precision-disclaimer presence, keyword normalisation and
   profile-membership, catalog-ID uniqueness, and `enforced_by` consistency.

**What `enforced_by` consistency means.** The validator enforces the **weak** form
only: every `enforced_by` value must reference a check code that exists in
`erc_engine.py`'s constant table, and every code in that table must be referenced
by **at least one** catalog entry. The constant table holds **S1–S5 + E1–E10 = 15
codes** — S4 and S5 are detected by schema validation rather than by predicates in
the ERC engine, but their codes (severity, message template, `id`) are defined
alongside S1–S3 so schema-validation findings surface in the same ERC report format
(see [erc-engine §Checks](idea-001.erc-engine.md#checks)). A single check may be
taught by multiple entries when it legitimately covers more than one angle — e.g.
E4 current budget splitting into a per-pin rule and a total-chip rule rather than
one compound entry. This means introducing a new ERC check and its
catalog entry must land in the **same PR**: the validator treats a missing catalog
row for an existing check code as a CI failure, so enforcement cannot ship without
teaching. The **strong** form — that the catalog's `rule` sentence semantically
matches what the check predicate actually fires on — is **not** lintable and is a
manual review step in step 5 of the workflow. When a PR changes either a check
predicate or a catalog `rule` referencing it, the reviewer is expected to re-read
the other entries sharing that `enforced_by` and confirm they all still describe
the same condition.

**Same-PR invariants.** Two rules in this doc require changes to land in a single
commit rather than follow-ups; collected here so the pattern is visible in one place:

- A new catalog keyword lands in at least one component profile under
  `.claude/skills/circuit/components/*.py` in the same PR (keyword bullet above).
- A new ERC check lands with its catalog row in the same PR (this section above).

Both are enforced by `validate_catalog.py` as CI failures on the PR branch — not
as post-merge TODOs.

## Seed backlog (non-ERC educational rules)

The ERC checks cover one catalog entry each (S1–S5, E1–E10). To reach the 30–50 target,
`BACKLOG.md` is seeded with these educational-only rules identified during the concept
discussion — they inform the maker but are not automatically enforceable:

| ID (proposed) | Category | Topic |
|---|---|---|
| PS-01 | Power Supply | Bulk capacitor (10–100 µF) at main power entry |
| PS-02 | Power Supply | LDO vs 78xx linear regulator — headroom and efficiency |
| DI-01 | Digital Inputs | Switch/button debounce — software delay vs RC hardware |
| DI-02 | Digital Inputs | Voltage divider for resistive sensors (LDR, thermistor) |
| DO-01 | Digital Outputs | PWM as analog-output proxy — hardware vs software PWM |
| DO-02 | Digital Outputs | MOSFET gate resistor (10–100 Ω) to dampen ringing |
| COMM-01 | Communication | Breakout boards often integrate I2C pull-ups — inspect the PCB |
| COMM-02 | Communication | Bidirectional logic-level shifter for 3.3 V ↔ 5 V buses |
| HW-ESP32-01 | Hardware Specifics | Native USB on ESP32-S2/S3/C3 obsoletes external CH340 |
| HW-RPI-01 | Hardware Specifics | Raspberry Pi has no built-in ADC — use MCP3008 over SPI |
| HW-ARD-01 | Hardware Specifics | Arduino Uno A4/A5 are the I2C pins — cannot be shared |

These eleven plus the ERC-mapped entries (≥ 15: S1–S5 and E1–E10, each with at
least one catalog row per the weak-form rule above) give ≥ 26 rules in Phase 3,
leaving the remainder of the 30–50 target — 4 slots at the floor, up to 24 at the
ceiling — for rules that surface during real use, subject to the per-category
ceilings in the scope table above.

---
