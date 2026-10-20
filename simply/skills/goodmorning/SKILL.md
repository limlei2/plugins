---
name: goodmorning
description: "Start of day: reads the last daily log, checks it against git, PRs, CI, and open handoffs, and suggests a first task. Changes nothing."
disable-model-invocation: true
---

# Goodmorning

Brief the user on where work stands, comparing last night's log with reality, then wait. This skill only reads.

The log format is defined in `${CLAUDE_PLUGIN_ROOT}/skills/goodnight/references/daily-log-format.md`. Read it first; parse the log by its exact headings and ` | key: value` fields.

## Step 1. Find the newest log

```bash
ROOT=$(git rev-parse --show-toplevel) && cd "$ROOT"
ls .simply/daily/*.md 2>/dev/null | sort | tail -1
```

If not in a git repo, stop and say so. If there is no log, say "No daily log found" and skip to Step 3 with `SINCE=$(date -v-2d +%FT%T 2>/dev/null || date -d '2 days ago' +%FT%T)`.

Otherwise read the log and take from its header: `updated`, `head`, and `branches`. Set `SINCE` to `updated`. If the log is more than 7 days old, say so in the briefing.

## Step 2. Parse the log

First validate it with the same script goodnight uses:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/goodnight/scripts/check_log.py <log>
```

Then pull out Summary, In progress, Blocked, Open questions, Tomorrow, and Handoffs. Any section the script reports an error in is unreadable: say so in the briefing and keep going; do not guess its contents.

## Step 3. Check reality since the log

Run these, ignoring any that fail because a tool is missing:

```bash
git fetch --all --prune --quiet
git log --all --since="$SINCE" --format='%h %an %D %s'
git branch --show-current; git status --short
gh pr list --author @me --state all --search "updated:>=${SINCE%%T*}" --json number,title,state,headRefName,mergedAt
```

For each branch in the log's `branches` and In progress items:

```bash
git rev-parse --short "<branch>" 2>/dev/null || echo gone
git log -1 --format=%cr "<branch>"
gh pr view "<branch>" --json number,state,mergedAt,statusCheckRollup
```

Handoffs: list every file under `.simply/handoffs/`. Read only its `Status:` line. A file with `Status: open` is not yet taken; anything else is taken. If the field is missing, list the file as "status unknown".

If `gh` is missing or unauthenticated, say so and continue with git only.

## Step 4. Flag drift

Mark each In progress and Blocked item with one flag, first match wins:

- **merged**: its PR is merged, or its branch is merged into the default branch. Treat as done.
- **gone**: the branch no longer exists locally or on the remote.
- **failing**: any required check in `statusCheckRollup` is failing.
- **moved**: the branch tip differs from the SHA in `branches`. Note who pushed.
- **stale**: no commit on the branch in 3 or more days.
- **as left**: none of the above.

Also list commits since the log that touch no logged branch (5 max, newest first): work the log doesn't know about.

## Step 5. Rank open threads and pick a first task

Build the list by these rules, in this order:
1. Drop items flagged **merged** or **gone**.
2. Items flagged **failing** first.
3. Then open handoffs (`Status: open`), newest first.
4. Then the rest in the log's Tomorrow order; items not in Tomorrow go last in log order.

Keep the top 7. The suggested first task is item 1, with its `next` step from the log copied verbatim.

## Output

A briefing in exactly these sections and order. Each section is 5 bullets max, except Open threads (7 max). Total 40 lines max.

1. **Where we left off**: the log date and its Summary.
2. **What changed since**: new commits, PR and CI changes, open handoffs.
3. **Open threads, ranked**: each with its drift flag and `next` step.
4. **Open questions** from the log, verbatim.
5. **Suggested first task** and its exact next step.

End by asking the user to confirm the first task or pick another. Do no work until they answer.

## Guardrails

- Change nothing: no edits, commits, checkouts, pulls, or handoff status updates. `git fetch` is the only allowed write, to refs only.
- Do not start the suggested task before the user confirms.
- Do not invent a `next` step the log does not contain; say it is missing.
- Do not read or interpret handoff contents beyond the `Status:` line.
- Do not report a branch as stale or merged without the command output that shows it.
