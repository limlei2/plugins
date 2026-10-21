---
name: goodmorning
description: "Start of day: reads the last daily log, checks it against git, PRs, CI, and open handoffs, and suggests a first task. Changes nothing."
disable-model-invocation: true
---

# Goodmorning

Brief the user on where work stands, comparing last night's log with reality, then wait. This skill only reads.

The log format is defined in `${CLAUDE_PLUGIN_ROOT}/skills/goodnight/references/daily-log-format.md`. Read it first; parse the log by its exact headings and ` | key: value` fields.

An angle-bracket value (`<repo root>`, `<log>`, `<since>`) is what an earlier command printed or the log said: get it once, then write it literally. Each Bash call starts a fresh shell, so a shell variable would have to be rebuilt in every call.

**Commands:** write every file (reports, briefs, `design.md`, PR bodies) with the Write tool, never `cat > … <<EOF`, `echo >`, or `printf >`. One step per Bash call: no `cd "$PWD"`, and don't chain unrelated steps with `;` or `&&`. Commit messages go in separate `-m` flags with no newline inside a quote: `git commit -m "<subject>" -m "Co-Authored-By: …"`. Why: Claude Code can't check heredocs or multi-line quoted strings, so each such call stops the run for a permission prompt the user can't permanently allow.

## Step 1. Find the newest log

```bash
git rev-parse --show-toplevel        # prints <repo root>
ls <repo root>/.simply/daily/
```

If the first command fails (not a git repo), stop and say so. The newest log is the last `.md` file in name order (names are dates); its full path is `<log>`. If there is none, say "No daily log found" and skip to Step 3 with `<since>` two days ago: run `date -v-2d +%FT%T` (macOS), or `date -d '2 days ago' +%FT%T` if that fails.

Otherwise read the log and take from its header: `updated`, `head`, and `branches`. `<since>` is `updated`. If the log is more than 7 days old, say so in the briefing.

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
git log --all --since=<since> --format='%h %an %D %s'
git branch --show-current
git status --short
gh pr list --author @me --state all --search "updated:>=<since date>" --json number,title,state,headRefName,mergedAt
```

`<since date>` is the `YYYY-MM-DD` part of `<since>`.

For each branch in the log's `branches` and In progress items:

```bash
git rev-parse --short <branch>       # fails if the branch is gone
git log -1 --format=%cr <branch>
gh pr view <branch> --json number,state,mergedAt,statusCheckRollup
```

A failing `rev-parse` means the branch is gone; skip the other two for it.

Handoffs: list every file under `<repo root>/.simply/handoffs/`. Read only its `Status:` line. A file with `Status: open` is not yet taken; anything else is taken. If the field is missing, list the file as "status unknown".

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
