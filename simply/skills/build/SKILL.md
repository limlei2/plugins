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

## Limits

Hard limits. Hitting one means stop and escalate (Step 7); never push past it.

| Limit | Value |
| --- | --- |
| Criteria in the brief | 7 max |
| Self-review rounds (Step 6) | 2 max |
| Diff size, excluding lockfiles and generated files | 400 changed lines, 10 files |
| Clarifying questions (standalone only) | 1 message, before any code |

Over the diff limit, the task is too big for one PR. Escalate with a proposed split for `/simply:factory`.

## Step 1. Write the brief (standalone only)

Write a brief from `$ARGUMENTS` in the format in [references/brief.md](references/brief.md). Read the files the task names and the files they import first so Files and Checks are real paths and real commands. Show the brief to the user in your reply, then continue without waiting.

Ask the user (once, all questions in one message, then wait) only when you cannot write one of these from the request and the code:
- a Goal that is one sentence,
- at least one checkable criterion,
- the "Work in" files.

Anything else unclear: choose the most literal reading, record it in Constraints, and proceed.

## Step 2. Check the brief

Confirm every listed file exists or is meant to be created, the criteria don't contradict each other, and each check can run. If the brief is wrong (missing file, contradictory criteria, a check that cannot pass) stop and escalate (Step 7). Don't patch around it.

Ambiguity inside a valid brief: take the most literal reading, note it as an assumption for the PR, continue.

## Step 3. Branch

Under factory the worktree already has a branch; use it. Standalone:

```bash
test -z "$(git status --porcelain)" || { echo "dirty tree"; exit 1; }
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD | sed 's|^origin/||')
git fetch origin "$BASE" && git switch -c "build/<slug>" "origin/$BASE"
```

`<slug>`: 2–4 lowercase words from the Goal, hyphenated. A dirty tree stops the build: tell the user to commit or stash first. Don't stash for them.

## Step 4. Implement

Before writing code, read the rules for the layer you touch and follow them:

| Touching | Read |
| --- | --- |
| UI components, styles, pages | `${CLAUDE_PLUGIN_ROOT}/skills/frontend-rules/SKILL.md` |
| Server logic, services, jobs | `${CLAUDE_PLUGIN_ROOT}/skills/backend-rules/SKILL.md` |
| Schema, migrations, queries | `${CLAUDE_PLUGIN_ROOT}/skills/db-rules/SKILL.md` |
| Endpoints, request/response shapes | `${CLAUDE_PLUGIN_ROOT}/skills/api-design-rules/SKILL.md` |

Make the smallest change that meets every criterion (principle: `principle-laziness-protocol`). Stay inside the brief's "Work in" files; never edit "Do not touch". If a criterion truly needs a file outside the list, that is a wrong brief: escalate.

Commit after each working unit, each leaving the checks green. Message: `<type>(<scope>): <subject>`, same rules as the PR title in Step 7.

## Step 5. Verify

1. Run every command in Checks. Each must pass.
2. Check each criterion against the real artifact and record the evidence: command plus result, or file and line (principle: `principle-prove-it-works`). Verify on the surface the user meets:
   - UI change: start the project's dev server (the `dev` script in `package.json`, or the command in `CLAUDE.md`), open the page in the built-in browser (`mcp__Claude_Browser__*`), and check the default, empty, loading, and error states. Evidence: the URL and what you saw in each state.
   - API change: call the endpoint (`curl`) and read the real response.
   - Data change: query the result, don't trust the migration's exit code.
   - CLI or script: run it with real arguments.
3. "Inconclusive", "should work", a check on a different surface, or a green suite that never exercises the criterion is not a pass. Treat it as a failure.

When a check fails, find the first place the system went wrong and fix it there, not where the symptom showed (principle: `principle-fix-root-causes`). Re-run all checks after every fix.

## Step 6. Self-review

Read `git diff <base>...HEAD` as a reviewer would:
- Bugs and unhandled edge cases.
- Callers of changed code you didn't update (`grep` for every renamed or changed symbol).
- Changes outside the brief's scope.
- Debug leftovers: `console.log`, `print`, commented-out code, TODOs you added, temp files.
- Comments that narrate what the code does. Keep only comments that explain a non-obvious why.

Fix what you find, then repeat Step 5.

At most 2 review-fix rounds. If the same premise fails twice (the same check, the same criterion), stop: write down the assumption both fixes shared and say it in the escalation (principle: `principle-attack-the-premise`). Don't try a third fix on it.

## Step 7. Ship or escalate

**Ship** when every check passes and every criterion has evidence:

1. Tidy history: squash fixup commits into the commit they fix (`git rebase -i` is unavailable, so use `git reset --soft <base>` and recommit). 5 commits max, each one landable and in order.
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

**Escalate** when the brief is wrong or any **Limits** value is hit. Commit and push any partial work to the branch, open no PR, and report:
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
