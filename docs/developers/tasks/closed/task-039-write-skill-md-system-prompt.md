---
id: TASK-039
title: Write .claude/skills/circuit/SKILL.md with full system prompt
status: closed
opened: 2026-05-12
closed: 2026-05-13
effort: Medium (2-8h)
effort_actual: Medium (2-8h)
complexity: Senior
human-in-loop: Support
epic: circuit-skill-packaging
order: 1
prerequisites: [TASK-022, TASK-031, TASK-033, TASK-016]
---

## Autonomy

`Main` → `Support` per TASK-060 sweep. SKILL.md system-prompt content
is the skill's user-facing contract — auto-prepare a draft, pause for
review at the commit stop-line before it lands.

## Description

Author `.claude/skills/circuit/SKILL.md` — the full system prompt that
turns the skill from a library into a Claude Code skill. Per
`idea-001.skill-packaging.md`:

- **Frontmatter**: `name: circuit`, the description sentence, and the
  full `allowed-tools` allowlist (Bash invocations for renderer, ERC,
  BOM, netlist, layout).
- **System prompt** establishing the seven behavioural rules from
  `idea-001-circuit-skill.md §AI Skill Prompt`:
  1. Knows the component library.
  2. Writes and edits YAML, not Python.
  3. Enforces layout conventions.
  4. Applies best practices grounded in the rule catalog.
  5. Asks before guessing (batched questions).
  6. Runs ERC first.
  7. Can add components.

## Acceptance Criteria

- [x] `SKILL.md` frontmatter declares `name`, `description`, and `allowed-tools`.
- [x] All seven behavioural rules are present with concrete examples.
- [x] No rule advocates runtime LLM generation of hardware advice — the catalog is the source.
- [x] System prompt cross-references the relevant docs (`docs/circuit-yaml.md`, `docs/erc-checks.md`, `docs/components.md`).

## Closure note

`allowed-tools` allowlist re-pointed from the dossier's stale
`python .claude/skills/circuit/<script>.py` patterns to the
post-[ADR-0012](../../adr/0012-library-as-installable-package.md)
form: `python -m circuitsmith.<module>` plus
`python scripts/regenerate_circuit_artefacts.py`. BOM, netlist, and
layout submodules are library-only (no CLIs) and are driven via the
regenerator, not direct invocation. The skill draft surfaces this
contract explicitly in the **Invocations** section.

## Test Plan

The Phase 6 acceptance test (TASK-041) exercises this prompt end-to-end. Manual review by the maintainer (HIL: Main) for tone and correctness before merge.

## Prerequisites

- **TASK-022** — ERC engine must exist so rule 6 ("Runs ERC first") is enforceable.
- **TASK-031** — BOM exporter must exist for the skill to invoke.
- **TASK-033** — netlist exporter must exist for the skill to invoke.
- **TASK-016** — referenced docs (`circuit-yaml.md`, `layout.md`) must exist.

## Notes

The `allowed-tools` allowlist is security-relevant — review carefully
against the actual scripts the skill needs.
