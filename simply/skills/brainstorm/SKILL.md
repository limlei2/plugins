---
name: brainstorm
description: "Pipeline stage 1: interviews you one question at a time until every open decision is settled, writes design.md, and waits for your go before planning. Runs after /simply:start; hands off to /simply:plan."
disable-model-invocation: true
---

# Brainstorm

Grill the user until intent is settled: one goal, one approach, every decision written down with its reason and who made it, so plan never has to guess.

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

**Plugin root:** if `${CLAUDE_PLUGIN_ROOT}` appears literally in this file (you opened it with Read during a hand-off, so nothing filled it in), it means the folder two levels above this `SKILL.md`, e.g. `/…/simply` for `/…/simply/skills/plan/SKILL.md`. Substitute that absolute path everywhere below before running any command; the shell does not set this variable.

`run_state.py` below means `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/run_state.py`. An angle-bracket value (`<run>`, `<repo root>`) is what an earlier command printed: run that command on its own, then write the printed value literally. Each Bash call starts a fresh shell, so a shell variable would have to be rebuilt in every call.

**Commands:** write every file (reports, briefs, `design.md`, PR bodies) with the Write tool, never `cat > … <<EOF`, `echo >`, or `printf >`. One step per Bash call: no `cd "$PWD"`, and don't chain unrelated steps with `;` or `&&`. Commit messages go in separate `-m` flags with no newline inside a quote: `git commit -m "<subject>" -m "Co-Authored-By: …"`. Why: Claude Code can't check heredocs or multi-line quoted strings, so each such call stops the run for a permission prompt the user can't permanently allow.

## Limits

| Limit | Value | Why |
| --- | --- | --- |
| Questions per message | 1, with your recommended answer | One question gets a considered answer; a list gets skimmed. The recommendation makes "yes" a full reply. |
| Interview length | Until every open branch is answered, or the user replies **skip** | The user, not a count, decides when they've said enough; **skip** hands every remaining branch to you. |
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

Read the files the task names and the files they import, plus the project's `CLAUDE.md` and package manifest. Read more only to answer a branch in Step 3 before asking it, and keep raw file contents out of your reply: summarize (rule: `rule-keep-context-lean`).

## Step 3. Interview

Walk the design tree one branch at a time, in dependency order: settle what the user sees before how it's stored, and the shape of data before the code that reads it (rule: `rule-ask-with-context`). The branches, covered only where this task leaves them open and never read out as a list:

- what the user does and sees, and what success looks like;
- scope: what this deliberately won't do;
- edge cases and error behavior: empty, invalid, duplicate, concurrent, missing input;
- data, API, or file shape, and what happens to existing data;
- what existing code to reuse, reshape, or delete (rule: `rule-design-it-in`);
- how to prove it works: which tests, which surface (browser, curl, CLI);
- which library or approach, when there is a real choice.

Before each question, check whether the code, `CLAUDE.md`, or `git log` answers it. If it does, don't ask: record a Decision tagged `(code: <file>:<line>)`. A choice a sensible builder would settle without changing what gets built (a variable name, a helper's location): decide it, tag it `(my call)`, don't ask (rule: `rule-decide-and-report`).

Each question is its own message, in this shape, then wait for the reply:

```markdown
**Found:** <what the code says, with file:line, 1-2 lines>
**Question:** <one sentence>
**My answer:** <the answer you'd pick> — <one-line why>
```

The first message starts with one line: "I'll ask one question at a time; reply **skip** whenever you want me to decide the rest." A task with nothing open gets no questions: say so and go to Step 4. A task that already says not to ask ("don't ask me", "just decide", "skip the questions") counts as **skip** before the first question; record that with `run_state.py log <run> "brainstorm: user opted out of questions"`.

After each reply, record the Decision tagged `(you)`. Follow any new branch the answer opens. An answer that contradicts an earlier one or the code: say which, and ask which wins. Stop when every open branch has a Decision. On **skip**: decide every remaining branch, tag each `(my call)`, and go to Step 4.

A branch that needs outside facts to choose a library or approach: read `${CLAUDE_PLUGIN_ROOT}/skills/research/SKILL.md` and follow it in its From-brainstorm mode for that one question (no clarifying question, 20-fetch budget), then ask the user to confirm its pick as the next question. A second such branch stays in Open questions.

## Step 4. Write `<run>/design.md`

Exactly these `##` sections, in this order, all present:

```markdown
# Design: <slug>

## Goal
<one sentence>

## Approach
<2-5 sentences: how the change fits the existing code, naming the files it touches>

## Decisions
- <decision> — why: <reason> (you | my call | code: <file>:<line>)

## Out of scope
- <what this run deliberately won't do>, or `none`

## Open questions
- <question plan must work around, with the default plan should assume>, or `none`
```

Every answer and every call from Step 3 is a Decision, tagged with who made it, so the user can see which choices they never heard. Prefer the approach that deletes or reshapes existing code over one that bolts a layer on (rule: `rule-design-it-in`).

## Step 5. Check

```bash
wc -l <run>/design.md                         # 60 max
grep -c '^## ' <run>/design.md                # exactly 5
```

Over 60 lines: cut detail that belongs in a brief. Fix and re-run until both hold.

## Output

- **Goal:** the sentence.
- **Approach:** one line.
- **Decisions:** each with its why and its tag; list the `(my call)` ones first, since the user hasn't seen them.
- **Out of scope** and **Open questions**, or `none`.
- The `design.md` path.

## Hand-off

1. `run_state.py log <run> "brainstorm: <n> decisions, <n> open questions"` and `run_state.py set <run> stage=plan`.
2. `run_state.py get <run> mode`. Send the Output above. If the mode is `prompt`, or the user answered any question, end with "Reply **go** to continue to plan, or tell me what to change." and wait. Only an `auto` run whose task opted out of the questions continues without waiting. If the user asks for changes, apply them to `design.md`, re-run Step 5, and summarize again. Apart from that one opt-out, nothing is planned or built until the user approves the design.
3. After **go**, or straight on for an opted-out `auto` run: read and follow `${CLAUDE_PLUGIN_ROOT}/skills/plan/SKILL.md`.

## Guardrails

- Never write task briefs, branches, or code here: briefs need a settled design, and code needs briefs.
- Never leave a Decision without its why and its tag: plan can't tell a choice from an accident without the why, and the user can't tell what they agreed to without the tag.
- Never ask a question the code answers, and never send two questions in one message.
