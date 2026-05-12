---
id: TASK-067
title: Adopt and commit docs/developers/CODE_OF_CONDUCT.md (short custom CoC mirroring AwesomeStudioPedal)
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
epic: developer-docs-governance
order: 6
---

## Description

The repo is MIT-licensed, public, and intended to grow contributors
(Phase 7 extracts the skill into a standalone repo with its own
collaborators). A Code of Conduct is standard practice for any
public collaborative repo — GitHub Insights flags its absence in the
"community profile" checklist, and many contributors check for one
before submitting a PR.

Adopt [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)
verbatim — the project does not have grounds (or evidence) to deviate
from the de-facto standard, and inventing a custom CoC is a
maintenance burden no one wants.

## Acceptance Criteria

- [x] `docs/developers/CODE_OF_CONDUCT.md` exists. *Superseded by user direction: short custom CoC mirroring AwesomeStudioPedal's pattern, not verbatim Contributor Covenant 2.1.*
- [x] Enforcement contact is GitHub-routed ("contact the owner of the repository via GitHub"). *Superseded by user direction: no personal email in committed files.*
- [x] `README.md` and `CONTRIBUTING.md` each link to the CoC.
- [x] GitHub's "community profile" page reflects the CoC after merge. *(Pending merge to `main`.)*

## Test Plan

No automated tests. Verify the CoC renders correctly in GitHub
preview, the email contact resolves to a real inbox, and the
community-standards page shows the green check.

## Prerequisites

None — boilerplate adoption.

## Notes

If the user prefers a project-specific enforcement email rather than
their personal address, surface that as the one
clarification-question at task activation (HIL: No, but the email
choice is the kind of one-decision item where a quick batched question
beats an ADR). Default if no preference is stated: the recorded user
email.

The Phase 7 standalone-repo extraction (EPIC-006) inherits this CoC
verbatim — no per-repo customisation.

## Closure notes

User overrode two of the task body's directives at activation:

1. **Custom short CoC, not verbatim Contributor Covenant 2.1.** Mirrors
   AwesomeStudioPedal's CoC structure (27 lines, in-short / expected /
   not-acceptable / enforcement / scope). Maintenance burden is the same
   either way; consistency with the sister project wins. Memory rule
   recorded: `feedback-mirror-awesomestudiopedal.md`.
2. **No personal email anywhere in committed files.** Enforcement
   clause uses "contact the owner of the repository via GitHub";
   `pyproject.toml` authors field drops the email field, keeping just
   the name. Memory rule recorded:
   `feedback-no-personal-contact-in-docs.md`. Follow-up scaffolded as
   TASK-074 (a pre-commit lint to mechanically enforce the no-email
   rule).
