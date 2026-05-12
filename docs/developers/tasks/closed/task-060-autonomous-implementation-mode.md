---
id: TASK-060
title: Set up autonomous-implementation mode (AUTONOMY.md, /epic-run, HIL sweep, branch hygiene)
status: closed
closed: 2026-05-12
opened: 2026-05-12
effort: Large (8-24h)
effort_actual: Medium (2-8h)
complexity: Senior
human-in-loop: Clarification
---

## Description

The user wants epic implementation to run with minimal involvement:
brief at the start, review at the end, intervene only on rare
occasions in between. The task system already has the necessary
mechanical pieces (`/ts-task-active`, `/ts-task-done`, `/housekeep`,
`/commit`, `/check-branch`, `human-in-loop` labels), but the
operational protocol that turns them into an autonomous-epic loop is
missing.

This task is the seed: it produces the protocol, the driver skill,
the branch convention, the ADR machinery, and the HIL re-classification
needed before the first autonomous epic run (EPIC-007).

## Decisions already made (this conversation)

1. **First pilot epic:** EPIC-007 (Project Bootstrap). Finish TASK-047
   and TASK-048 autonomously to prove the loop end-to-end before
   committing to a larger epic. Smallest blast radius, already active.
2. **Main-HIL tasks → "auto-prepare + pause for review."** Agent
   completes the work up to a defined stop-line, surfaces a review
   packet, then waits. KiCad-GUI and remote-push steps stay genuinely
   manual.
3. **Mid-epic ambiguity → decide + ADR + continue.** Agent picks the
   most defensible option, files an ADR under `docs/developers/adr/`,
   keeps moving. ADRs are reviewed in batch at the stop-line.

## Why this is needed (audit findings)

A read of all 58 open tasks plus the active epic surfaced these gaps:

- **HIL labels are decorative, not operational.** 9 tasks tagged
  `Main`, 8 tagged `Clarification` — no document defines what the
  agent does when it sees those values. Without a contract, every
  ambiguity becomes a question.
- **No epic driver.** `/ts-task-active` activates one task; nothing
  sequences an epic. The agent has to re-derive "what's next?" from
  prerequisites + order on every iteration.
- **EPIC-007 sits on `branch: main`.** `/check-branch` will block
  every commit. Every other epic file lacks a `branch:` field.
  Without per-epic branches the cutover-PR rule (e.g. TASK-015) and
  the rollback story break.
- **No ADR folder.** The "decide + ADR + continue" rule needs a
  destination. TASK-054 is the planned seed but sits behind several
  other tasks; the autonomy loop needs it on day one.
- **No permissions allowlist.** `.claude/settings.json` is empty.
  Routine `pytest` / `python scripts/housekeep.py` / `git status`
  calls will trigger interactive permission prompts during a long
  autonomous run.
- **No "definition of done" gate.** Closing a task today is whatever
  the agent decides. Autonomous loops need a checklist that always
  runs (acceptance criteria checked, tests pass, /housekeep clean,
  /commit succeeds without bypass).

## Acceptance Criteria

- [x] `docs/developers/AUTONOMY.md` exists and codifies, in
      operational terms: HIL semantics (No / Clarification / Support /
      Main with the user-chosen rules), the epic-driver loop, the
      per-task definition of done, the stop-line review-packet
      format, the ADR-on-ambiguity rule, the no-push-without-approval
      rule.
- [x] `docs/developers/adr/` is seeded with `0000-template.md` (MADR-lite:
      Status / Context / Decision / Consequences) and
      `0009-autonomous-implementation-mode.md` recording this task's
      own decisions. (Note: this AC said `0001-autonomous-implementation-mode.md`
      but ADRs 0001–0008 were already allocated by TASK-054 for the
      foundational dossier decisions; the autonomous-implementation
      record lands as `ADR-0009` instead.) Folder is referenced from
      `AUTONOMY.md` and `CLAUDE.md`.
- [x] `CLAUDE.md` has a new "## Autonomy" section pointing at
      `docs/developers/AUTONOMY.md` and stating that `human-in-loop`
      is the operational contract, not a label.
