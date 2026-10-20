---
name: build
description: "Takes one task from request to open PR: frames it as a brief, implements the smallest change, verifies against each criterion, self-reviews, and ships a PR or escalates. Use for '/simply:build', 'build this', 'implement and open a PR', or when a /simply:factory worker is handed a brief. One agent, one task, one PR; never spawns subagents. For work that splits into parallel tasks, use /simply:factory."
argument-hint: "<task, or a brief in references/brief.md format>"
disable-model-invocation: true
---

# Build

Turn one task into one verified PR, or into a precise escalation.

## Modes

- **Standalone**: the user ran `/simply:build <task>`. Start at Step 1.
- **Given a brief**: you received a brief (you are a `/simply:factory` worker). Skip Step 1. Execute the brief exactly: don't re-scope, don't add criteria, don't reinterpret the goal. Never ask the user in this mode.

## Step 1. Write the brief (standalone only)

Write a brief from `$ARGUMENTS` in the format in [references/brief.md](references/brief.md). Read the code the task touches first so Files and Checks are real paths and real commands. If the goal is genuinely unclear, ask once with all questions together. Otherwise proceed.

## Step 2. Check the brief

Confirm every listed file exists or is meant to be created, the criteria don't contradict each other, and each check can run. If the brief is wrong (missing file, contradictory criteria, a check that cannot pass) stop and escalate (Step 7). Don't patch around it.

Ambiguity inside a valid brief: take the most literal reading, note it as an assumption for the PR, continue.

## Step 3. Branch

Under factory the worktree already has a branch; use it. Standalone: `git switch -c build/<short-slug>` from the default branch, after confirming `git status` is clean.

## Step 4. Implement

Make the smallest change that meets every criterion. Stay inside the brief's "Work in" files; never edit "Do not touch". If a criterion truly needs a file outside the list, that is a wrong brief: escalate.

## Step 5. Verify

1. Run every command in Checks. Each must pass.
2. Check each criterion against the real artifact (run it, call it, read the output) and record the evidence: command plus result, or file and line.

Fix any failure and re-run all checks.

## Step 6. Self-review

Read `git diff <base>...HEAD` as a reviewer would. Look for bugs, debug leftovers, callers of changed code you missed, and changes outside the brief's scope. Fix what you find, then repeat Step 5.

At most 2 review-fix rounds. If the same premise fails twice (the same check, the same criterion), stop and escalate instead of looping.

## Step 7. Ship or escalate

**Ship** when every check passes and every criterion has evidence:

```bash
git add <files> && git commit -m "<goal>"
git push -u origin HEAD
gh pr create --title "<goal>" --body-file <body.md>
```

PR body: the goal, a criteria table (criterion | evidence), and an Assumptions section listing every literal reading from Step 2 (or "none").

**Escalate** when the brief is wrong or the loop limit hit. Commit and push any partial work to the branch, open no PR, and report:
- Unresolved: which criterion or check, with the exact failure.
- Tried: each attempt, one line each.
- Question: one specific question whose answer unblocks the task.

## Output

Either the PR link plus the criteria table with evidence and assumptions, or the escalation (unresolved, tried, question). Nothing else.

## Guardrails

- Never spawn subagents. One agent, one task, one PR.
- Given a brief, never rewrite it: no new criteria, no wider scope, no "while I'm here" fixes.
- Never mark a criterion met without evidence from the real artifact; a passing test suite is not evidence for an untested criterion.
- Never weaken or skip a check to make it pass. A check that cannot pass is an escalation.
- Never open a PR with a failing check.
