---
name: take
description: "Resumes a /simply:give handoff: verifies the repo matches it, then continues from its exact next step."
argument-hint: "[handoff-path]"
disable-model-invocation: true
---

# Take

Continue a task from a `/simply:give` handoff with no loss of context, after proving the code in front of you is the code the handoff describes. (rule: `rule-state-lives-in-files`)

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

The format is defined once in [handoff-format.md](${CLAUDE_PLUGIN_ROOT}/skills/give/references/handoff-format.md). Read it before parsing.

## Step 1. Find the handoff

If `$ARGUMENTS` is a path, use it. Otherwise:

```bash
ROOT=$(git rev-parse --show-toplevel)
grep -l '^Status: open$' "$ROOT"/.simply/handoffs/*.md | sort | tail -1
```

If none is found, say so, list the five newest files in `.simply/handoffs/` with their `Status:` lines, and stop. If the chosen file says `Status: taken`, tell the user who took it and when, and stop unless they confirm.

Read the whole file, then validate it:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/give/scripts/check_handoff.py <handoff>
```

If it reports errors, list them and stop: the handoff is incomplete, and guessing the missing parts defeats the point of a handoff.

## Step 2. Verify before trusting

From the git root, run the verifier. It is read-only and compares branch, commit, stash, listed files, and working tree with the handoff's Code state:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/take/scripts/verify_state.py <handoff>
```

- Exit `0`: everything matches. Go to Step 3.
- Exit `2` (`NEEDS_APPLY`): the tree is clean and the giver's uncommitted work is in the recorded stash. Run the `git stash apply --index <sha>` it prints, then re-run the verifier; it must exit `0`.
- Exit `1`: mismatch. Show the user the table it printed, which includes the fix for each failed check, and stop (rule: `rule-ask-with-context`). Do not run any fix yourself, edit the handoff, or touch code.

## Step 3. Restate and claim

Write one paragraph to the user: the goal, where it stands, and the exact next step, in your own words. If the paragraph cannot be written without guessing, the handoff is incomplete: name the missing field and ask.

Then edit line 3 of the handoff to:

```
Status: taken by <git config user.name> at <YYYY-MM-DD HH:MM>
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
- Never mark `taken` before verification passes.
- Do not rely on the original conversation or ask the giver for context the file should hold; missing context is a gap to report.
- Do not open questions already answered under Decisions and why.