- [x] An `/epic-run` skill exists (registered in `.vibe/config.toml`
      `enabled_skills`) that reads an epic file, walks tasks in
      `prerequisites + order` topological order, and for each task:
      activates → implements → runs tests → commits via `/commit` →
      marks done. It pauses at the next Main-HIL stop-line with a
      review packet and exits. (Implemented as a protocol-scaffold
      SKILL.md the agent follows — a future iteration may extract
      the loop into a Python driver; see the skill's "Status" section.)
- [x] Every open task with `human-in-loop: Main` or `Clarification`
      is swept; each one's HIL value is either kept (with a one-line
      `## Autonomy` rationale in the body) or downgraded. **Applied
      sweep (confirmed by user 2026-05-12):** **Concrete
      proposed sweep — to be confirmed in one batched user decision
      before the rewrite lands:**
  - **Keep Main** (irreversible / physical / remote-push):
    TASK-015 (cutover PR), TASK-034 (KiCad GUI import),
    TASK-041 (interactive five-test session),
    TASK-043 / TASK-044 / TASK-045 (standalone-repo extraction + push).
  - **Keep Main but auto-prepare + pause for review** (operationally
    autonomous up to the stop-line, just needs a maintainer-eyes pass):
    TASK-024 (rule catalog prose), TASK-039 (SKILL.md system prompt).
  - **Downgrade Clarification → No** (ADR-on-ambiguity rule applies):
    TASK-001, TASK-009, TASK-012, TASK-014, TASK-019, TASK-022,
    TASK-036, TASK-048.
- [x] Each open epic file has a `branch:` field that is **not** `main`
      (scheme: `release/epic-NNN-<slug>`). EPIC-007 closed under the
      old convention with `epic-007-project-bootstrap`; the
      `release/` prefix was introduced for EPIC-008 onward and the
      remaining open epics (001..006) follow the new scheme.
- [x] `.claude/settings.json` is created with: an `allow` list for the
      routine commands the loop runs (pytest, `python scripts/housekeep.py`,
      `git status` / `diff` / `log`, `ls`, `grep`, `cat` of generated
      indexes); a `deny` list for `git push`, `gh pr merge`, and any
      `--no-verify` / `CS_COMMIT_BYPASS` invocation so a remote push
      or hook bypass cannot happen without explicit user approval.
      Additionally — observed during the EPIC-007 pilot (2026-05-12) —
      add `Bash(sed:*)`, `Bash(awk:*)`, `Bash(head:*)`, `Bash(tail:*)`
      to the deny list so file slicing/editing routes through the
      Read/Edit tools per the CLAUDE.md "use dedicated tool" rule.
      Leave `cat` out of the deny list — `cat <<'EOF' ... EOF`
      heredocs are load-bearing in the `/commit` wrapper invocation.

      **Outcome:** allow list already populated; deny list extended
      with `Bash(sed:*)`, `Bash(awk:*)`, `Bash(head:*)`, `Bash(tail:*)`,
      `Bash(git push:*)`. `gh pr create` / `gh pr merge` left **out**
      of the deny list per user direction — they go through the
      harness's prompt-by-default path so the user can approve
      per-invocation when they do want the agent to run them. The
      AUTONOMY.md "No-published-effect-without-approval" section
      documents the deny-vs-prompt split.
- [x] Each epic file gains a documented `## Implementation log`
      convention (one append-only line per closed task: date, task ID,
      ADRs filed, anything notable). Documented in `AUTONOMY.md`;
      `housekeep.py` does not need to maintain it. (Convention
      documented in AUTONOMY.md `## Implementation log`. Existing
      epic files do not retroactively gain the section; the agent
      adds it on first task closure under the new protocol.)
- [x] A definition-of-done checklist is written into `AUTONOMY.md`
      and the `/epic-run` skill enforces it before invoking
      `/ts-task-done`.

## Implementation notes (closure)

