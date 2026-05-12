# Changelog

All notable changes to CircuitSmith are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) at
a relaxed cadence — bullet lists per release, no per-PR enumeration. The
project version follows [Semantic Versioning](https://semver.org/) once the
first tag is cut; until then the `[Unreleased]` section is the only entry.

## [Unreleased]

### Bootstrap

- Repository initialised from the IDEA-027 dossier in
  [AwesomeStudioPedal](https://github.com/tgd1975/AwesomeStudioPedal).
- Task system installed (45 → 49 open tasks across 7 epics).
- Pre-commit hook + `/commit` wrapper for atomicity and message-policy
  enforcement.
- Security-review git hooks (`pre-merge-commit`, `post-merge`, `pre-rebase`)
  ported from AwesomeStudioPedal; install via `bash scripts/install_git_hooks.sh`.

### Tooling

- TASK-046 closed: `pyproject.toml` (`requires-python = ">=3.11"`) and
  `requirements-dev.txt` landed — first Phase 0 prerequisite for EPIC-001
  cleared.
- TASK-047 closed: pytest configured (`testpaths = ["scripts/tests"]`,
  `python_files = "test_*.py"`, `addopts = "-ra"`, `strict_markers = true`).
  Pytest 9.0.2 silently drops `--strict-markers` from `addopts`, so the
  flag is set as a proper ini option. 114 tests discovered and green.
- TASK-048 closed: GitHub Actions CI workflow at
  `.github/workflows/ci.yml` — runs on `ubuntu-latest` and
  `windows-latest`, mirroring the pre-commit hook (markdownlint + pytest)
  so a `CS_COMMIT_BYPASS` cannot land broken code.
- TASK-061 closed: `ruff` adopted as the Python linter — minimal initial
  ruleset (`select = ["E4", "E7", "E9", "F"]`). Wired symmetrically into
  `pyproject.toml`, `scripts/pre-commit`, the `/commit` fixer registry
  (`*.py → ruff check --fix <files>`), and the `.claude/settings.json`
  allowlist. Baseline cleanup of `scripts/` — 10 findings fixed (4
  auto-fixed unused imports + 1 multi-import line; 6 `E741` ambiguous
  `l` in `test_housekeep.py` renamed to `ln`).
- **EPIC-007 (Project Bootstrap) closed** — all attributed tasks done.
- Pre-commit hook: exclude `.claude/security-review-latest.md` from the
  markdownlint glob. The file is gitignored runtime state written by
  the security-review hook on every merge; markdownlint-cli2 doesn't
  consult `.gitignore`, so the exclude is set explicitly.

### Planning

- EPIC-008 (Architecture Fitness Functions and Governance) scaffolded
  with the Phase 2b trigger-gate tasks (TASK-049..059) — structural
  KiCad netlist test, portability lint, schema-validation pre-commit,
  netgraph golden-hash contract, ADR seed, and the
  `check-phase2b-trigger` release gate.
- TASK-060 scaffolded — seed for autonomous-implementation mode
  (AUTONOMY.md protocol, `/epic-run` driver, branch hygiene, HIL sweep)
  to drive EPIC-007 end-to-end as the first pilot.
- TASK-060 body extended with the planned `sed/awk/head/tail` deny
  entries for `.claude/settings.json` (observed during the EPIC-007
  pilot run) and a note that the existing allowlist is non-empty
  contrary to the original description.

### Policy

- `CLAUDE.md`: forbid diagnostic suffixes (`; echo "EXIT=$?"`,
  `&& echo OK`) on Bash invocations — the permission-allowlist matcher
  checks the whole command string, so the suffix would force a prompt
  even when the primary command is allowed.
- `CLAUDE.md`: forbid end-of-turn "continue?" checkpoints. The agent
  keeps going until the requested scope is done or a real stop-line is
  hit; the user suspends via laptop lid, not via question.
- `CLAUDE.md`: branch merges to `main` are **squash-merged** (one
  commit per branch, named for the branch's primary purpose) — never
  plain fast-forward.
- `CLAUDE.md`: `CHANGELOG.md` `[Unreleased]` is updated **as part of
  the same squash commit** that lands the work, not in a follow-up.
- `scripts/security_review_changes.py`: `ruff` added to the
  CRITICAL → HIGH demotion list for `permissions-allow-added` findings
  (alongside `git/grep/ls/python3/jq/...`). The demotion list is now
  annotated with a paragraph explaining the single-developer
  assumption and an explicit re-audit trigger for whenever an
  additional developer joins the project.

### Developer experience

- VSCode workspace: subtle copper window accent for visual identification
  of CircuitSmith windows (`titleBar.activeBackground` etc. in
  `.vscode/settings.json`).

### Governance (EPIC-008 unblocked slice)

- TASK-054 closed: `docs/developers/adr/` seeded with eight foundational
  ADRs (slots-not-coordinates, AI-at-authoring-time-only, NetGraph as
  shared contract, exporter decoupling, ERC pre-layout, rule catalog
  authoritative, skill directory is the library, Phase 2b on evidence)
  plus a README documenting the format, the add/supersede procedure,
  and the index.
- TASK-051 closed: `scripts/portability_lint.py` enforces the
  portability contract for `.claude/skills/circuit/` — no host-project
  paths, no project-module imports, no host-project name references.
  `.portability-allow.txt` carries auditable exceptions. Wired into
  the pre-commit hook (only fires on staged changes inside the skill
  dir) and the GitHub Actions workflow (unconditional). 18
  fixture-based tests cover each forbidden pattern, the `docs/`
  exception for sibling-project names, the allow-list resolver, and
  the empty/missing-dir no-op.
- TASK-055 closed: code-owner skills mechanism. `.claude/codeowners.yaml`
  registry binds file globs to `co-<name>` skills;
  `scripts/codeowner_hook.py` (registered under `hooks.PreToolUse` in
  `.claude/settings.json` with `matcher: "Edit|Write"`) prints the
  matched skill's body as an informational reminder. Glob syntax is
  gitignore-flavoured (`**`/`*`/`?` segment-aware); stdlib-only YAML
  parser keeps the per-edit overhead minimal. 26 tests cover the
  parser, matcher, body extractor, and the full `run()` flow.
  Documentation in `docs/developers/CODE_OWNERS.md`.
- TASK-056 closed: first three code-owner skills authored —
  `co-netgraph`, `co-schema`, `co-erc-engine` — each binding to its
  high-blast-radius module via the registry and declaring invariants
  as a checklist (hash determinism, schema-version bump on break,
  stable check IDs, etc.). Registered in `.vibe/config.toml`.
  Subsequent code-owner skills (`bom_exporter`, `netlist_exporter`,
  `knowledge/rules.json`, `layout_engine/kernel.py`) land alongside
  the modules they bind, not upfront.

EPIC-008 is partially closed: the four unblocked tasks above are done;
TASK-050 / TASK-052 / TASK-053 remain open until their respective
feature-epic deliverables land.

### Autonomy

- TASK-060 closed: autonomous-implementation mode wired up.
  - `docs/developers/AUTONOMY.md` codifies the four HIL values
    (`No` / `Clarification` / `Support` / `Main`) with defined agent
    behaviours, the epic-driver loop, the definition-of-done
    checklist, the review-packet format, the ADR-on-ambiguity rule,
    and the deny-vs-prompt split for published-effect actions.
  - `docs/developers/adr/0000-template.md` seeds a maintained blank
    ADR for future records.
  - `docs/developers/adr/0009-autonomous-implementation-mode.md`
    records the protocol's own decision.
  - `CLAUDE.md` gains a `## Autonomy` section pointing at
    AUTONOMY.md and stating that `human-in-loop:` is the
    operational contract.
  - `.claude/skills/epic-run/SKILL.md` is the protocol-scaffold
    driver skill the agent follows (composer over `/ts-task-active`,
    `/commit`, `/housekeep`, `/ts-task-done`, `/check-branch`).
  - `.claude/settings.json` `permissions.deny` extended with
    `Bash(sed:*)`, `Bash(awk:*)`, `Bash(head:*)`, `Bash(tail:*)`,
    `Bash(git push:*)`. `gh pr create` / `gh pr merge` are
    deliberately **not** in deny — they go through the
    prompt-by-default path so the user can approve per-invocation.
  - HIL sweep applied across 15 open tasks: 7 `Clarification` → `No`
    (TASK-001/009/012/014/019/022/036), 2 `Main` → `Support`
    (TASK-024 rule catalog, TASK-039 SKILL.md prompt), 6 `Main`
    kept (TASK-015/034/041/043/044/045). Each task gains a one-line
    `## Autonomy` rationale.
  - Open epic files (EPIC-001..006, EPIC-008) carry a
    `release/epic-NNN-<slug>` `branch:` field — `/ts-task-active`
    nags on mismatch with the `[c]ontinue` rewrite path.

### Documentation (EPIC-009 — Developer Docs and Governance Scaffolding)

- TASK-062 closed: `docs/developers/DEVELOPMENT_SETUP.md` — canonical
  first-time-setup walk-through. Tool prerequisites, Ubuntu / Windows 11
  install procedure, smoke-test, common-setup-problems appendix.
  `CONTRIBUTING.md` redirects to this doc.
- TASK-063 closed: `docs/developers/TESTING.md` — three conceptual test
  layers (unit / integration / contract / golden), pytest convention,
  `pyproject.toml` `testpaths` updated to `["tests", "scripts/tests"]`.
  Coverage tooling deferred until product code lands.
- TASK-064 closed: `docs/developers/CODING_STANDARDS.md` — naming,
  formatting (ruff), comment-WHY policy, public-function type-hint
  requirement.
- TASK-065 closed: `docs/developers/CI_PIPELINE.md` — inventory of the
  `ci.yml` workflow, gate semantics (all jobs blocking), local pre-commit
  hook mirror, red-build response sequence, known gap (ruff not yet in CI).
- TASK-066 closed: `docs/developers/TASK_SYSTEM.md` — human-facing
  counterpart to `AUTONOMY.md`. IDEA/EPIC/TASK artefacts, lifecycle
  states, every `/ts-*` skill catalogued, `/housekeep` role.
- TASK-067 closed: `docs/developers/CODE_OF_CONDUCT.md` — short custom
  CoC mirroring AwesomeStudioPedal's shape (not verbatim Contributor
  Covenant 2.1 — user override at activation). Enforcement contact is
  GitHub-routed ("contact the owner of the repository via GitHub"), no
  personal email anywhere in committed files. `pyproject.toml`
  `authors` field stripped of email.
- TASK-068 closed: `docs/developers/ARCHITECTURE.md` — top-down view.
  Mermaid pipeline (`flowchart LR`) and module-boundary graph
  (`graph TD`) with the three forbidden edges marked red dashed. Module
  table linking each module to its ADR(s) and code-owner skill.
  README's architecture section summarised down with link.
- TASK-069 closed: `docs/developers/MERMAID_STYLE_GUIDE.md` —
  diagram-type selector, palette, edge conventions, node-label rules,
  mandatory prose summary alongside every mermaid block for
  accessibility.
- TASK-070 closed: `docs/developers/SECURITY_REVIEW.md` — usage of
  `scripts/security_review_changes.py` and the three security-review
  hooks, reviewer checklist (secrets / shell-exec / path-traversal /
  dependency / permissions-allow / gh-PUT / skills / CI), bypass
  policy, escalation path.
- TASK-071 closed: `docs/developers/COMMIT_POLICY.md` — pathspec
  rationale with the concrete two-session race story, provenance-token
  mechanics, three-check hook-failure protocol, `CS_COMMIT_BYPASS`
  policy, squash-merge + CHANGELOG-rides-along rule, LLM-attribution
  trailer ban.
- TASK-072 closed: `docs/developers/BRANCH_PROTECTION_CONCEPT.md` —
  ruleset and rationale for GitHub server-side branch protection on
  `main` (status checks required, linear history, no force-push, no
  deletion; PR review off for solo posture with contributor-#2 flip
  trigger documented; admin enforcement off).
- TASK-073 closed: GitHub branch protection applied on
  `tgd1975/CircuitSmith/main` via `gh api --method PUT
  /repos/.../branches/main/protection --input <body>`. As-applied
  configuration matches `BRANCH_PROTECTION_CONCEPT.md` 1:1.
- TASK-074 scaffolded under EPIC-008 (architecture fitness functions):
  extend the security-review hook to mechanically detect personal-
  contact-info leaks (email / phone / real name beyond the GitHub
  handle). Surfaced from the TASK-067 user override; `feedback-no-
  personal-contact-in-docs` memory rule recorded.
- **Skill updates:** `/status` rewritten to four parallel Bash calls
  (printf-chained compound defeated the allowlist); `/housekeep` no
  longer runs `git add` (staging rides with the next `/commit`
  pathspec); `/epic-run` protocol gains a **Hand-off phase**
  (bundles the HIL stop-line task with the commit phase into one
  user-interaction block) and a **CHANGELOG-delta phase** (appends
  the run's missing entries to `[Unreleased]`, never edits or
  removes).
- **VS Code workspace palette refreshed** to dark orange
  (`titleBar.activeBackground: #4A2810`) — replaces the prior
  copper-toned palette while keeping the per-project visual
  identification pattern.
- **EPIC-009 closed** — all 12 tasks done. The first-day-junior
  documentation set + server-side branch protection are in place
  before EPIC-001 implementation work begins.

Nothing under `.claude/skills/circuit/` exists yet — see
[EPIC-001..006](docs/developers/tasks/EPICS.md), `Phase 0` (EPIC-007),
and the governance gates in [EPIC-008](docs/developers/tasks/EPICS.md).
