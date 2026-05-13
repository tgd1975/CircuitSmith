---
id: EPIC-010
name: circuitsmith-package
title: Consolidate skill-resident Python into circuitsmith package
status: open
opened: 2026-05-13
closed:
assigned:
branch: release/epic-010-circuitsmith-package
---

Seeded by IDEA-002 (Consolidate skill-resident Python into a central module).

Relocate library code from `.claude/skills/circuit/` to `src/circuitsmith/`
and rename the importable package from `circuit` to `circuitsmith`. The
skill folder shrinks to agent-facing prompts (and optional thin shims);
the Python code becomes a first-class installable package.

This epic supersedes [ADR-0007](../../adr/0007-skill-directory-is-the-library.md)
("The skill directory is the library") with a new ADR-0012
("Library as installable package"). The no-host-project-imports
invariant survives unchanged — only the *scope* moves from
`.claude/skills/circuit/` to `src/circuitsmith/`.

EPIC-006 (Circuit Skill — Skill Packaging and Standalone Extraction)
is rewritten in place by this epic's Phase 1.3: the standalone-folder
extraction path is replaced by a PyPI publication path, and
TASK-045 (replace-skill-dir-with-pinned-copy) retires.

Gates EPIC-003. The full execution plan — Phases 0–5, one stop-line
at the end of Phase 1 (ADR-0012 sign-off), atomic Phase 2 relocation,
verification gates, rollback — lives in the seeding idea file:
[`docs/developers/ideas/archived/idea-002-consolidate-skill-python-into-central-module.md`](../../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md).

## Tasks
