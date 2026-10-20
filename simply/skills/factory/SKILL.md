---
name: factory
description: "Splits a request into independent tasks, writes one brief per task, runs a /simply:build worker per task in parallel worktrees, and collects the PRs into one report. Research mode fans out read-only workers, one angle each, and combines them into one comparison and recommendation. Use for '/simply:factory', 'factory this', 'split this into parallel PRs', 'fan out the work', or '/simply:factory research <question>'. For a single task, use /simply:build."
argument-hint: "[build|research] <request>"
disable-model-invocation: true
---

# Factory

Plan with a strong model, execute with cheap ones: you (the main agent) split and write briefs, workers execute them, you collect.

Mode is the first word of `$ARGUMENTS`: `research` selects research mode; `build` or anything else selects build mode (the default). The rest is the request.

## Step 1. Plan

Read enough of the code to split the request into tasks. A task qualifies only if it:
- shares no files with any other task,
- doesn't depend on another task's result,
- needn't land together with another task.

Merge tasks that fail any test into one, or sequence them (run the first factory, then the next). Write one brief per task in the format in `${CLAUDE_PLUGIN_ROOT}/skills/build/references/brief.md`. Pin every decision in Constraints so workers don't remake it.

Research mode: one task per angle (one library, one question). Use the same brief format with Files `read-only`, and Criteria listing the facts the angle must answer, each with a source.

## Step 2. Confirm

Show the task list: one line per task (goal, Work-in files, model). Ask the user to confirm or edit. Dispatch nothing until they confirm.

## Step 3. Dispatch

Spawn every worker in a single message, one Agent call per task.

Build mode:
- `subagent_type: "general-purpose"`, `model: "sonnet"` (unless the user picked another), `isolation: "worktree"`.
- Prompt: `Read ${CLAUDE_PLUGIN_ROOT}/skills/build/SKILL.md and follow it in given-a-brief mode. Do not spawn subagents. Your brief:` followed by the full brief.

Research mode:
- `subagent_type: "Explore"`, `model: "haiku"` (`"sonnet"` for angles that need judgment), no `isolation`.
- Prompt: `Read ${CLAUDE_PLUGIN_ROOT}/skills/research/SKILL.md and follow it for this one angle. Do not edit files. Do not spawn subagents. Your brief:` followed by the full brief.

Resolve `${CLAUDE_PLUGIN_ROOT}` to its absolute path before sending; workers read the file rather than invoke the skill, because subagents may not be able to call plugin skills by name.

## Step 4. Collect

Wait for every worker. Record per task: branch, PR link or escalation, and criteria status. If a worker returns neither a PR nor an escalation, note it as a gap; don't redo its work yourself.

Build mode, optional cross-PR review (offer it when 2+ PRs landed): spawn ONE reviewer, `subagent_type: "general-purpose"`, `model: "opus"`, no worktree. Prompt it to read every PR diff in one pass (`gh pr diff <n>`) and report only conflicts between PRs and cross-cutting mistakes (duplicated helpers, inconsistent naming, a contract one PR changes and another relies on). It reports; it does not edit.

Research mode: check `git status` is clean after workers finish.

## Step 5. Combine (research mode)

Write one comparison across all angles (a table where the angles share dimensions), then one recommendation. Keep facts (sourced) separate from inference (yours). List every source.

## Output

Build mode: a table `task | branch | PR | status | escalations`, then each escalation's question verbatim, then the cross-PR review findings if run.

Research mode: the comparison, the recommendation, facts vs inference, and sources.

## Guardrails

- Never nest: only factory spawns agents, one level deep. Workers never spawn.
- Never dispatch before the user confirms the task list.
- Never give two workers the same file; if you can't split cleanly, run fewer, bigger tasks.
- Never edit a worker's brief after dispatch, fix its PR yourself, or answer its escalation by guessing; relay escalations to the user.
