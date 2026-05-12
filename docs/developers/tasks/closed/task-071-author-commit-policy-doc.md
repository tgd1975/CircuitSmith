---
id: TASK-071
title: Author docs/developers/COMMIT_POLICY.md (pathspec rationale, race story, bypass policy)
status: closed
opened: 2026-05-12
closed: 2026-05-12
effort: Medium (2-8h)
effort_actual: Small (<2h)
complexity: Medium
human-in-loop: No
epic: developer-docs-governance
order: 10
---

## Description

The commit policy lives as a one-paragraph rule in
[`CLAUDE.md`](../../../../CLAUDE.md) (`## Commits go through /commit
— always`) plus three lines in
[`CONTRIBUTING.md`](../../../../CONTRIBUTING.md). That is enough for
an agent to follow the rule but **not enough for a human to
understand why**. A contributor who hits a pre-commit hook failure,
or who is tempted by muscle-memory `git commit -am`, needs to know:

- Why pathspec, not `git add` + `git commit`?
- Why is the rule load-bearing rather than advisory?
- Why does the pre-commit hook validate a token rather than just
  running its checks?
- When is `CS_COMMIT_BYPASS` legitimate, and what gets logged?
- What does the "three-check protocol" for hook failures actually
  look like?

ASP's
[`COMMIT_POLICY.md`](../../../../../AwesomeStudioPedal/docs/developers/COMMIT_POLICY.md)
(244 lines) is the model — it tells the race-condition story
explicitly (two concurrent Claude sessions clobbering each other's
indexes), explains the pathspec property that fixes it, and documents
every bypass with its log location.

## Acceptance Criteria

- [x] `docs/developers/COMMIT_POLICY.md` exists and is linked from CLAUDE.md (`## Commits go through /commit — always` → "Rationale: COMMIT_POLICY.md") and from CONTRIBUTING.md.
- [x] The pathspec rationale is explained with a worked example of the race-condition failure mode the rule prevents.
- [x] The one-shot-token mechanism (`.git/cs-commit-token` written by `scripts/commit-pathspec.sh`, validated by the pre-commit hook) is documented end-to-end so a contributor can read the hook source and follow.
- [x] The three-check hook-failure protocol from `.claude/skills/commit/SKILL.md` is transcribed (or linked + summarised) so it is discoverable from the doc.
- [x] Bypass policy: `CS_COMMIT_BYPASS="<reason>"` is logged to `.git/cs-commit-bypass.log`; the doc names which scenarios are legitimate (interactive rebase, recovery from broken `/commit`, manual repo surgery) and which are not (silencing a hook to land work).
- [x] Squash-merge + CHANGELOG-rides-along policy is transcribed from CLAUDE.md so a contributor can find it without re-reading the agent file.
- [x] LLM-attribution-trailer ban (`Co-Authored-By: Claude …`) is recorded with rationale.

## Test Plan

No automated tests. Manual: a contributor reading the doc cold should
be able to answer four questions: (1) why pathspec, (2) how do I
recover from a hook failure that flags unrelated files, (3) when is
bypass acceptable, (4) why does the project squash-merge.

## Prerequisites

None — the policy is already in force; this task documents it.

## Notes

The framing "implicit knowledge is no knowledge" from the project
owner is the operating principle here. Every rule in CLAUDE.md that
applies to humans should appear in this doc with its *reason*, not
just its statement. Where the rule is identical (LLM-attribution ban,
squash-merge), the doc can quote CLAUDE.md verbatim and link back;
where the rationale is non-obvious (pathspec, token-validation), the
doc owns the depth.

The race-condition story is the heart of this doc. Tell it
concretely (two sessions, named files, the sequence of git commands)
rather than abstractly — it is the one piece of context that makes
the pathspec rule self-evidently correct.

## Sizing rationale

Medium because the pathspec mechanics + token-validation flow + the
race-condition narrative each require careful prose. The rest is
transcription from CLAUDE.md.
