---
name: brainstorm
description: "Pipeline stage 1: interviews you in rounds of up to 4 multiple-choice questions (the big picture and playback first, then the details), each with a recommended answer, writes design.md, has a fresh agent check it for gaps, and waits for your go before planning. Runs after /simply:start; hands off to /simply:plan."
disable-model-invocation: true
---

# Brainstorm

Find out what the user actually wants and why, then pin down the details: one goal, one approach, every decision written down with its reason and who made it, so plan never has to guess.

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

**Plugin root:** if `${CLAUDE_PLUGIN_ROOT}` appears literally in this file (you opened it with Read during a hand-off, so nothing filled it in), it means the folder two levels above this `SKILL.md`, e.g. `/…/simply` for `/…/simply/skills/plan/SKILL.md`. Substitute that absolute path everywhere below before running any command; the shell does not set this variable.

`run_state.py` below means `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/run_state.py`. An angle-bracket value (`<run>`, `<repo root>`) is what an earlier command printed: run that command on its own, then write the printed value literally. Each Bash call starts a fresh shell, so a shell variable would have to be rebuilt in every call.

**Commands:** write every file (reports, briefs, `design.md`, PR bodies) with the Write tool, never `cat > … <<EOF`, `echo >`, or `printf >`. One step per Bash call: no `cd "$PWD"`, and don't chain unrelated steps with `;` or `&&`. Commit messages go in separate `-m` flags with no newline inside a quote: `git commit -m "<subject>" -m "Co-Authored-By: …"`. Why: Claude Code can't check heredocs or multi-line quoted strings, so each such call stops the run for a permission prompt the user can't permanently allow.

## Limits

| Limit | Value | Why |
| --- | --- | --- |
| Questions per round | 1-4, in one `AskUserQuestion` call; 2-4 options each, your pick first | 4 is the tool's maximum; cards the user flips through cost one round trip instead of one per question. |
| Playback chunk | 200 words max, one part at a time | Long enough to describe one part, short enough that the user reads it and corrects it. |
| Interview length | Until every open branch is answered, or the user replies **skip** | The user, not a count, decides when they've said enough; **skip** hands every remaining branch to you. |
| `/simply:research` calls | 1, for one "which library or approach" question | Research is the most expensive step here; one question that needs outside facts is the most a design should hang on. |
| `design.md` length | 60 lines max | Past 60 lines it is a plan, not a design; detail belongs in plan's briefs. |
| Builder check | 1 agent, 1 round of questions | A second check reads a design already shaped by the first one's answers; one fresh reader finds the gaps worth asking about. |

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

Ask in rounds: one `AskUserQuestion` call per round with 1-4 questions, then wait for the answers (rule: `rule-ask-with-context`, which has the card format and the fallback when the tool is missing). Before the first round, write one line: "I'll ask in rounds of up to 4; type **skip** in any Other box to let me decide the rest."

**Round 1: the big picture.** Who it's for and why now, what success looks like, what it must not do. Each card offers your 2-4 best concrete guesses from the task and the code; the Other box takes their own words, and an Other answer outranks your guesses. Skip any the task already answers.

**Play back as you go.** Once you understand a part (what it's for, or how one piece behaves), write it back above the next round's cards in at most 200 words, marking each guess `(my guess)`, and make that round's first card "Is this playback right?" with options `Yes (Recommended)` and `Partly` (an Other or `Partly` answer: ask what's off in the next round). Every part is played back once.

**Later rounds: the details.** Once the picture is confirmed, ask the narrow branches this task leaves open:

- edge cases and error behavior: empty, invalid, duplicate, concurrent, missing input;
- data, API, or file shape, and what happens to existing data;
- what existing code to reuse, reshape, or delete (rule: `rule-design-it-in`);
- how to prove it works: which tests, which surface (browser, curl, CLI);
- which library or approach, when there is a real choice.

Put the code's evidence in the question as `(found: <file>:<line> <what it says>)`, and say why your pick wins in its option description. A question whose options depend on another answer waits for the next round.

**Every question.** First check whether the code, `CLAUDE.md`, or `git log` answers it; if so, don't ask: record a Decision tagged `(code: <file>:<line>)`. A choice a sensible builder would settle without changing what gets built: decide it, tag it `(my call)`, don't ask (rule: `rule-decide-and-report`). After each round, record each answer as a Decision tagged `(you)` and follow any new branch it opens. An answer that contradicts an earlier one or the code: say which, and ask which wins.

**Ending.** Stop when every open branch has a Decision. On **skip** in any answer (the other answers in that round still count): decide every remaining branch, tag each `(my call)`, and go to Step 4. A task that already says not to ask ("don't ask me", "just decide", "skip the questions") counts as **skip** before the first round; record that with `run_state.py log <run> "brainstorm: user opted out of questions"`. A task with nothing open gets no questions: say so.

A branch that needs outside facts to choose a library or approach: read `${CLAUDE_PLUGIN_ROOT}/skills/research/SKILL.md` and follow it in its From-brainstorm mode for that one question (no clarifying question, 20-fetch budget), then put its pick to the user as a card in the next round. A second such branch stays in Open questions.

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

## Step 6. Builder check

Spawn one agent with the values and prompt in `${CLAUDE_PLUGIN_ROOT}/skills/brainstorm/references/builder-check.md`, resolving the plugin root and both paths to absolute ones. Tell the user first, in one line, that a fresh reader is checking the design and you may come back once with a few questions. Sort every question it returns into the Answered, Minor, and Theirs piles that file defines, and update `design.md`.

Theirs pile not empty: ask them in that file's format and wait. Write each answer into `design.md` as a Decision tagged `(you)`, then re-run Step 5. An opted-out run asks nothing: decide the Theirs pile too, tagged `(my call)`. If it replied `nothing important left`, say so in the Output.

## Output

- **Goal:** the sentence.
- **Approach:** one line.
- **Decisions:** each with its why and its tag; list the `(my call)` ones first, since the user hasn't seen them.
- **Builder check:** how many questions it raised, and how many went to each pile.
- **Out of scope** and **Open questions**, or `none`.
- The `design.md` path.

## Hand-off

1. `run_state.py log <run> "brainstorm: <n> decisions, <n> open questions, builder check <n> questions"` and `run_state.py set <run> stage=plan`.
2. `run_state.py get <run> mode`. Send the Output above. If the mode is `prompt`, or the user answered any question, end with "Reply **go** to continue to plan, or tell me what to change." and wait. Only an `auto` run whose task opted out of the questions continues without waiting. If the user asks for changes, apply them to `design.md`, re-run Step 5, and summarize again. Apart from that one opt-out, nothing is planned or built until the user approves the design.
3. After **go**, or straight on for an opted-out `auto` run: read and follow `${CLAUDE_PLUGIN_ROOT}/skills/plan/SKILL.md`.

## Guardrails

- Never write task briefs, branches, or code here: briefs need a settled design, and code needs briefs.
- Never leave a Decision without its why and its tag: plan can't tell a choice from an accident without the why, and the user can't tell what they agreed to without the tag.
- Never ask a question the code answers, never ask more than 4 per round, and never ask one per message when the next doesn't depend on its answer.
- Never give the builder agent the interview: it must read `design.md` as plan will, with nothing else.
