---
name: build
description: "One task to one verified PR: writes or follows a brief, implements, verifies, self-reviews, then opens the PR or escalates. For parallel tasks use /simply:factory."
argument-hint: "<task, or a brief in references/brief.md format>"
disable-model-invocation: true
---

# Build

Turn one task into one verified PR, or into a precise escalation.

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

## Modes

- **Standalone**: the user ran `/simply:build <task>`. Start at Step 1.
- **Given a brief**: you received a brief (you are a `/simply:factory` worker). Skip Step 1. Execute the brief exactly: don't re-scope, don't add criteria, don't reinterpret the goal. Never ask the user in this mode: decide, record the assumption, keep going (rule: `rule-decide-and-report`).

## Limits

Hard limits. Hitting one means stop and escalate (Step 7); never push past it.

| Limit | Value | Why |
| --- | --- | --- |
| Criteria in the brief | 7 max | More than 7 means more than one task; it should be split, not squeezed. |
| Self-review rounds (Step 6) | 2 max | Two failed fixes on one premise mean the premise is wrong; a third fix wastes tokens on the same mistake. |
| Diff size, excluding lockfiles and generated files | 400 changed lines, 10 files | Past this a reviewer stops reading carefully, so bugs get through. Smaller PRs get real review. |
| Clarifying questions (standalone only) | 1 message, before any code | Questions after work starts waste the work done; one batched message respects the user's time. |

Over the diff limit, the task is too big for one PR. Escalate with a proposed split for `/simply:factory`.

## Step 1. Write the brief (standalone only)

Write the criteria before any code (rule: `rule-criteria-before-code`). Write a brief from `$ARGUMENTS` in the format in [references/brief.md](references/brief.md). Read the files the task names and the files they import first so Files and Checks are real paths and real commands. Show the brief to the user in your reply, then continue without waiting (rule: `rule-decide-and-report`).

Ask the user (once, all questions in one message, then wait) only when you cannot write one of these from the request and the code:
- a Goal that is one sentence,
- at least one checkable criterion,
- the "Work in" files.

Anything else unclear: choose the most literal reading, record it in Constraints, and proceed.

## Step 2. Check the brief

Confirm every listed file exists or is meant to be created, the criteria don't contradict each other, and each check can run. If the brief is wrong (missing file, contradictory criteria, a check that cannot pass) stop and escalate (Step 7). Don't patch around it.

Ambiguity inside a valid brief: take the most literal reading, note it as an assumption for the PR, continue.

## Step 3. Branch

Find the default branch (both modes):

```bash
DEFAULT=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
[ -n "$DEFAULT" ] || DEFAULT=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
git fetch origin "$DEFAULT"
```

Under factory the worktree already has a branch; use it. Standalone:

```bash
test -z "$(git status --porcelain)" || { echo "dirty tree"; exit 1; }
git switch -c "build/<slug>" "origin/$DEFAULT"
```

`<slug>`: 2–4 lowercase words from the Goal, hyphenated. A dirty tree stops the build: tell the user to commit or stash first. Don't stash for them.

Then, in both modes, record the base commit that Steps 6 and 7 compare against:

```bash
BASE=$(git merge-base HEAD "origin/$DEFAULT")
```

## Step 4. Implement

Before writing code:
- Follow the conventions in the project's `CLAUDE.md` and the patterns of the nearest similar file.
- Remove dead code and redundant layers the change would build on (rule: `rule-delete-first`).
- If the requirement doesn't fit the current design, reshape the design rather than bolting it on (rule: `rule-design-it-in`).
- Validate untrusted input once, at the boundary; trust internal types after (rule: `rule-validate-at-the-edges`).
- Tests assert what callers or users can observe, not internals (rule: `rule-test-what-users-see`).

Make the smallest change that meets every criterion (rule: `rule-smallest-change`). Stay inside the brief's "Work in" files; never edit "Do not touch". If a criterion truly needs a file outside the list, that is a wrong brief: escalate.

Commit after each working unit, each leaving the checks green (rule: `rule-small-green-steps`). Message: `<type>(<scope>): <subject>`, same rules as the PR title in Step 7.

## Step 5. Verify

1. Run every command in Checks. Each must pass.
2. Check each criterion against the real artifact and record the evidence: command plus result, or file and line (rule: `rule-verify-the-real-thing`). Verify on the surface the user meets:
   - UI change: start the project's dev server (the `dev` script in `package.json`, or the command in `CLAUDE.md`) on the port named in the brief's Constraints (`PORT=<n>`, or `--port <n>` for Vite), else the default port, open the page in the built-in browser (`mcp__Claude_Browser__*`), and check the default, empty, loading, and error states. Evidence: the URL and what you saw in each state.
   - API change: call the endpoint (`curl`) and read the real response.
   - Data change: query the result, don't trust the migration's exit code.
   - CLI or script: run it with real arguments.
3. "Inconclusive", "should work", a check on a different surface, or a green suite that never exercises the criterion is not a pass. Treat it as a failure.

When a check fails, find the first place the system went wrong and fix it there, not where the symptom showed (rule: `rule-fix-at-the-source`). Re-run all checks after every fix.

## Step 6. Self-review

Read `git diff $BASE...HEAD` as a reviewer would:
- Bugs and unhandled edge cases.
- Callers of changed code you didn't update (`grep` for every renamed or changed symbol).
- Changes outside the brief's scope.
- Debug leftovers: `console.log`, `print`, commented-out code, TODOs you added, temp files.
- Comments that narrate what the code does. Keep only comments that explain a non-obvious why.
- Layers a reader must trace: one-caller wrappers, needless indirection, mutable state with wide scope (rule: `rule-easy-to-follow`).

Fix what you find, then repeat Step 5.

At most 2 review-fix rounds (rule: `rule-bounded-loops`). If the same premise fails twice (the same check, the same criterion), stop: write down the assumption both fixes shared and say it in the escalation (rule: `rule-question-the-assumption`). Don't try a third fix on it.

## Step 7. Ship or escalate

**Ship** when every check passes and every criterion has evidence:

1. Tidy history: squash fixup commits into the commit they fix (`git rebase -i` is unavailable, so use `git reset --soft $BASE` and recommit). 5 commits max, each one landable and in order.
2. Push and open the PR ready for review, never as a draft:

```bash
git push -u origin HEAD
gh pr create --title "<type>(<scope>): <subject>" --body-file <body.md>
```

**Title:** Conventional Commits. `type` is one of `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`. `scope` is the area changed. Subject is short, imperative, no trailing period: `feat(users): add cursor pagination`.

**Body:** a one-minute briefing for a reviewer who has the diff, 40 lines max. Short sentences. Exactly these `##` sections in this order, all present:
- `## Why`: the problem and the approach, 1–3 sentences.
- `## What changed`: 1–3 bullets.
- `## Scope`: what this covers and what it deliberately leaves out. Always present.
- `## Verification`: a table `criterion | evidence`, one row per criterion.
- `## Assumptions`: every literal reading from Step 2, or "none".

**Escalate** when the brief is wrong or any **Limits** value is hit. Commit and push any partial work to the branch, open no PR, and report (rule: `rule-ask-with-context`):
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
- Never open a PR with a failing check, or as a draft.
- Never call a criterion met because it "should" work. Run it.