- **HIL sweep applied verbatim** to the proposed table (user
  confirmed 2026-05-12 via batched AskUserQuestion). 15 tasks
  touched: 7 `Clarification` → `No`, 2 `Main` → `Support`, 6 `Main`
  kept. TASK-048 fell off the list (already closed during EPIC-007).
- **`/epic-run` is a protocol-scaffold skill**, not an executable
  driver — the agent follows the SKILL.md's contract directly.
  A Python driver that orchestrates the underlying skills
  explicitly is a possible follow-up; deferred per the task body's
  "composer over existing skills, not re-implementation" rule.
- **ADR numbering correction:** the AC mentioned
  `0001-autonomous-implementation-mode.md`. TASK-054 had already
  allocated ADR-0001..0008 for the foundational dossier decisions,
  so the autonomous-implementation record lands as **ADR-0009**.
  The AC's intent (an ADR exists for this protocol) is satisfied.
- **`gh pr` not denied** per user direction during the implementation
  ("sometimes I want you to do it"). Updated AUTONOMY.md and
  CLAUDE.md to describe the deny-vs-prompt split: hard-deny for
  things that are never OK, prompt-by-default for things that are
  sometimes OK with explicit approval.
- **Implementation log convention** is documented but not
  retroactively applied to existing epic files (EPIC-007 already
  closed; EPIC-008 will gain the section on its next task closure
  under the new protocol).
- **EPIC-007 branch convention exception:** EPIC-007 closed under
  `epic-007-project-bootstrap` (no `release/` prefix) before this
  protocol existed. The `release/epic-NNN-<slug>` scheme starts
  with EPIC-008 going forward.

## Test Plan

The pilot epic (EPIC-007) is the integration test. After this task
closes:

1. User invokes `/epic-run EPIC-007` once.
2. Agent walks TASK-047 → TASK-048 to completion on branch
   `epic-007-bootstrap`. No Main-HIL stop-line is hit.
3. Agent presents an end-of-epic review packet with: branch name,
   per-file diff summary, test status, ADRs filed (if any), open
   questions (if any).
4. User reviews and either approves the merge or sends the agent
   back with concrete fixes.

Pass criterion for *this* task: the EPIC-007 run completes without
the user having to issue any task-management commands (`/ts-task-active`,
`/ts-task-done`, `/housekeep`, `/commit`) during the run itself.

## Notes

- This is the only task in this batch where the user is heavily
  involved. From the next epic onward the contract is "brief +
  review", not "drive".
- `/epic-run` is a composer over existing skills (`/check-branch`,
  `/ts-task-active`, `/commit`, `/housekeep`, `/ts-task-done`,
  `/security-review`) — it does not re-implement state transitions.
- The HIL sweep deliberately keeps every step where automation would
  be a real risk (cutover, KiCad GUI, remote-push) as Main.
  Autonomy is about removing *needless* user involvement, not
  pretending physical-world steps don't exist.
- The ADR seed supersedes TASK-054 as the seed step. TASK-054
  remains open as "fill in the foundational decisions from the
  IDEA-001 dossier", which is content work, not infrastructure.
- The branch-rename for EPIC-007 should happen as the first commit
  on the new branch — `/ts-task-active` already nags on epic/branch
  mismatch and offers `[c]ontinue` which rewrites the epic frontmatter
  in place. Use that path so the rewrite is uncontroversial.
- This task explicitly does **not** introduce CI-level enforcement
  of the autonomy protocol (no GitHub Actions check that gates on
  ADR presence, no hook that rejects commits without an
  `## Implementation log` entry). Those are tightening moves; do
  them only after the pilot epic shows the protocol holds in
  practice.

## Sizing rationale

Sized Large because the deliverables are six independent artifacts
(AUTONOMY.md, ADR seed + template, `/epic-run` skill,
`.claude/settings.json` allow/deny, HIL sweep across 17 tasks, epic
branch rename across 8 epics) plus a CLAUDE.md amendment. Splitting
into smaller tasks would just create coordination overhead — every
piece needs the others to be useful, and the user has explicitly
asked to minimise their involvement.
