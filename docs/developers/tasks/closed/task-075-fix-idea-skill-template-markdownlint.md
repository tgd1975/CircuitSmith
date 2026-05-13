---
id: TASK-075
title: Fix /ts-idea-new template so generated files pass markdownlint on first run
status: closed
closed: 2026-05-13
opened: 2026-05-13
effort: Small (<2h)
effort_actual: Small (<2h)
complexity: Junior
human-in-loop: No
---

## Description

Idea files scaffolded by `/ts-idea-new` consistently fail `markdownlint-cli2`
on the first lint pass after creation, forcing a manual fixup step before
the file can be committed cleanly. The fault is in the skill template
itself ([`.claude/skills/ts-idea-new/SKILL.md`](../../../../.claude/skills/ts-idea-new/SKILL.md)),
not in user-authored content: the angle-bracket placeholders, the H1
duplication of the frontmatter `title`, and the surrounding blank-line
hygiene render a file shape that violates rules enabled in the project's
[`.markdownlint.json`](../../../../.markdownlint.json).

Fix the template so that the *unmodified scaffolded file* (i.e. before the
user has typed any body content) lints clean against the project config.
Any required user-fill placeholders should be expressed in a form that
markdownlint does not flag (HTML comments, code fences, or removed
entirely in favour of an empty section the user fills in).

## Acceptance Criteria

- [x] After running `/ts-idea-new "Some title"`, running `markdownlint-cli2`
      against the generated file reports zero errors with the project's
      `.markdownlint.json` config.
- [x] The `/ts-idea-new` SKILL.md template is updated in place; the workflow
      steps still produce a frontmatter + body file under
      `docs/developers/ideas/open/`.
- [x] The same scan is applied to `/ts-task-new` and `/ts-epic-new`; if
      either exhibits the same first-run failure, fix it under this task
      too. Note in the task body which siblings were also touched.

## Test Plan

No automated tests required — change is non-functional. Manual verification:
scaffold a throwaway idea via `/ts-idea-new`, run `markdownlint-cli2` against
the new file, confirm zero errors, then delete the throwaway before committing.

## Notes

- The project allows angle-bracket inline HTML by default (MD033 is not
  disabled globally but is disabled per-file in some generated files).
  Confirm whether the failure is MD033, MD025 (top-level heading
  duplicated by `title:` frontmatter), MD022/MD031/MD032 (blank-line
  hygiene around headings/fences/lists), or something else before
  deciding the fix shape — the right move depends on which rule is firing.
- Keep the template friendly to the scaffolding model: placeholders must
  still be unambiguous prompts to fill in (`<title>` is clearer than a
  bare blank line). A `<!-- TODO: ... -->` comment is one option that
  threads the needle.
- Sibling skills `/ts-task-new` and `/ts-epic-new` use a similar
  template shape — worth checking them in the same pass even if this
  task's title only names `/ts-idea-new`.

## Resolution

Two rules were firing:

- **`/ts-idea-new`** — MD025 (`Multiple top-level headings`). The
  template emitted a body `# <title>` H1 after the frontmatter
  `title:`, which is itself rendered as an H1. Fix: drop the body H1
  and start the body with the placeholder comment, matching the
  pattern already used by `/ts-epic-new`.
- **`/ts-task-new`** — MD033 (`Inline HTML`). Angle-bracket
  placeholders like `<expanded description with context and purpose>`
  were parsed as HTML tags (`<expanded …>`) and rejected. Fix: convert
  those placeholders to HTML comments (`<!-- … -->`) or italicised
  inline text (`_… _`) — both render invisibly to readers but lint
  clean. Existing user-supplied `# <Heading>` patterns elsewhere are
  not affected; only the scaffold-time placeholders changed.
- **`/ts-epic-new`** — already clean; the body never carried an H1
  and used no `<word…>` placeholders. No changes were made.

Verification: scaffolded fixtures matching each template's literal
output lint clean against the project `.markdownlint.json`.
