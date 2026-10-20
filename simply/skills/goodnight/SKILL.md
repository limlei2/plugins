---
name: goodnight
description: "End of day: writes .simply/daily/<date>.md for /simply:goodmorning and saves lasting project facts to CLAUDE.md. To hand off one task mid-day use /simply:give."
disable-model-invocation: true
---

# Goodnight

Write today's daily log so a fresh session tomorrow can resume without asking anything. (rule: `rule-state-lives-in-files`)

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule. The log format is fixed in [daily-log-format.md](references/daily-log-format.md). Read it first and follow it exactly; `/simply:goodmorning` parses it.

## Step 1. Locate the log

```bash
ROOT=$(git rev-parse --show-toplevel) && cd "$ROOT"
TODAY=$(date +%F)
LOG=".simply/daily/$TODAY.md"
```

If not in a git repo, stop and say so. If `$LOG` exists, read it: this run merges into it (Step 4), it does not start over.

## Step 2. Gather the day's work

Run these, ignoring any that fail because a tool is missing:

```bash
ME=$(git config user.email)
git log --all --since=midnight --author="$ME" --format='%h %D %s'
git branch --show-current; git rev-parse --short HEAD
git status --short
gh pr list --author @me --state all --search "updated:>=$TODAY" --json number,title,state,headRefName,url
gh pr list --search "reviewed-by:@me updated:>=$TODAY" --state all --json number,title,url
find .simply/handoffs -type f -newermt "$TODAY" 2>/dev/null
```

If `gh` is missing or unauthenticated, say so in the reply and continue with git only.

Other sessions in this project today (5 max, excluding this one):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/goodnight/scripts/recent_sessions.py "$ROOT" "${CLAUDE_SESSION_ID}"
```

Each result is a first request and a last reply, not a full record: use it to add Done or In progress items only where the reply states the outcome, and mark them `verified: unverified` unless a commit or PR above confirms them.

Then read back through the current conversation for: what was finished and how it was checked, what is half done and the next concrete action, decisions and their reasons, questions the user never answered, things blocked on someone else, and skill misfires or corrections the user repeated.

## Step 3. Fill every field from evidence

For each item, use what the commands and conversation show. Do not invent.

- **Done `verified`**: the actual check that passed (test command and count, CI status from `gh pr checks <n>`, a manual check the user confirmed). If nothing verified it, write `verified: unverified`.
- **In progress `next`**: precise enough to act on cold, naming the file, function, command, or failing test. "Continue work" is not a next step. If you cannot name one, ask the user.
- **Uncommitted changes** from `git status` on a branch go under In progress with that branch, and `next` says to commit or finish them.
- **Tomorrow**: 5 items max, ranked by these rules in order: (1) items that unblock someone else, (2) In progress items with the fewest remaining steps, (3) everything else in the order the user mentioned them.
- **Skill notes**: 5 max, only incidents from this session: the user corrected the agent, a skill step was skipped or wrong, or the same instruction was repeated. Each names the skill, what happened, and the suggested change. A correction made twice should be suggested as a check or script, not more text (rule: `rule-enforce-dont-remind`). Never edit the skill.

If an In progress item has no `next` or a Blocked item has no `unblocks`, ask the user once, listing all gaps together, then wait (rule: `rule-ask-with-context`). If the user doesn't supply one, write `next: missing` or `unblocks: missing`; never invent one.

## Step 4. Write the log

Create `.simply/daily/` if missing. If today's log already exists, merge: keep earlier items, update any that changed state (an In progress item now Done moves to Done), drop exact duplicates, and set `updated` to now. Write the whole file in the format's exact headings and order, with `- none` for empty sections.

Check it, fix every error it prints, and re-run until it prints `ok`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/goodnight/scripts/check_log.py "$LOG"
```

`/simply:goodmorning` runs the same script before reading, so a log that fails here is a log tomorrow can't parse.

## Step 5. Save durable facts

A durable fact is true beyond today: a new convention, a gotcha, a required setup step, a command that must be run a certain way. Day-specific detail (what you did, what is pending) stays only in the log.

1. Pick the target: `CLAUDE.md` at the git root if it exists, else `README.md`. If neither exists, list the facts in the reply and ask before creating `CLAUDE.md`.
2. Skip facts already stated there. Add new ones, 5 max per run, one line each, under the heading `## Conventions and gotchas` (create it at the end of the file if missing). Never edit other sections.
3. Show the user a diff summary: file, lines added, lines changed. Record each fact in the log's `## Durable facts saved`.

If there are no new durable facts, write nothing and say so.

## Output

- Path of the log written, and whether it was new or merged.
- The Summary and the ranked Tomorrow list.
- Durable-facts diff summary, or "no new durable facts".
- Suggested skill changes from Skill notes, each marked as awaiting the user's approval.
- Any source skipped (no `gh`, no handoffs folder).

## Guardrails

- Never edit any skill file, even if a Skill note suggests a change.
- Never put day-specific status into CLAUDE.md or README.
- Never write secrets, tokens, or customer data into the log.
- Do not create a second log file for the same day.
- Do not commit the log or the CLAUDE.md change unless the user asks.
- Do not mark anything Done that has no evidence; use `verified: unverified`.
