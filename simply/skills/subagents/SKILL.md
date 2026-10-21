---
name: subagents
description: "Executes a run's planned tasks in parallel: one fresh /simply:tdd worker per pending task in its own worktree, then confirms every task left a valid report. For one agent working the tasks in order use /simply:tdd."
argument-hint: "(no arguments: runs the pending tasks of the latest /simply:start run)"
disable-model-invocation: true
---

# Subagents

Dispatch one fresh worker per pending brief, in parallel, and collect a valid report from each (rule: `rule-plan-strong-execute-cheap`).

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

**Plugin root:** if `${CLAUDE_PLUGIN_ROOT}` appears literally in this file (you opened it with Read during a hand-off, so nothing filled it in), it means the folder two levels above this `SKILL.md`, e.g. `/…/simply` for `/…/simply/skills/plan/SKILL.md`. Substitute that absolute path everywhere below before running any command; the shell does not set this variable.

`run_state.py` below means `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/run_state.py`. Run folder and report format: `${CLAUDE_PLUGIN_ROOT}/skills/start/references/run-format.md`. Find the run with `run_state.py latest "$(git rev-parse --show-toplevel)"` unless the previous stage named it.

You only dispatch and collect. Judging code quality is review's job, not yours.

## Limits

Hard limits. Never exceed them, even if the plan implies more.

| Limit | Value | Why |
| --- | --- | --- |
| Workers per dispatch | 5 max | More than 5 branches at once is more than review can check in one sitting, and more agents mean more merge conflicts. |
| Retries per task | 1 | If a fresh worker with an exact fix still fails, the brief or the plan is wrong, and that needs review and the user, not more tokens. |
| Total agents per run (workers + retries) | 10 max | Caps the cost of one execute stage regardless of how retries play out. |
| Questions to the user | 0 | Execute runs unattended; workers escalate in their reports instead. |

More than 5 pending tasks: dispatch nothing, tell the user the plan broke the limit, and stop. One pending task (a review loop's fix task) is fine.

## Models

Use exactly these Agent tool values. Do not pick others. If the brief's Constraints name a model, use that for that task only.

| Task class | `subagent_type` | `model` | `effort` | `isolation` |
| --- | --- | --- | --- | --- |
| Hard | `general-purpose` | `opus` | `high` | `worktree` |
| Standard | `general-purpose` | `sonnet` | `medium` | `worktree` |
| Mechanical | `general-purpose` | `haiku` | `low` | `worktree` |

Classify each brief by the first rule that matches:
1. **Hard** if it touches auth, permissions, payments, secrets, concurrency or locking, a data migration, or more than 5 files.
2. **Mechanical** if every change is a rename, copy or text change, config value, or dependency bump with no logic change.
3. **Standard** otherwise.

## Step 1. Read the run

```bash
RUN=<run folder>
run_state.py set "$RUN" stage=execute execute=subagents
run_state.py get "$RUN" pending    # e.g. 1,2,3; `none` means stop: nothing to run, tell the user to run /simply:plan
```

For each pending `<n>`, the brief is `$RUN/tasks/<n>-<slug>.md` and the report path is `$RUN/reports/<n>-<slug>.md`. Read each brief's Files and Constraints only, enough to classify it (rule: `rule-keep-context-lean`).

## Step 2. Check the base

Worktrees branch from the main checkout's current commit, so it must be on the default branch and up to date:

```bash
git fetch origin && git status -sb | head -1   # expect: ## <default>...origin/<default> with no ahead/behind
```

If it's on another branch, or behind, stop and tell the user. A fix task whose Constraints name a branch is fine: its worker pulls that branch itself.

## Step 3. Dispatch

For every brief that touches UI and has no `Dev server port` in Constraints, append `- Dev server port: <3101 + index>` to the copy you send, where index is the task's 0-based position in this dispatch, so parallel workers never start servers on the same port (rule: `rule-no-shared-writes`).

Spawn every worker in a single message, one Agent call per task, with the values from **Models**. Resolve `${CLAUDE_PLUGIN_ROOT}` to its absolute path; workers read the skill file rather than invoke it, because subagents may not be able to call plugin skills by name. Use this prompt verbatim, then append the full brief:

`Read <abs plugin root>/skills/tdd/SKILL.md and follow it in given-a-brief mode. Do not spawn subagents. Do not ask questions; escalate in the report instead. Write your report to <abs report path>. Your brief:`

## Step 4. Check each report

Wait for every worker. For each task:

```bash
test -f "$RUN/reports/<n>-<slug>.md" && run_state.py check-report "$RUN/reports/<n>-<slug>.md"
```

A task needs a retry when the report is missing, `check-report` fails, or its `## Escalation` is not `none`. Read only the report, never the diff; don't judge the code.

## Step 5. Retry once

For each task that needs one, spawn a **fresh** worker (never resume the old one; resumed agents silently drop instructions) with the same Agent values and port as the original. Its prompt is the Step 3 prompt plus the original brief, then:
- a `## Fix` section: what to change in one to three lines (the `check-report` errors, the missing report, or your answer to the escalation's question from the brief, `design.md`, or the code), and `Continue from branch: <branch>` when the previous report names a pushed branch;
- the previous report, verbatim, or `no report` if there was none.

One retry per task, no more (rule: `rule-bounded-loops`). A question that needs a product or preference decision (naming, UX, scope) is not retried: leave it for review to take to the user (rule: `rule-ask-with-context`). After the retry, whatever the outcome, leave the task for review. A task still without a valid report gets one written by you at its report path: `## Branch` the worker's branch or `none`, `## Commits` `none`, every criterion row with evidence `not run: no valid report`, `## Assumptions` `none`, and an `## Escalation` with Unresolved / Tried / Question. Run `check-report` on it.

## Output

A table `task | class | model | branch | retried | escalation`, then each escalation's question verbatim. Then the hand-off.

## Hand-off

1. `run_state.py set <run> pending=none stage=review` and `run_state.py log <run> "execute: <n> tasks done, <k> escalated"`.
2. `run_state.py get <run> mode`. If `prompt`: send the Output summary and end with "Reply **go** to continue to review, or tell me what to change." Wait.
3. If `auto`, or after **go**: read and follow `${CLAUDE_PLUGIN_ROOT}/skills/review/SKILL.md`.

## Guardrails

- Never nest: only this skill spawns agents, one level deep. Workers never spawn.
- Never exceed the **Limits** table or use a model outside the **Models** table.
- Never open a PR; review opens them on approve.
- Never edit a worker's branch or code yourself. Retry with a fresh worker or leave it for review.
- Never resume a worker; every retry is a fresh agent.
- Never pass a worker's claim through as checked: a report counts only after `check-report` prints `ok`.
