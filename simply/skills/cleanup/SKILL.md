---
name: cleanup
description: "After pipeline runs finish, shows a rundown per run, then on one go deletes their branches, worktrees, run folders, and taken handoffs, updates AGENTS.md and README.md, and suggests workflow improvements. For end-of-day notes use /simply:goodnight instead."
disable-model-invocation: true
---

# Cleanup

Remove what finished runs left behind so later agents don't read stale context, keep what was learned in `AGENTS.md`, and point out what to improve.

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

**Plugin root:** if `${CLAUDE_PLUGIN_ROOT}` appears literally in this file (you opened it with Read, so nothing filled it in), it means the folder two levels above this `SKILL.md`, e.g. `/…/simply` for `/…/simply/skills/cleanup/SKILL.md`. Substitute that absolute path everywhere below before running any command; the shell does not set this variable.

`survey.py` below means `python3 ${CLAUDE_PLUGIN_ROOT}/skills/cleanup/scripts/survey.py`. An angle-bracket value (`<repo root>`, `<base>`) is what an earlier command printed: run that command on its own, then write the printed value literally. Run folders and `run.md` fields: `${CLAUDE_PLUGIN_ROOT}/skills/start/references/run-format.md`.

**Commands:** write every file with the Write or Edit tool, never `cat > … <<EOF`, `echo >`, or `printf >`. One step per Bash call: no `cd "$PWD"`, and don't chain unrelated steps with `;` or `&&`. Commit messages go in separate `-m` flags with no newline inside a quote. Why: Claude Code can't check heredocs or multi-line quoted strings, so each such call stops for a permission prompt the user can't permanently allow.

## Limits

| Limit | Value | Why |
| --- | --- | --- |
| Go prompts | 1 per cleanup | One rundown, one decision; asking per item turns a tidy-up into a chore. |
| Extra confirmations | 1 per branch flagged `closed-unmerged` or `no-pr` | That work exists nowhere else; one blanket go is too easy to give for it. |
| Noticed notes | 5 max | Past 5 the useful note gets buried; "nothing worth noting" is a valid answer. |
| Agents spawned | 0 | The work is short, sequential, and destructive; a second actor adds risk, not speed. |

## Step 1. Survey

```bash
git rev-parse --show-toplevel          # prints <repo root>
git -C <repo root> fetch --prune origin
survey.py <repo root>
```

`survey.py` exits 1 (not a git repo, `gh` missing or signed out): stop and show its error line. It prints JSON: `current_branch`, `dirty`, `handoffs_taken`, and per run `run`, `slug`, `stage`, `base`, `state`, `branches` (`name`, `local`, `remote`, `pr`, `unpushed`, `flags`), `worktrees` (`path`, `branch`, `dirty`). Keep the JSON out of your reply (rule: `rule-keep-context-lean`).

Runs with `state` `clean` are cleaned. `in-progress` and `skip-open-pr` runs are listed and left alone. No `clean` run and no taken handoff: say "nothing to clean" with the skipped runs and stop.

## Step 2. Sort every item

For each `clean` run:

| Item | Goes to |
| --- | --- |
| Branch with `unpushed` in its flags | **Kept, would lose work** (unpushed commits) |
| Worktree with `dirty: true` | **Kept, would lose work** (uncommitted edits); its branch is kept too |
| Branch flagged `closed-unmerged` or `no-pr`, not kept above | **Ask first** |
| Branch flagged `merged`, not kept above | **Delete** |
| Worktree with `dirty: false` | **Delete** (before its branch) |
| Run folder | **Delete** only if every branch and worktree of the run is in Delete or Ask first; otherwise **Kept** until a later cleanup |

Every path in `handoffs_taken` goes to **Delete**. Never touch `.simply/daily/`.

## Step 3. Draft the doc edits

Read each `clean` run's `design.md` and `reports/*.md` (not `tasks/`), and `git log --oneline <base>` for the runs' merged commits.

