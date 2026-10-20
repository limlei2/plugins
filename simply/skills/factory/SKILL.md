---
name: factory
description: "Splits a request into 2-5 independent tasks and runs a /simply:build worker on each in parallel (or /simply:research workers with `research`), then checks every result itself. For one task use /simply:build."
argument-hint: "[build|research] <request>"
disable-model-invocation: true
---

# Factory

Plan with a strong model, execute with cheap ones: you (the main agent) split and write briefs, workers execute them, you check and collect (rule: `rule-plan-strong-execute-cheap`, `rule-spend-review-where-mistakes-are-expensive`).

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

Mode is the first word of `$ARGUMENTS`: `research` selects research mode; `build` or anything else selects build mode (the default). The rest is the request.

## Limits

These are hard limits. Never exceed them, even if the user's request implies more.

| Limit | Build mode | Research mode | Why |
| --- | --- | --- | --- |
| Workers per run | 2 min, 5 max | 2 min, 6 max | One task doesn't need factory's overhead. More than 5 PRs at once is more than you can review in one sitting, and more agents mean more merge conflicts. |
| Criteria per brief | 7 max | 7 max | A bigger brief is two tasks; cheap workers lose track of long criteria lists. |
| Retries per task | 1 | 1 | If a fresh worker with an exact fix still fails, the brief or the plan is wrong, and that needs you, not more tokens. |
| Cross-PR reviewers | 1, only when 3+ PRs opened | none | With 1–2 PRs the main agent's own diff check (Step 5) already covers conflicts. |
| Total agents per run (workers + retries + reviewer) | 11 max | 12 max | Caps the cost of one run regardless of how the steps above play out. |

Fewer than 2 tasks: stop and tell the user to run `/simply:build` (or `/simply:research`) instead. More than the max: dispatch the first batch only, list the rest as "Next run" in the Output, and stop after this run.

## Models

Use exactly these Agent tool values. Do not pick others. If the user's request names a model for a task, use theirs for that task only.

| Role | `subagent_type` | `model` | `effort` | `isolation` |
| --- | --- | --- | --- | --- |
| Build worker, hard task | `general-purpose` | `opus` | `high` | `worktree` |
| Build worker, standard task | `general-purpose` | `sonnet` | `medium` | `worktree` |
| Build worker, mechanical task | `general-purpose` | `haiku` | `low` | `worktree` |
| Research worker | `Explore` | `sonnet` | `medium` | none |
| Cross-PR reviewer | `general-purpose` | `opus` | `high` | none |

Classify each build task by the first rule that matches:
1. **Hard** if it touches auth, permissions, payments, secrets, concurrency or locking, a data migration, or more than 5 files.
2. **Mechanical** if every change is a rename, copy or text change, config value, or dependency bump with no logic change.
3. **Standard** otherwise.

## Step 1. Plan

Read the files the request names and the files they import, plus the project's `CLAUDE.md` and package manifest. Read nothing else unless a task's files are still unknown, and keep raw file contents out of your reply: summarize (rule: `rule-keep-context-lean`). Then write this planning checkpoint in your reply, all four items, each answered (write `n/a: <reason>` rather than dropping one):

1. **Blocking first steps.** Work every task depends on (a schema change, a shared type, a new package). If there is one, this run dispatches **only** that step as a single build worker (an exception to the 2-worker minimum), reports it, and stops. The user re-runs `/simply:factory` after it merges.
2. **Independent workstreams.** Tasks that share no files, don't depend on each other's result, and needn't land together.
3. **Shared state** (rule: `rule-no-shared-writes`). Anything two tasks would both write (a file, a config, a lockfile, a route table). Split it so each task owns its part; if it can't be split, merge those tasks or sequence them.
4. **Smallest decomposition.** Why this many tasks and not fewer. If only one task remains, stop and tell the user to run `/simply:build`.

A task with more than 7 criteria is too big: split it, or cut criteria that restate another.

Research mode: one task per angle (one library, one question). Files is the single line `- Work in: read-only`, Checks is `- none`, Criteria list the facts the angle must answer.

## Step 2. Write and check the briefs

Write one brief per task in the format in `${CLAUDE_PLUGIN_ROOT}/skills/build/references/brief.md` to `.simply/factory/<YYYY-MM-DD-HHMM>-<slug>/<task-slug>.md` at the git root. Pin every decision in Constraints so workers don't remake it.

