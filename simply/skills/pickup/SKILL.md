---
name: pickup
description: "Loads a handoff written by /simply:give, verifies the repo matches it (branch, commit, stash, files), marks it picked up, and continues the task from its exact next step. Use for 'pick up the handoff', 'continue from handoff', 'resume that task', or when given a .simply/handoffs/*.md path. With no path, takes the newest open handoff. Not for reviewing the day's leftovers (use /simply:goodmorning)."
argument-hint: "[handoff-path]"
disable-model-invocation: true
---

# Pickup

Continue a task from a `/simply:give` handoff with no loss of context, after proving the code in front of you is the code the handoff describes.

The format is defined once in [handoff-format.md](${CLAUDE_PLUGIN_ROOT}/skills/give/references/handoff-format.md). Read it before parsing.

## Step 1. Find the handoff

If `$ARGUMENTS` is a path, use it. Otherwise:

```bash
ROOT=$(git rev-parse --show-toplevel)
grep -l '^Status: open$' "$ROOT"/.simply/handoffs/*.md | sort | tail -1
```

If none is found, say so, list the five newest files in `.simply/handoffs/` with their `Status:` lines, and stop. If the chosen file says `Status: picked-up`, tell the user who took it and when, and stop unless they confirm.

Read the whole file.

## Step 2. Verify before trusting

Compare each recorded value in Code state with the repo:

| Check | Command | Match when |
|---|---|---|
| Branch | `git branch --show-current` | equals `Branch:` |
| Commit | `git rev-parse HEAD` | equals `Commit:` |
| Stash | `git cat-file -t <Stash>` | prints `commit` (skip if `none`) |
| Working tree | `git status --porcelain -- . ':(exclude).simply'` | see below |
| Files | `ls` each path in Files involved | all exist, except files the handoff says are new or deleted |

Working tree, when a stash is recorded:
- Tree clean: run `git stash apply --index <Stash>`, then re-run the status check.
- Tree dirty: `git diff <Stash>` must print nothing (same machine, giver's edits still present).

After that, the status lines must equal `Dirty files:`.

On any mismatch, stop. Report a table of expected vs actual for each failed check and the command that would fix it (for example `git switch <branch>`), but do not run it. Do not edit the handoff or any code.

## Step 3. Restate and claim

Write one paragraph to the user: the goal, where it stands, and the exact next step, in your own words. If the paragraph cannot be written without guessing, the handoff is incomplete: name the missing field and ask.

Then edit line 3 of the handoff to:

```
Status: picked-up by <git config user.name> at <YYYY-MM-DD HH:MM>
```

## Step 4. Continue

Do the Exact next step. Then continue only with work the handoff names: the rest of In progress, then the Goal. Stop and report when any of these happens:
- The How to verify commands pass: the Goal is done.
- The next action needs a decision not recorded under Decisions and why.
- The next action is outside Files involved and the Goal doesn't clearly require it.

Throughout:
- Honor Decisions and why. Reversing one needs a stated reason to the user first.
- Do not retry anything in Dead ends unless something the dead end depended on has changed; say what.
- Finish with the How to verify commands and report their result.

## Output

1. The verification result: every check passed, or the mismatch table (then stop).
2. The restatement paragraph.
3. The work on the next step, ending with the verify commands and results.

## Guardrails

- Never "fix" a mismatch by checking out, resetting, or stashing on your own; the user decides.
- Never mark `picked-up` before verification passes.
- Do not rely on the original conversation or ask the giver for context the file should hold; missing context is a gap to report.
- Do not open questions already answered under Decisions and why.
