# EPIC-013 — plan for the human-in-loop tasks (TASK-104..109)

> Working document. Produced 2026-06-21, after TASK-102 (inventory) and
> TASK-103 (drift catalogue) closed. Those two were the only autonomously
> completable tasks — **everything from order-3 onward is gated on TASK-104,
> and TASK-104 + TASK-108 + TASK-109 are `human-in-loop: Main`.** This plan
> is how we drive that phase together; nothing here is executed without your
> sign-off.

## Status — updated 2026-06-21

TASK-102..107 are **closed and pushed** on
`release/epic-013-post-epic-006-doc-audit`. The three gating decisions were
made: voice **accepted**, README **full rewrite** (TASK-109), `TESTING.md`
**stub-and-point** (TASK-107). What landed: the canonical-voice note +
concept-stage drift fixes (104); the `check_doc_references.py` CI gate +
~17 broken-link fixes (105); tutorial alignment, "See also" pointers, and
the ARCHITECTURE glossary (106); the `TESTING.md` ↔ `testing/`
reconciliation (107).

**Remaining — both Main-HIL, awaiting your direction:**

- **TASK-108** — annotate the IDEA-001 dossier. Large: section-level
  shipped / changed / dropped / future notes across all nine `idea-001.*`
  files (~5,400 lines). The agent can draft; you must verify each EPIC / ADR
  mapping — inaccuracies mislead future readers, which is why it is Main.
- **TASK-109** — README + entry-point rewrite (blank-page, per your
  decision). The public face; the AC requires your fresh-visitor cold-read.

Two ways to proceed (your call): **(a)** I draft 108 then 109 on-branch for
your cold-read at review — maximal progress, you sign off at merge; or
**(b)** you drive them and I assist. The sections below are the execution
reference either way.

## Why this phase is human-in-loop

| Task | Order | HIL | Prereq | Why it needs you |
|---|---|---|---|---|
| TASK-104 voice unification | 3 | **Main** | 103 ✓ | Rewriting your authored prose into a chosen voice — subjective; reviewed in batches. |
| TASK-105 cross-ref audit | 4 | Clarification | 104 | Builds `check_doc_references.py` + fixes the broken links; audits *canonical* text, so waits for 104. |
| TASK-106 tutorial alignment | 5 | Clarification | 104 | Small; fixes D19/D22. |
| TASK-107 test-plan alignment | 6 | Clarification | 104 | Reconciles `TESTING.md` ↔ `testing/`; fixes D10–D15. |
| TASK-108 dossier annotation | 7 | **Main** | 104 | Annotating the archived IDEA-001 dossier — editorial judgment on what shipped vs didn't. |
| TASK-109 README + entry-points | 8 | **Main** | 104–108 | The public face; AC *requires* your cold-read sign-off. |

The whole chain funnels through TASK-104. Once its voice decision is made
and the batches are approved, 105–108 are largely mechanical and 109 is the
capstone.

## Decision 1 — the canonical voice (TASK-104's first gate)

TASK-104 says: pick the voice of the most recent EPIC-005/006 docs, capture
it as a discoverable style note in `CODING_STANDARDS.md` (or a sibling). The
best exemplars in-repo are the **EPIC-011 `testing/` chapters**, **AUTONOMY.md**,
and **COMMIT_POLICY.md**. Proposed style note for your approval (drop into
`CODING_STANDARDS.md` under a new "Documentation voice" heading):

> **Documentation voice.** Present-tense and declarative for how the system
> behaves ("the renderer emits…", not "the renderer will emit…"); imperative
> for instructions to the reader. Terse and concrete — lead with the rule,
> then the *why* in a clause or parenthetical. Cite tasks/ADRs/code paths
> inline (`TASK-091`, `ADR-0012`, `src/circuitsmith/netgraph.py`) rather than
> describing them. No marketing language, no aspirational "we plan to" for
> shipped features, no status banners that rot. Em-dashes for asides; short
> paragraphs over walls of prose.

**You decide:** accept this voice as-is, amend it, or pick a different
exemplar. Everything in TASK-104 keys off this.

## Decision 2 — scope of the README rewrite (TASK-109)

The README is concept-stage end-to-end (D1–D5). Two options:

