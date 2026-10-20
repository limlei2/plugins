---
name: give
description: "Hands one in-progress task to a new chat or agent: freezes the code state and writes a handoff file for /simply:take. For a whole-day summary use /simply:goodnight."
argument-hint: "[slug or note for the receiver]"
disable-model-invocation: true
---

# Give

Turn the current task into one handoff file a cold agent can pick up and continue exactly where this conversation stopped. (rule: `rule-state-lives-in-files`)

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

The format is the contract with `/simply:take`: follow [references/handoff-format.md](references/handoff-format.md) exactly, every heading, in order.

## Step 1. Pick the task

Identify the single task in flight from the conversation. If several are interleaved, take the one the user worked on last and name the others under Open questions. Slug: the first word of `$ARGUMENTS` if it matches `^[a-z0-9-]{3,40}$`, else 2–4 lowercase hyphenated words from the task. Anything else in `$ARGUMENTS` goes under Note from giver.

## Step 2. Freeze the code state

```bash
ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"
git status --porcelain -- . ':(exclude).simply'
```

If that prints anything, stash it and put it straight back, so the receiver gets a fixed snapshot and this working tree is untouched:

```bash
git stash push -u -m "simply-give: <slug>" -- . ':(exclude).simply'
STASH=$(git rev-parse 'stash@{0}')
git stash apply --index "$STASH"
```

Then record `git branch --show-current` and `git rev-parse HEAD`. Use the full SHAs, never `stash@{N}` (it shifts).

Check: `git status --porcelain -- . ':(exclude).simply'` matches the first output. If the apply conflicted or the lists differ, stop and tell the user; do not write the handoff.

If not in a git repo, use the current directory as root and write `Branch: none (not a git repo)` under Code state.

## Step 3. Write the handoff

`mkdir -p "$ROOT/.simply/handoffs"`, then write `<YYYY-MM-DD-HHMM>-<slug>.md` (local time, `date +%Y-%m-%d-%H%M`) with `Status: open`.

Fill each section from the conversation and the repo, not memory:
- Done so far: only items with a real check in this conversation. Name the command and its result. Anything unchecked moves to In progress.
- Exact next step: one action, with file, symbol, and command. If you cannot name it, the task is not ready; ask the user what comes next (rule: `rule-ask-with-context`).
- Dead ends: every approach tried and abandoned, with the reason or error text. This is the section a fresh agent most needs.
- Files involved: run `git diff --name-only HEAD` plus untracked files, and add files that were read for context.

## Step 4. Cold-read review

First check the structure, fix every error, and re-run until it prints `ok`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/give/scripts/check_handoff.py <handoff>
```

Then re-read the file as an agent that has never seen this chat (the script can't check this part). Fix any line that relies on the conversation: "the error", "that approach", "as above", a symbol with no path. Check that the Code state block matches Step 2 exactly.

## Output

- The handoff path.
- One line to paste into the new chat: `/simply:take <absolute path>`
- If a stash was recorded: one line saying the stash lives only in this clone, so a receiver on another machine needs the WIP committed and pushed instead.

## Guardrails

- One task per handoff. A second task gets its own `/simply:give`.
- Never commit, reset, or switch branches here; the giver's tree must look the same after as before.
- Never put secrets, tokens, or `.env` values in the file. Name the variable instead.
- Do not soften failures. A red test is written as red, with its output line.
- Keep the `Status:` line spelling exact; `/simply:goodmorning` greps for it.
