---
id: TASK-058
title: Implement scripts/check_phase2b_trigger.py
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-renderer-layout
order: 16
prerequisites: [TASK-057]
---

## Description

Implement `scripts/check_phase2b_trigger.py` — the observer half of
the Phase 2b trigger gate. The script aggregates
`meta.yml.provenance.escalations` (per
[TASK-057](task-057-emit-v01-escalations-to-meta-yml.md)'s schema)
across every committed `meta.yml` file at HEAD and produces a report
the release script (TASK-059) and the maintainer can read.

Logic:

1. Walk all `meta.yml` files committed to the repo.
2. Load `provenance.escalations` from each.
3. Group entries by `category`.
4. Compute `non_addressable_count` — sum of entries whose `category`
   is anything other than `no-canonical-rule` (i.e. cannot be retired
   by a §5.3 table addition; signals a genuine kernel gap).
5. Compute `no_rule_count` — entries with `category: no-canonical-rule`
   that are still present after the latest §5.3 revision (a separate
   stale-canonical check would compute this; in v0.1 just expose the
   count).
6. Emit a JSON report to stdout (build-artifact friendly).
7. Emit a Markdown summary to stderr (release-notes friendly).
8. Exit 0 unconditionally — this script *observes*, it does not gate.
   The gate is wired in [TASK-059](task-059-wire-phase2b-gate-into-release-script.md).

JSON report shape:

```json
{
  "total_escalations": 0,
  "by_category": { "no-canonical-rule": 0, "router-stall": 0, ... },
  "non_addressable_count": 0,
  "no_rule_count": 0,
  "circuits_with_escalations": []
}
```

## Acceptance Criteria

- [ ] `scripts/check_phase2b_trigger.py` exists and accepts an optional `--repo-root` argument (defaults to CWD).
- [ ] Walks committed `meta.yml` files (not the working tree — uses `git ls-files`).
- [ ] Produces the JSON report shape above on stdout and a Markdown summary on stderr.
- [ ] Exits 0 even when the trigger logic indicates a gate-worthy condition.
- [ ] `tests/test_phase2b_trigger.py` covers: empty corpus → all-zeros report; mixed corpus → correct category counts; malformed `meta.yml` field → script fails loudly with a clear error (not a silent zero).
- [ ] CI emits the JSON report as a build artifact (`phase2b-trigger.json`) on every PR.

## Test Plan

Fixture-based: `tests/fixtures/meta-empty/`, `tests/fixtures/meta-mixed/`,
`tests/fixtures/meta-malformed/`. Each contains a tree of fake
`meta.yml` files; the script runs against each fixture root with
`--repo-root` overridden. Assert the JSON shape on stdout.

## Prerequisites

- **TASK-057** — the `escalations` field with its `category` enum is the input contract.

## Notes

The Markdown summary on stderr is the document the maintainer reads
at release-prep review. The dossier's
[Phase 2b trigger gate](../../ideas/archived/idea-001-circuit-skill.md#phase-2b-ai-placer-contingent-on-real-failure-modes)
says "the maintainer evaluates at every release-prep review" — this
script turns the *evaluation* into a one-line `cat
phase2b-trigger.json | jq …`. TASK-059 then turns the evaluation into
a release-script gate.
