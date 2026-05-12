---
id: TASK-067
title: Adopt and commit docs/developers/CODE_OF_CONDUCT.md (Contributor Covenant 2.1)
status: open
opened: 2026-05-12
effort: Small (<2h)
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

- [ ] `docs/developers/CODE_OF_CONDUCT.md` exists with Contributor Covenant 2.1 verbatim text, attribution preserved.
- [ ] Enforcement contact is set: project owner email (`t.deutsch.75@gmail.com` per the user's recorded identity, unless the user prefers a project-specific alias).
- [ ] `README.md` and `CONTRIBUTING.md` each link to the CoC in their respective footer / contributing sections.
- [ ] GitHub's "community profile" page (Insights → Community Standards) reflects the CoC after merge.

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
