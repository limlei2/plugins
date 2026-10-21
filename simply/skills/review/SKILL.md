---
name: review
description: "Pipeline stage after /simply:tdd or /simply:subagents: the main agent checks every task's diff against its brief, re-runs its Checks, writes review.md, then opens the PR(s) or sends findings back to /simply:plan. Start a run with /simply:start."
disable-model-invocation: true
---

# Review

Check every task of a pipeline run yourself, then ship it or send it back. You (the main agent) review; spawn no reviewer (rule: `rule-spend-review-where-mistakes-are-expensive`).

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

**Plugin root:** if `${CLAUDE_PLUGIN_ROOT}` appears literally in this file (you opened it with Read during a hand-off, so nothing filled it in), it means the folder two levels above this `SKILL.md`, e.g. `/…/simply` for `/…/simply/skills/plan/SKILL.md`. Substitute that absolute path everywhere below before running any command; the shell does not set this variable.

Run state lives in files: read and write it only through `run_state.py`, in the format in `${CLAUDE_PLUGIN_ROOT}/skills/start/references/run-format.md` (rule: `rule-state-lives-in-files`).

`run_state.py` below means `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/run_state.py`. An angle-bracket value (`<run>`, `<repo root>`, `<default>`) is what an earlier command printed: run that command on its own, then write the printed value literally. Each Bash call starts a fresh shell, so a shell variable would have to be rebuilt in every call.

**Commands:** write every file (reports, briefs, `design.md`, PR bodies) with the Write tool, never `cat > … <<EOF`, `echo >`, or `printf >`. One step per Bash call: no `cd "$PWD"`, and don't chain unrelated steps with `;` or `&&`. Commit messages go in separate `-m` flags with no newline inside a quote: `git commit -m "<subject>" -m "Co-Authored-By: …"`. Why: Claude Code can't check heredocs or multi-line quoted strings, so each such call stops the run for a permission prompt the user can't permanently allow.

## Limits

Hard limits. Never exceed them, even if the run implies more.

| Limit | Value | Why |
| --- | --- | --- |
| Review → plan loops per run | 2 | Two rounds of fixes that still fail mean the plan or design is wrong; a third round spends tokens on the same mistake. |
| Findings per task | 5 max | More than 5 means the task needs re-planning, not a fix list; long lists bury the finding that matters. |
| PR body | 40 lines max | A reviewer who has the diff reads a one-minute briefing; past that they skim. |
| PRs per run | 5 max | More than 5 PRs at once is more than a person can review in one sitting. |

Over 5 findings on a task: keep the 5 that block a criterion or Check, and make the last one "re-plan this task". Over 5 PRs: stop before opening any and escalate (Step 5), since plan should never have produced more than 5 worker branches.

## Step 1. Load the run

Use the run folder you were handed. If the user typed `/simply:review` directly, find it:

```bash
git rev-parse --show-toplevel          # prints <repo root>
run_state.py latest <repo root>        # prints <run>
```

Then, with the run folder either way:

```bash
run_state.py check <run>                              # must print ok
run_state.py set <run> stage=review                   # only after check printed ok
run_state.py get <run> mode loop execute branch
```

Read `<run>/design.md` and every `<run>/tasks/<n>-<slug>.md`. Find the base every diff compares against:

```bash
git symbolic-ref --short refs/remotes/origin/HEAD     # prints origin/<default>
git fetch origin <default>
```

If `symbolic-ref` fails, run `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` instead; it prints `<default>`.

## Step 2. Check each task yourself

A report is a claim, not evidence (rule: `rule-verify-the-real-thing`). For each task file, in task-number order:

1. No `reports/<n>-<slug>.md`: verdict `changes`, finding "no report". Otherwise run `run_state.py check-report <run>/reports/<n>-<slug>.md`; any error is a finding.
2. Branch: tdd mode uses the run's `branch` for every task; subagents mode uses the report's `## Branch`. Read the diff without dumping it into your reply (rule: `rule-keep-context-lean`):
   ```bash
   git diff origin/<default>...<branch> -- <the brief's Work-in paths>
   git diff --stat origin/<default>...<branch>
   ```
3. Against the brief, each of these is a finding:
   - a criterion with no change that meets it, or with evidence that is not a real command result or file:line ("should work", a suite that never exercises it);
   - any file in `--stat` outside the brief's "Work in" (tdd mode: outside the union of all briefs' "Work in"), or any "Do not touch" file;
   - debug leftovers: `console.log`, `print`, commented-out code, added TODOs, temp files;
   - bugs, unhandled edge cases, callers of a changed symbol left unchanged (`grep` for each).
4. Re-run every command in the brief's Checks yourself on that branch: in the worktree that has it checked out (`git worktree list`), else `git switch <branch>` in a clean main checkout. A failing or skipped Check is a finding. Never weaken a Check to make it pass.
5. Report `## Escalation` not `none`: if the question is a product or preference decision (naming, UX, scope), collect it as a question for the user (Step 3). Otherwise it is a finding.

