---
name: plan
description: "Pipeline stage 2: questions you one at a time on the plan's open choices, turns design.md into 1-5 checked task briefs, and asks you to run them with /simply:tdd or /simply:subagents; after a review asking for changes, writes only the fix tasks."
disable-model-invocation: true
---

# Plan

Turn the design into task briefs a cheap executor can follow without remaking a decision: plan with a strong model, execute with cheap ones (rule: `rule-plan-strong-execute-cheap`).

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

**Plugin root:** if `${CLAUDE_PLUGIN_ROOT}` appears literally in this file (you opened it with Read during a hand-off, so nothing filled it in), it means the folder two levels above this `SKILL.md`, e.g. `/…/simply` for `/…/simply/skills/plan/SKILL.md`. Substitute that absolute path everywhere below before running any command; the shell does not set this variable.

`run_state.py` below means `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/run_state.py`, and `check_briefs.py` means `python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/check_briefs.py`. An angle-bracket value (`<run>`, `<repo root>`) is what an earlier command printed: run that command on its own, then write the printed value literally. Each Bash call starts a fresh shell, so a shell variable would have to be rebuilt in every call.

**Commands:** write every file (reports, briefs, `design.md`, PR bodies) with the Write tool, never `cat > … <<EOF`, `echo >`, or `printf >`. One step per Bash call: no `cd "$PWD"`, and don't chain unrelated steps with `;` or `&&`. Commit messages go in separate `-m` flags with no newline inside a quote: `git commit -m "<subject>" -m "Co-Authored-By: …"`. Why: Claude Code can't check heredocs or multi-line quoted strings, so each such call stops the run for a permission prompt the user can't permanently allow.

## Modes

Find the run first. Handed off: use its `<run>`. Typed directly: run `git rev-parse --show-toplevel` (prints `<repo root>`), then `run_state.py latest <repo root>` (prints `<run>`); no run means stop and tell the user to run `/simply:start <task>`. Then `run_state.py get <run> loop`:

- **First plan** (`loop` is `0`): Steps 1-4.
- **Loop plan** (`loop` is `1` or `2`; review found changes and already incremented it): Step 5 only.

## Limits

Hard limits. Never exceed them, even if the design implies more.

| Limit | Value | Why |
| --- | --- | --- |
| Tasks per first plan | 1 min, 5 max | More than 5 is more than one review can check in one sitting; split the request across runs. |
| Tasks in subagents mode | 2 min, 5 max | One task doesn't need parallel worktrees; more workers mean more merge conflicts. |
| Criteria per brief | 7 max | More than 7 means more than one task; cheap executors lose track of long criteria lists. |
| Questions per message | 1, with your recommended answer; first plan only, a loop plan asks nothing | One question gets a considered answer; a loop's findings are already exact. |
| Interview length | Until every open plan choice is answered, or the user replies **skip**; the tdd-or-subagents question is always asked | Brainstorm settled what to build; this settles how it splits, which the user may see differently. |
| Fix tasks per loop | 1 per branch with findings | Two fix tasks on one branch would collide; the findings for a branch belong in one brief. |

More than 5 tasks: brief the first 5 in run order, list the rest under "Next run" in the Output, and stop there.

## Step 1. Planning checkpoint (first plan)

Read `<run>/design.md`, then the files its Approach names and the files they import. Read nothing else unless a task's files are still unknown, and keep raw file contents out of your reply: summarize (rule: `rule-keep-context-lean`). Write this checkpoint in your reply, all six items, each answered (write `n/a: <reason>` rather than dropping one):

1. **Blocking first steps.** Work every other task depends on (a schema change, a shared type, a new package). It gets the lowest task numbers so it runs first.
2. **Independent workstreams.** Tasks that share no files, don't depend on each other's result, and needn't land together.
3. **Shared state** (rule: `rule-no-shared-writes`). Anything two tasks would both write (a file, a config, a lockfile, a route table). Split it so each task owns its part; if it can't be split, merge those tasks or order them.
4. **Smallest decomposition.** Why this many tasks and not fewer. One task is fine: it runs with tdd.
5. **Interfaces.** Every function, type, route, or file format that one task provides and another uses, with its exact name and signature as the code will spell it, which task provides it, and which tasks use it. A task that uses another's runs after it.
6. **Size.** Estimate each task's diff: changed lines and files, excluding lockfiles and generated files. Split a task where a reviewer could reject one part and approve the other; fold a task that is only setup (config, scaffolding, a type) into the task whose deliverable needs it. The estimate is a guess written into the brief, not a limit.

A task with more than 7 criteria is too big: split it, or cut criteria that restate another.

Then question the user on the plan's open choices, one question per message in brainstorm's shape (**Found** / **Question** / **My answer**), waiting for each reply (rule: `rule-ask-with-context`). Ask only what `design.md` doesn't settle and would change the briefs:

- where to split, and in what order the tasks land;
- an interface's name or shape, when more than one would be reasonable;
- what proves each task: which test command, which surface;
- a task whose estimate is far larger than the others: split it, or keep it whole.