- **(a) Reframe in place** — keep the structure, retense to "shipped at
  v0.1.0", fix the five drift items, tighten the tutorial/contributor/
  architecture pointers. Lower risk, faster.
- **(b) Rewrite from a blank page** — a fresh-visitor-first README. Higher
  impact, but a bigger diff and more of your review time.

I recommend **(a)** unless you want a marketing-grade front page. Either way
TASK-109 is Main-HIL: I draft, you read it cold and sign off.

## Execution plan, task by task

### TASK-104 — voice unification (Main, batched)

Rewrite targets (from `_doc-audit-inventory.md` §4), grouped into review
batches of ≤5 files. After each batch I stop; you read the rewritten files
cold and sign off before the next.

- **Batch A (highest drift):** `README.md`*, `ARCHITECTURE.md`,
  `TESTING.md`, `CONTRIBUTING.md`, `CLAUDE.md`.
  *(README's full treatment is formally TASK-109; in Batch A I only fix its
  concept-stage drift so the entry-point isn't wrong while 105–108 run.)*
- **Batch B (builder/skill):** `.claude/skills/circuit/docs/circuit-yaml.md`,
  `docs/builders/wiring/esp32/README.md`,
  `docs/builders/wiring/nrf52840/README.md`.
- Skip everything classified `post-epic-006`/clean — already canonical.
- For each file: rewrite in the Decision-1 voice, fix inline the drift items
  D-numbered to it, update the inventory's freshness column to
  `post-epic-006`, strike the resolved drift rows in `_doc-audit-drift.md`
  with the commit ref.
- **Out-of-scope guard:** if a file needs more than a voice/tense pass
  (architecture revision), file a follow-up TASK rather than expanding scope
  (TASK-104 "Notes").

### TASK-105 — cross-reference audit (Clarification)

- Build `scripts/check_doc_references.py` (five reference classes: relative
  links, `TASK/EPIC/IDEA` refs, code-path mentions, ADR refs, external URLs
  behind an opt-in `--check-external` flag). Pattern: mirror
  `scripts/check_test_plan_staleness.py` (TASK-091) — same CLI shape, same
  CI-job-naming convention (`check-docs-refs`), `tests/` suite, settings
  allow-rule, `scripts/README.md` row, `CI_PIPELINE.md` gate.
- Fix the broken-link drift it will catch: **D8, D16, D18, D20, D21, D23,
  D24, D25** (already located — see the catalogue).
- Wire into CI only once it exits 0 (so the gate lands green).
- This one is autonomously completable **once TASK-104 closes** (no Main
  gate) — I can run it without batched sign-off, surfacing only the external
  URLs for your call.

### TASK-106 — tutorial alignment (Clarification)

- Fix **D19** (`users/README.md` stale status) and **D22**
  (`tutorial/README.md` placeholder status). Confirm tutorial steps still
  match the shipped CLI/schema (they scanned clean). Small.

### TASK-107 — test-plan alignment (Clarification)

- Reconcile **D15**: trim `TESTING.md` to an intro that points at
  `testing/README.md` as canonical (or fold its unique content in), and fix
  the stale imports **D10–D14**. Decision needed: *stub vs fold* — I
  recommend stub + a one-paragraph "see testing/ for the full plan".

### TASK-108 — annotate IDEA-001 dossier (Main)

- Add "shipped / didn't ship / changed" annotations to the archived
  `idea-001.*` dossier (do **not** rewrite it — it's a frozen record).
  Editorial; you review the annotations.

### TASK-109 — README + entry-points (Main, capstone)

- Per Decision 2. Final cold-read sign-off by you is the AC. Includes the
  CHANGELOG prose sanity check and the "fresh-visitor walkthrough".

## What I need from you to proceed

1. **Decision 1** — approve / amend the canonical voice note.
2. **Decision 2** — README reframe-in-place (a) vs blank-page (b).
3. **Decision 3** — `TESTING.md`: stub-and-point vs fold-in (TASK-107).
4. **Go-ahead + tempo** — confirm the batch tempo (I draft Batch A, you sign
   off, repeat), or tell me to run the non-Main tasks (105–107) straight
   through and reserve your review for the Main batches (104 drafts, 108,
   109) only.

Once you answer, I activate TASK-104 and produce Batch A drafts for review.