Classify each build task (hard, standard, mechanical) per **Models**. For every build task that touches UI, add `- Dev server port: <3101 + task index>` to Constraints so parallel workers never start servers on the same port. Then run the checker and fix every error it reports before going on:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/factory/scripts/check_briefs.py .simply/factory/<run>/*.md             # build mode
python3 ${CLAUDE_PLUGIN_ROOT}/skills/factory/scripts/check_briefs.py --research .simply/factory/<run>/*.md  # research mode
python3 ${CLAUDE_PLUGIN_ROOT}/skills/factory/scripts/check_briefs.py --blocking .simply/factory/<run>/*.md  # blocking first step only
```

It fails on missing sections, empty Criteria, more than 7 criteria, a brief count outside the **Limits**, and two briefs whose "Work in" paths overlap.

## Step 3. Confirm

Show the checkpoint and a table `task | class | model | effort | Work-in files`. Dispatch nothing until the user confirms. If they edit the list, re-run Step 2's checker before dispatching.

## Step 4. Dispatch

Precondition: worktrees branch from the main checkout's current commit, so it must be on the default branch and up to date. Check:

```bash
git fetch origin && git status -sb | head -1   # expect: ## <default>...origin/<default> with no ahead/behind
```

If it's on another branch, or behind, stop and tell the user, unless the request named that branch as the base on purpose.

Spawn every worker in a single message, one Agent call per task, with the values from **Models**. Resolve `${CLAUDE_PLUGIN_ROOT}` to its absolute path in every prompt; workers read the skill file rather than invoke it, because subagents may not be able to call plugin skills by name.

Use these prompts verbatim, then append the full brief:
- Build: `Read <root>/skills/build/SKILL.md and follow it in given-a-brief mode. Do not spawn subagents. Do not ask questions; escalate instead. Your brief:`
- Research: `Read <root>/skills/research/SKILL.md and follow it in given-a-brief mode. Do not edit files. Do not spawn subagents. Your brief:`

## Step 5. Check each result yourself

Wait for every worker. A worker's report is a claim, not evidence (rule: `rule-verify-the-real-thing`). For each build task:
1. Read the PR diff (`gh pr diff <n>`) against its brief: every criterion addressed, nothing outside "Work in", no debug leftovers.
2. Read the PR's Verification table. A criterion without real evidence counts as unmet.
3. Write your own one-line verdict per task: `ok`, or what is wrong.

For research tasks, spot-check the source URL behind each finding that drives the recommendation, and run `git status` to confirm nothing was edited.

## Step 6. Retry once, then escalate

For a task that failed your check or escalated with a question you can answer from the request or the code:
- Spawn a **fresh** worker (never resume the old one; resumed agents silently drop instructions) with the same Agent values as the original. Its prompt carries the original brief, a `## Fix` section stating exactly what to change, and the previous worker's report and branch.
- One retry per task, no more (rule: `rule-bounded-loops`). If the retry fails too, or the question needs a decision only the user can make, relay it to the user verbatim with what was tried (rule: `rule-ask-with-context`).
- A question that needs a product or preference decision (naming, UX, scope) always goes to the user. Never retry it.

Build mode, cross-PR review: run it when 3 or more PRs opened; skip it otherwise. Spawn ONE reviewer with the **Models** values. Prompt it to read every PR diff in one pass (`gh pr diff <n>`) and report only conflicts between PRs and cross-cutting mistakes (duplicated helpers, inconsistent naming, a contract one PR changes and another relies on), at most 10 findings, each with PR number, file, and line. It reports; it does not edit.

## Step 7. Combine (research mode)

Write one comparison across all angles (a table where the angles share dimensions), then one recommendation with what would change it. Keep facts (sourced) separate from inference (yours). List every source.

## Output

Build mode: the planning checkpoint, a table `task | model | branch | PR | your verdict | escalations`, each escalation's question verbatim, then the cross-PR review findings if run.

Research mode: the comparison, the recommendation, facts vs inference, and sources.

## Guardrails

- Never nest: only factory spawns agents, one level deep. Workers never spawn.
- Never exceed the **Limits** table or use a model outside the **Models** table.
- Never dispatch before the user confirms, or with briefs that fail the checker.
- Never give two workers the same file; if you can't split cleanly, run fewer, bigger tasks.
- Never pass a worker's summary through as your own. Your verdict comes from the diff.
- Never edit a worker's PR yourself or guess an answer to its escalation. Retry with a fresh worker or ask the user.