Never re-ask a Decision in `design.md`. Choices that don't change the briefs: decide and record in Constraints (rule: `rule-decide-and-report`). Record each answer in the Constraints of the briefs it touches. On **skip**, or when the run log shows the user opted out of brainstorm's questions, decide the rest yourself. Nothing open: no questions; say so. The tdd-or-subagents question is still asked.

## Step 2. Write and check the briefs (first plan)

Write the criteria before any code exists (rule: `rule-criteria-before-code`). One brief per task in the format in `${CLAUDE_PLUGIN_ROOT}/skills/plan/references/brief.md`, to `<run>/tasks/<n>-<slug>.md`: `<n>` is the run order 1..5, blocking work first; `<slug>` is 2-4 lowercase words from the task's Goal, hyphenated.

- Files and Checks are real paths and real commands from the code you read.
- Pin every Decision from `design.md` that touches the task in its Constraints, so the executor doesn't remake it.
- Interfaces and Estimate come from checkpoint items 5 and 6. A Uses of another task's Provides is `task <n>: <that Provides text, verbatim>`; the checker compares the text.
- Context is the `task` field (`run_state.py get <run> task`), verbatim.

```bash
check_briefs.py <run>/tasks/*.md
```

Fix every error it reports and re-run until it exits 0 (it then prints `ok: <n> briefs`). Then `run_state.py set <run> pending=<all task numbers, comma-separated>`.

## Step 3. Ask how to execute (first plan, every run, both modes)

Show the checkpoint and a table `task | goal | Work-in files | estimate`. Then ask, and wait for the answer even in auto mode:

> **TDD** (one agent, tasks in order, one branch, one PR) or **subagents** (one worker per task in parallel worktrees, one PR per task)? I recommend **<choice>**: <one-line reason>.

Recommend `subagents` only when there are 2+ tasks, no two share a Work-in file, no task uses another's Provides, and there is no blocking first step; otherwise recommend `tdd`.

## Step 4. Fit the briefs to the choice (first plan)

- **tdd:** `run_state.py set <run> execute=tdd`.
- **subagents:** run `check_briefs.py --parallel <run>/tasks/*.md`. On an overlap or a task that uses another's Provides, merge those tasks into one brief (renumber, still 7 criteria max) and re-run until it exits 0. If merging leaves one task, tell the user it now runs as tdd and set `execute=tdd`. For every task that touches UI, add `- Dev server port: <3100 + n>` to Constraints so parallel workers never start servers on the same port. Then `run_state.py set <run> execute=subagents pending=<task numbers>`.

## Step 5. Loop plan

Read `<run>/review.md` and `run_state.py get <run> execute` and `run_state.py get <run> branch`. Reuse the execute choice; never ask again.

1. Take only the findings in `review.md`. Never rewrite, renumber, or re-run a task that passed.
2. Group the findings by branch: the run's `branch` in tdd mode, each failed task's report `## Branch` (in `<run>/reports/`) in subagents mode.
3. Write one fix brief per branch to `<run>/tasks/<n>-fix-<slug>.md`, with `<n>` continuing after the highest existing task number. Criteria come from the findings, written before code (rule: `rule-criteria-before-code`), each checkable. Constraints starts with `- Fix branch: <branch>` and `- Fixes task <n>: <finding>` for each finding. Interfaces are the fixed task's, unless a finding is about one; Estimate is the fix's own size.
4. Check only the new briefs: `check_briefs.py <run>/tasks/<new n>-*.md` (subagents mode with 2+ fix briefs: add `--parallel`). Fix and re-run until it exits 0.
5. `run_state.py set <run> pending=<fix task numbers>`. Don't touch `loop`; review owns it.

## Output

First plan: the checkpoint, the table `task | goal | Work-in files | estimate`, the user's choice, `pending`, and "Next run" if tasks were cut.

Loop plan: `loop <n>`, a table `fix task | branch | findings it fixes`, and `pending`.

## Hand-off

1. `run_state.py log <run> "plan: <n> tasks, user chose <execute>"` (loop plan: `"plan: loop <n>, <n> fix tasks"`) and `run_state.py set <run> stage=execute`.
2. `run_state.py get <run> mode`. If `prompt`: send the Output above and end with "Reply **go** to continue to <tdd or subagents>, or tell me what to change." Wait. If the user asks for changes, apply them, re-run the checker for this entry, and summarize again.
3. If `auto`, or after **go**: `run_state.py get <run> execute`, then read and follow `${CLAUDE_PLUGIN_ROOT}/skills/tdd/SKILL.md` if `tdd`, or `${CLAUDE_PLUGIN_ROOT}/skills/subagents/SKILL.md` if `subagents`.

## Guardrails

- Never write code, create branches, or edit files outside `<run>` here: execute owns the branch, and edits here skip the briefs' checks.
- Never increment `loop` or decide to escalate: review owns both, and two writers would miscount the 2-loop cap.
- Never edit `run.md` by hand: `run_state.py` validates every field, and a hand edit skips that check.