Verdict per task: `approve` with finding `ok`, or `changes` with its findings, 5 max.

Subagents mode with 3+ worker branches: also read the branches side by side for conflicts between them: duplicated helpers, inconsistent naming, a contract one branch changes and another relies on. Each conflict is a finding on the later task.

## Step 3. Write `<run>/review.md`

Exactly these sections, in this order:

```markdown
## Verdict
approve

## Tasks
| task | verdict | finding |
| --- | --- | --- |
| 1-add-validation | approve | ok |

## Changes needed
none

## Cross-task
n/a
```

- `## Verdict`: the single line `approve` or `changes`. `approve` only if every task is `approve`, every Check passed, there is no cross-task conflict, and no question is open.
- `## Changes needed`: one bullet per finding: `- task <n>: <file>:<line>: <what is wrong>; done when <what done looks like>`. Or `none`.
- `## Cross-task`: tdd mode `n/a`; subagents mode with 1–2 branches `n/a`; with 3+ branches one bullet per conflict, or `none`.

If questions were collected, ask them now in one message (rule: `rule-ask-with-context`) and wait. Questions always go to the user, never into a loop. Append each answer to `<run>/design.md` under its decisions, then continue.

## Step 4. Approve: ship

Plan the PRs: tdd mode, one PR from `branch`; subagents mode, one PR per worker branch, except a branch that a later fix task replaced: a fix brief's Constraints line `- Fix branch: <b>` means its report's branch was built on `<b>` and supersedes it, so open the PR from the newest branch in each chain only. Prompt mode: show the verdict and the PR plan (`branch | title`), then wait for **go** before pushing anything. Auto mode: continue.

For each branch:

1. Tidy history: squash fixup commits into the commit they fix (`git rebase -i` is unavailable, so run `git merge-base HEAD origin/<default>`, then `git reset --soft <that commit>`, and recommit). 5 commits max, each landable and in order.
2. Push and open the PR ready for review, never as a draft, never with a failing Check:
   ```bash
   git push -u origin <branch>
   gh pr create --head <branch> --title "<type>(<scope>): <subject>" --body-file <body.md>
   ```

**Title:** Conventional Commits. `type` is one of `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`. `scope` is the area changed. Subject is short, imperative, no trailing period: `feat(users): add cursor pagination`.

**Body:** 40 lines max, short sentences, exactly these `##` sections in this order:
- `## Why`: the problem and the approach, 1–3 sentences, from `design.md`.
- `## What changed`: 1–3 bullets.
- `## Scope`: what this covers and what it deliberately leaves out, from `design.md` out of scope. Always present.
- `## Verification`: a table `criterion | evidence`, the rows of this branch's reports' `## Criteria` tables, evidence you confirmed in Step 2.
- `## Assumptions`: the reports' `## Assumptions`, or "none".

Subagents mode: after all PRs exist, add a line `Related: #<n>, #<n>` to each body naming its sibling PRs (`gh pr edit <n> --body-file <body.md>`).

Then `run_state.py set <run> stage=done` and `run_state.py log <run> "review: approve, <k> PR(s) opened"`.

## Step 5. Changes: loop or escalate

Read `loop`.

- **loop < 2**: `run_state.py set <run> loop=<loop+1> stage=plan`, then `run_state.py log <run> "review: changes (<one-line summary>)"`. Prompt mode: show the Tasks table and Changes needed, then "Reply **go** to send these findings back to plan", and wait. Auto mode: read `${CLAUDE_PLUGIN_ROOT}/skills/plan/SKILL.md` and follow it with this run.
- **loop == 2**: stop looping (rule: `rule-bounded-loops`). `run_state.py set <run> stage=escalated`, `run_state.py log <run> "review: escalated after 2 loops"`, and report to the user (rule: `rule-ask-with-context`): **Unresolved** (each finding still open, with file:line), **Tried** (one line per loop, from the run log and earlier findings), **Question** (one specific question whose answer unblocks the run). Name the assumption every loop shared (rule: `rule-question-the-assumption`). Then stop.

## Output

- Approve: the Tasks table, then each PR link with its branch.
- Changes, looping: the Tasks table, Changes needed, and the hand-off line (prompt mode) or the plan stage's output (auto mode).
- Escalated: Unresolved, Tried, Question. Nothing else.

## Guardrails

- Never spawn a reviewer or any subagent; the main agent reviews.
- Never pass a report's claim through as your verdict; every verdict comes from the diff and Checks you re-ran.
- Never edit a task's code yourself. Findings go back to plan.
- Never approve with a failing or skipped Check, an open question, or a criterion without real evidence.
- Never open a PR as a draft, or push before **go** in prompt mode.
- Never loop a third time, and never loop a question that needs the user.
