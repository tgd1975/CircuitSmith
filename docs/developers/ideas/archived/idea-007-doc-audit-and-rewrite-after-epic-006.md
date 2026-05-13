---
id: IDEA-007
title: Intensive review and rework of the documentation after EPIC-006
description: Documentation audit and rewrite once EPIC-006 lands, to reconcile drift between code and docs
category: 🛠️ tooling
---

## Archive Reason

2026-05-13 — Elevated to EPIC-013 (Post-EPIC-006 Documentation Audit and Rewrite).

Once EPIC-006 is implemented, CircuitSmith will have gone through the
full arc from concept-stage dossier to a working schematic-generation
pipeline (CLI, layout engine, AI placer, renderer, ERC, BOM,
fixtures, CI). The documentation in `docs/` has accumulated in lockstep
with that work, mostly task-by-task — meaning prose written for an
earlier shape of the system is still sitting next to prose written for
the final shape. By the time EPIC-006 closes, the docs will need an
end-to-end pass to bring them into one voice, one mental model, and
one canonical structure.

## Motivation

- The inherited `idea-001.*` dossier (now in
  [`docs/developers/ideas/archived/`](../archived/)) described a system
  that didn't exist yet. EPICs 001–006 incrementally make it real, but
  the order of implementation means later docs sometimes contradict
  earlier ones rather than supersede them cleanly.
- Per-task documentation tends to optimise locally — what the *task*
  needs to explain — not globally. The result is fine paragraph by
  paragraph but uneven as a whole: redundant explanations, drifted
  terminology, broken cross-references, stale "future work" notes
  that have already become reality.
- Onboarding docs (`README.md`, `docs/builders/`, `docs/developers/`)
  were largely written before there was anything to demonstrate. After
  EPIC-006 there *is* something to demonstrate — the docs should
  reflect that.

## Rough approach

Not prescriptive — a rough sketch of what the review pass should
cover:

1. **Inventory.** Walk every `.md` file under `docs/` and the repo
   root. Bucket by audience (builder, developer, contributor) and by
   freshness (written pre-EPIC-001, mid-epic, post-EPIC-006).
2. **Drift sweep.** Identify claims that no longer match the code:
   stale CLI flags, retired scripts (`generate-schematic.py` etc.),
   filepaths that have moved, "planned" features that shipped, examples
   that no longer parse.
3. **Voice and structure.** Pick a canonical voice (likely the one used
   in the later EPIC-005/006 docs, since those were written with the
   full system in mind) and bring the earlier docs forward to match.
4. **Cross-reference audit.** Every internal link, every reference to
   `TASK-NNN` / `EPIC-NNN` / `IDEA-NNN`, every code-path mention —
   verify or fix.
5. **Tutorial alignment.** Coordinate with [[idea-004-tutorial-and-examples-to-show-capabilities]]
   so the worked-example layer and the reference docs tell the same
   story.
6. **Test-plan alignment.** Coordinate with [[idea-003-detailed-test-plan-for-every-part-of-circuitsmith]]
   so the "how it's tested" sections in the docs match the actual test
   surface.

## Open questions

- Convert to a single large EPIC, or several smaller tasks under an
  existing umbrella? An EPIC scopes the work but risks bundling
  unrelated rewrites; a flat set of tasks risks fragmenting the voice
  pass.
- Should `idea-001.*` archived dossier be revisited at the same time
  (annotate "what shipped" vs "what didn't") or left as a historical
  artefact?
- Builder docs (`docs/builders/`) vs developer docs
  (`docs/developers/`) — both need the pass, but on different
  schedules and with different audiences. Same task or split?

## When

Strictly after EPIC-006 closes. Doing it during EPIC-006 means
chasing a moving target; doing it well after means rediscovering all
the small drifts a second time.
