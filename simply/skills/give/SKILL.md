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

An angle-bracket value (`<repo root>`, `<stash sha>`) is what an earlier command printed: run that command on its own, then write the printed value literally. Each Bash call starts a fresh shell, so a shell variable would have to be rebuilt in every call.

**Commands:** write every file (reports, briefs, `design.md`, PR bodies) with the Write tool, never `cat > … <<EOF`, `echo >`, or `printf >`. One step per Bash call: no `cd "$PWD"`, and don't chain unrelated steps with `;` or `&&`. Commit messages go in separate `-m` flags with no newline inside a quote: `git commit -m "<subject>" -m "Co-Authored-By: …"`. Why: Claude Code can't check heredocs or multi-line quoted strings, so each such call stops the run for a permission prompt the user can't permanently allow.

## Step 1. Pick the task

Identify the single task in flight from the conversation. If several are interleaved, take the one the user worked on last and name the others under Open questions. Slug: the first word of `$ARGUMENTS` if it matches `^[a-z0-9-]{3,40}$`, else 2–4 lowercase hyphenated words from the task. Anything else in `$ARGUMENTS` goes under Note from giver.

## Step 2. Freeze the code state

```bash
git rev-parse --show-toplevel                                   # prints <repo root>
git -C <repo root> status --porcelain -- . ':(exclude).simply'
```

Run every git command in this step with `-C <repo root>`, so paths resolve from the root without a `cd`.

If that prints anything, stash it and put it straight back, so the receiver gets a fixed snapshot and this working tree is untouched:

```bash
git -C <repo root> stash push -u -m "simply-give: <slug>" -- . ':(exclude).simply'
git -C <repo root> rev-parse 'stash@{0}'                        # prints <stash sha>
git -C <repo root> stash apply --index <stash sha>
```

Then record `git branch --show-current` and `git rev-parse HEAD`. Use the full SHAs, never `stash@{N}` (it shifts).

Check: `git status --porcelain -- . ':(exclude).simply'` matches the first output. If the apply conflicted or the lists differ, stop and tell the user; do not write the handoff.

If not in a git repo, use the current directory as root and write `Branch: none (not a git repo)` under Code state.

## Step 3. Write the handoff

Write `<repo root>/.simply/handoffs/<YYYY-MM-DD-HHMM>-<slug>.md` (local time, `date +%Y-%m-%d-%H%M`) with `Status: open`, using the Write tool; it creates the folder.

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
