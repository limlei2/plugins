---
name: brainstorm
description: "Pipeline stage 1: settles what the task means and how to approach it in design.md before any planning. Runs after /simply:start; hands off to /simply:plan."
disable-model-invocation: true
---

# Brainstorm

Settle intent before planning: one goal, one approach, every decision written down with its reason, so plan never has to guess.

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

**Plugin root:** if `${CLAUDE_PLUGIN_ROOT}` appears literally in this file (you opened it with Read during a hand-off, so nothing filled it in), it means the folder two levels above this `SKILL.md`, e.g. `/…/simply` for `/…/simply/skills/plan/SKILL.md`. Substitute that absolute path everywhere below before running any command; the shell does not set this variable.

`run_state.py` below means `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/run_state.py`. An angle-bracket value (`<run>`, `<repo root>`) is what an earlier command printed: run that command on its own, then write the printed value literally. Each Bash call starts a fresh shell, so a shell variable would have to be rebuilt in every call.

**Commands:** write every file (reports, briefs, `design.md`, PR bodies) with the Write tool, never `cat > … <<EOF`, `echo >`, or `printf >`. One step per Bash call: no `cd "$PWD"`, and don't chain unrelated steps with `;` or `&&`. Commit messages go in separate `-m` flags with no newline inside a quote: `git commit -m "<subject>" -m "Co-Authored-By: …"`. Why: Claude Code can't check heredocs or multi-line quoted strings, so each such call stops the run for a permission prompt the user can't permanently allow.

## Limits

| Limit | Value | Why |
| --- | --- | --- |
| Questions to the user | 1 message, only when a one-sentence Goal can't be written | Everything else is a decision you can make and record; questions the code answers waste the user's time. |
| `/simply:research` calls | 1, for one "which library or approach" question | Research is the most expensive step here; one question that needs outside facts is the most a design should hang on. |
| `design.md` length | 60 lines max | Past 60 lines it is a plan, not a design; detail belongs in plan's briefs. |

## Step 1. Find the run

Handed off from `/simply:start`: use its `<run>`. Typed directly:

```bash
git rev-parse --show-toplevel          # prints <repo root>
run_state.py latest <repo root>        # prints <run>
```

No run: stop and tell the user to run `/simply:start <task>`. Read the task with `run_state.py get <run> task`.

## Step 2. Read the code

Read the files the task names and the files they import, plus the project's `CLAUDE.md` and package manifest. Read nothing else, and keep raw file contents out of your reply: summarize (rule: `rule-keep-context-lean`).

## Step 3. Settle intent

Write the Goal as one sentence: the outcome, not the steps.

- Can't write it from the task and the code: ask the user once, all questions in one message, each with what you found and the options you see, then wait (rule: `rule-ask-with-context`).
- Anything else unclear: pick the most literal reading, record it as a Decision with its why, and keep going (rule: `rule-decide-and-report`).

An open question that needs outside facts to choose a library or approach: read `${CLAUDE_PLUGIN_ROOT}/skills/research/SKILL.md` and follow it in its From-brainstorm mode for that one question (no clarifying question, 20-fetch budget). Record its pick as a Decision with the research's reason. A second such question stays in Open questions.

## Step 4. Write `<run>/design.md`

Exactly these `##` sections, in this order, all present:

```markdown
# Design: <slug>

## Goal
<one sentence>

## Approach
<2-5 sentences: how the change fits the existing code, naming the files it touches>

## Decisions
- <decision> — why: <reason>

## Out of scope
- <what this run deliberately won't do>, or `none`

## Open questions
- <question plan must work around, with the default plan should assume>, or `none`
```

Every assumption from Step 3 is a Decision. Prefer the approach that deletes or reshapes existing code over one that bolts a layer on (rule: `rule-design-it-in`).

## Step 5. Check

```bash
wc -l <run>/design.md                         # 60 max
grep -c '^## ' <run>/design.md                # exactly 5
```

Over 60 lines: cut detail that belongs in a brief. Fix and re-run until both hold.

## Output

- **Goal:** the sentence.
- **Approach:** one line.
- **Decisions:** each with its why.
- **Out of scope** and **Open questions**, or `none`.
- The `design.md` path.

## Hand-off

1. `run_state.py log <run> "brainstorm: <n> decisions, <n> open questions"` and `run_state.py set <run> stage=plan`.
2. `run_state.py get <run> mode`. If `prompt`: send the Output above and end with "Reply **go** to continue to plan, or tell me what to change." Wait. If the user asks for changes, apply them to `design.md`, re-run Step 5, and summarize again.
3. If `auto`, or after **go**: read and follow `${CLAUDE_PLUGIN_ROOT}/skills/plan/SKILL.md`.

## Guardrails

- Never write task briefs, branches, or code here: briefs need a settled design, and code needs briefs.
- Never leave a Decision without its why: plan can't tell a choice from an accident without it.