- **AGENTS.md** (the only agent-context file you edit; `CLAUDE.md` points at it). Propose a line for each lasting fact: a `(you)` decision in `design.md`, or a report Assumption or Escalation that reveals how the codebase works, only if an agent couldn't get it from the code or `git log`. Skip anything about this run alone. Propose removing each existing `AGENTS.md` line that names a file, flag, or command that no longer exists (check with `ls`, `grep`, or `--help`). No `AGENTS.md`: propose creating it with those facts, and flag in the rundown if `CLAUDE.md` doesn't contain `AGENTS.md`.
- **README.md**: propose an edit only where a merged change added, removed, or changed a feature, command, or behavior a user should know.

Each proposal is a short diff (`-` / `+` lines) with the file and the run it came from.

## Step 4. Rundown, then one go

Send one message, in this order:

1. `**<k> run(s) to clean**`, then skipped runs on one line each: `<slug>: in progress (<stage>)` or `<slug>: PR #<n> still open`.
2. One `### <slug>` section per `clean` run: stage, then each branch with its flags and PR number (`local`, `remote`, or both), each worktree, and the run folder, each under its pile from Step 2.
3. `### Handoffs`: each taken handoff path.
4. `### Doc edits`: every diff from Step 3, or `none`.
5. "Reply **go** to apply all of this, or tell me what to change. I'll ask about each **Ask first** branch separately."

Wait (rule: `rule-decide-and-report`). On changes, update the piles or diffs and send the rundown again.

## Step 5. Apply

After **go**, in this order. Each command is its own Bash call; a failure stops that item only: note the error and keep going.

1. If `current_branch` is a branch being deleted: if `dirty` is false, `git switch <base>`; otherwise stop and tell the user to commit or stash.
2. Apply the doc edits with Edit (or Write for a new `AGENTS.md`), before any run folder disappears.
3. Each **Ask first** branch: one question per branch, **Found** (`<branch>`, PR #<n> closed unmerged or no PR, `<k>` commits not on `<base>`) / **Question** (delete it?) / **My answer** (no) (rule: `rule-ask-with-context`). A yes moves it to Delete; a no moves it and its run folder to Kept.
4. Delete, worktrees first:
   ```bash
   git -C <repo root> worktree remove <path>
   git -C <repo root> branch -D <name>                 # only when local is true
   git -C <repo root> push origin --delete <name>      # only when remote is true
   ```
   Then each run folder and each taken handoff: `rm -r <run folder>`, `rm <handoff path>`.
5. Verify: run `survey.py <repo root>` again; every deleted item must be gone (rule: `rule-verify-the-real-thing`). Anything still there goes in the Output with its error.
6. Doc edits change tracked files: leave them uncommitted and say so, unless the user asked you to commit.

## Step 6. Noticed

From the cleaned runs' files and git only, never this chat's history (it may have been cleared), write up to 5 notes. Each note: what happened, the file that shows it (path, plus section or line), and where the fix goes: `AGENTS.md`, a simply skill (name it), or a habit. Look for: escalations and their questions, review loops (`run.md` log `review: changes`), retries, `size:` assumptions (estimate far off), questions brainstorm or plan asked that the code answered, and the same assumption across runs. Notes about simply skills are suggestions: never edit the plugin. Nothing found: `nothing worth noting`.

## Output

- **Cleaned:** per run, what was deleted (branches, worktrees, folder).
- **Kept:** each kept item and why.
- **Skipped runs:** slug and reason.
- **Docs:** files changed, and that they are uncommitted.
- **Noticed:** the notes from Step 6.

## Guardrails

- Never delete anything before the user's **go**: deletions are irreversible.
- Never delete a branch with unpushed commits or a worktree with uncommitted edits: that work exists nowhere else.
- Never edit `CLAUDE.md`: it points at `AGENTS.md`, and two copies drift.
- Never spawn agents, and never run from another skill or tell a pipeline stage to run this: only the user starts a cleanup.
- Never delete `.simply/daily/`: goodmorning reads it.
