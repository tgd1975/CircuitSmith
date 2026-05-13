---
id: ADR-0012
title: Library is an installable package; skill folder is the agent-facing surface
status: Accepted
date: 2026-05-13
dossier-section: idea-002-consolidate-skill-python-into-central-module.md
supersedes: ADR-0007
---

## Context

ADR-0007 collapsed library and skill into one location:
`.claude/skills/circuit/` *was* the library, and Phase 7 extraction was
a mechanical `cp -r` of that directory. The portability contract that
prohibited host-project imports kept the directory standalone-ready.

That decision aged poorly. The Python tree under
`.claude/skills/circuit/` is now several modules deep
(`netgraph.py`, `layout_engine/`, `schema/`, `components/`,
`renderer.py`, …) and continues to grow. The user reports the
nested-under-a-skill-folder shape as "no oversight possible … i am
lost"; readers cannot tell library code from skill-config. The
problem worsens with each subsequent epic (renderer, ERC, exporters)
that would otherwise land more `.py` files inside the skill folder.

Two architectures could replace ADR-0007:

- **Folder-copy extraction (the ADR-0007 status quo).** Keep the
  library where it is; ship the folder as the deliverable.
- **Installable package + agent-facing skill folder.** Move the
  library to a normal `src/` layout, ship it as a wheel on PyPI,
  and let the skill folder retain only the agent prompts.

The user has explicitly rejected the status quo and chosen the
package shape (see [`idea-002` § "Decisions (2026-05-12)"](../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md#decisions-2026-05-12)).

## Decision

The library is an **installable Python package** named `circuitsmith`,
laid out under `src/circuitsmith/`. The deliverable to a consuming
repo is two artefacts:

1. The Python package — `pip install circuitsmith` (PyPI) or a git
   URL pin during development.
2. The skill files at `.claude/skills/circuit/` — `SKILL.md`,
   `docs/`, and optional thin shim `.py` files that import from
   `circuitsmith.*`.

Skills consume the package; the package never knows about skills.
There is no third "loose lib/" surface.

The **no-host-project-imports invariant survives unchanged** — only
its scope shifts. The contract now applies to `src/circuitsmith/`
instead of `.claude/skills/circuit/`. `scripts/portability_lint.py`
retargets at the new path; its rule set is unchanged. The lint stays
green across the refactor.

## Consequences

**Easier:**

- The Python tree has one obvious location — `src/circuitsmith/` —
  that newcomers and reviewers can read end-to-end.
- Distribution becomes a normal Python release flow:
  `python -m build`, trusted publishing, semantic version pins.
  Consumers get reproducible installs from PyPI.
- The skill folder shrinks to its actual responsibility: the
  agent-facing prompt surface. SKILL.md and `docs/` stop sharing
  oxygen with library code.
- Future code-owner reminder skills (`co-netgraph`, `co-schema`,
  `co-erc-engine`, …) point at one canonical path under
  `src/circuitsmith/` rather than tracking the skill-folder layout.

**Harder:**

- Two artefacts must stay in sync at release time: the package
  version on PyPI and the skill folder's expectation of which
  `circuitsmith` API surface exists. A consumer who pins an old
  package against a new skill folder hits a version mismatch.
- The skill folder loses its "the view is the deliverable" property
  from ADR-0007 — a reader who only sees `.claude/skills/circuit/`
  no longer sees the library. They have to follow the import
  trail into `src/circuitsmith/`.
- Tests now require an editable install (`pip install -e .[dev]`)
  rather than the `sys.path` splice
  [tests/conftest.py:14-16](../../../tests/conftest.py#L14-L16)
  used under ADR-0007. The splice is deleted as part of the
  refactor.

## See also

- [ADR-0007](0007-skill-directory-is-the-library.md) — superseded
  by this ADR.
- [`idea-002-consolidate-skill-python-into-central-module.md`](../ideas/archived/idea-002-consolidate-skill-python-into-central-module.md)
  — the full dossier, including the decision rationale,
  module-layout target, and the five-phase execution plan.
- [EPIC-010](../tasks/active/epic-010-circuitsmith-package.md) —
  the execution epic.
- [EPIC-006](../tasks/open/epic-006-circuit-skill-packaging.md) —
  rewritten in place to publish the package to PyPI rather than
  copy the folder; see TASK-076 § "Rewrite EPIC-006 in place".
