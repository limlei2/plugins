---
name: goodmorning
description: "Start-of-day briefing. Use for 'goodmorning', 'good morning', 'where did we leave off', 'what's on today', or 'catch me up'. Reads the newest .simply/daily/ log written by /simply:goodnight, checks it against current git, PR, CI, and handoff state, flags drift, and suggests a first task. Read-only: changes nothing and waits for confirmation. Not for picking up a specific handoff."
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

Pull out Summary, In progress, Blocked, Open questions, Tomorrow, and Handoffs. If a heading is missing or a line does not match its section's shape, report that section as unreadable and keep going; do not guess its contents.

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

Handoffs: list every file under `.simply/handoffs/`. Read only its `Status:` line. A file with `Status: open` is unpicked; anything else is picked up. If the field is missing, list the file as "status unknown".

If `gh` is missing or unauthenticated, say so and continue with git only.

## Step 4. Flag drift

Mark each In progress and Blocked item with one flag, first match wins:

- **merged**: its PR is merged, or its branch is merged into the default branch. Treat as done.
- **gone**: the branch no longer exists locally or on the remote.
- **failing**: any required check in `statusCheckRollup` is failing.
- **moved**: the branch tip differs from the SHA in `branches`. Note who pushed.
- **stale**: no commit on the branch in 3 or more days.
- **as left**: none of the above.

Also note commits since the log that touch no logged branch: someone else's work the user may need to know about.

## Step 5. Rank open threads and pick a first task

Start from the log's Tomorrow order, then adjust: drop merged items, raise failing ones, raise anything that unpicked handoffs or new commits make urgent. The suggested first task is the top item, with its `next` step from the log copied verbatim.

## Output

A short briefing, in this order, each section a few lines at most:

1. **Where we left off**: the log date and its Summary.
2. **What changed since**: new commits, PR and CI changes, unpicked handoffs.
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
