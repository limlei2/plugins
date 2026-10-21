---
name: tdd
description: "Executes a run's planned tasks one by one with real test-first TDD on one branch, verifies each on the real surface, and writes a report per task; also the worker skill behind /simply:subagents. For parallel workers use /simply:subagents."
argument-hint: "(no arguments: runs the pending tasks of the latest /simply:start run)"
disable-model-invocation: true
---

# TDD

Turn each planned brief into tested, verified, pushed commits plus a report that review can trust, or into a precise escalation.

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

**Plugin root:** if `${CLAUDE_PLUGIN_ROOT}` appears literally in this file (you opened it with Read during a hand-off, so nothing filled it in), it means the folder two levels above this `SKILL.md`, e.g. `/…/simply` for `/…/simply/skills/plan/SKILL.md`. Substitute that absolute path everywhere below before running any command; the shell does not set this variable.

`run_state.py` below means `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/run_state.py`. An angle-bracket value (`<run>`, `<repo root>`, `<default>`, `<task base>`) is what an earlier command printed: run that command on its own, then write the printed value literally. Each Bash call starts a fresh shell, so a shell variable would have to be rebuilt in every call. Run folder, `run.md` fields, and the report format: `${CLAUDE_PLUGIN_ROOT}/skills/start/references/run-format.md`. Brief format: `${CLAUDE_PLUGIN_ROOT}/skills/plan/references/brief.md`.

**Commands:** write every file (reports, briefs, `design.md`, PR bodies) with the Write tool, never `cat > … <<EOF`, `echo >`, or `printf >`. One step per Bash call: no `cd "$PWD"`, and don't chain unrelated steps with `;` or `&&`. Commit messages go in separate `-m` flags with no newline inside a quote: `git commit -m "<subject>" -m "Co-Authored-By: …"`. Why: Claude Code can't check heredocs or multi-line quoted strings, so each such call stops the run for a permission prompt the user can't permanently allow.

## Modes

- **Inline** (the run's `execute` is `tdd`, or the user typed `/simply:tdd`): you run every task in `pending`, in number order, on one branch. Find the run with `git rev-parse --show-toplevel` (prints `<repo root>`), then `run_state.py latest <repo root>` (prints `<run>`), unless the previous stage named it. Ends with **Hand-off**.
- **Given a brief** (you are a `/simply:subagents` worker): your prompt holds one brief and an absolute report path. Work on your worktree's branch, or the branch the brief's Constraints name for a fix task. Never ask the user: decide, record the assumption, keep going (rule: `rule-decide-and-report`). Never spawn agents. Never touch `run.md`. Ends after the push; no hand-off.

In both modes execute the brief exactly: no new criteria, no wider scope, no reinterpreted goal.

## Limits

Hard limits. Hitting one means stop that task and escalate (Step 7); never push past it.

| Limit | Value | Why |
| --- | --- | --- |
| Criteria in a brief | 7 max | More than 7 means more than one task; it should be split, not squeezed. |
| Self-review rounds (Step 6) | 2 max | Two failed fixes on one premise mean the premise is wrong; a third fix wastes tokens on the same mistake. |
| Questions to the user | 0 | Execute runs unattended; anything unclear is an assumption in the report or an escalation. |

## Step 1. Set up (inline only)
```bash
run_state.py set <run> stage=execute execute=tdd
run_state.py get <run> pending    # e.g. 1,2,3 (none means stop: nothing to run, tell the user to run /simply:plan)
```
Tasks are `<run>/tasks/<n>-<slug>.md`; each report goes to `<run>/reports/<n>-<slug>.md`.

## Step 2. Branch

Find the default branch (both modes):

```bash
git symbolic-ref --short refs/remotes/origin/HEAD     # prints origin/<default>
git fetch origin <default>
```

If `symbolic-ref` fails, run `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` instead; it prints `<default>`.

Inline: `.simply/` holds the run, so leave it out of the clean-tree check. If `run_state.py get <run> branch` is `none`:

```bash
git status --porcelain -- . ':!.simply'               # must print nothing
git switch -c simply/<run-slug> origin/<default>      # <run-slug>: the run folder name without its YYYY-MM-DD-HHMM- prefix
run_state.py set <run> branch=simply/<run-slug>
```

Otherwise (a review loop) run the same clean-tree check, then `git switch <branch>` and `git pull --ff-only origin <branch>`. The clean-tree check printing anything (a dirty tree) stops the run: tell the user to commit or stash first. Don't stash for them.

Given a brief: stay on the worktree's branch. If Constraints (or a `## Fix` section) name a branch to continue, take its commits onto your branch; your worktree cannot check that branch out if another worktree holds it:

```bash
git fetch origin <branch>
git reset --hard origin/<branch>      # your worktree's own fresh branch only
```

Run the reset only if the fetch succeeded.

Then, per task, record its base: run `git rev-parse --short HEAD`; it prints `<task base>`.

## Step 3. Check the brief

Confirm every listed file exists or is meant to be created, the criteria don't contradict each other, there are 7 criteria or fewer, each check can run, and every Interfaces `Uses:` item exists with that exact name and signature (in the code, or on this branch from an earlier task). If the brief is wrong, don't patch around it: write the report with an Escalation (Step 7) and go to the next task (inline) or stop (given a brief). Ambiguity inside a valid brief: take the most literal reading, record it under Assumptions, continue.

## Step 4. Red, green, commit, per criterion

Before the first test: follow the project's `CLAUDE.md` and the nearest similar file; remove dead code the change would build on (rule: `rule-delete-first`); reshape the design rather than bolt on (rule: `rule-design-it-in`); validate untrusted input once, at the boundary (rule: `rule-validate-at-the-edges`). Stay inside "Work in"; never edit "Do not touch". A criterion that needs a file outside "Work in" is a wrong brief: escalate. Build every Interfaces `Provides:` item with exactly the name and signature written there: later tasks were briefed against that text.

For each criterion, in brief order:
1. **Red.** Write one test that asserts what a caller or user observes (rule: `rule-test-what-users-see`). Run it. It must fail, and fail for the reason the criterion names: an assertion on the missing behavior, not an import error, typo, or missing fixture. A test that passes before any code means the criterion is already met or the test is wrong; find out which and record it.
2. **Green.** Write the smallest code that makes it pass (rule: `rule-smallest-change`). Run it again: it must pass.
3. **Checks.** Run every command in the brief's Checks. All must pass; fix the first place things went wrong, not where the symptom showed (rule: `rule-fix-at-the-source`).
4. **Commit** with every check green (rule: `rule-small-green-steps`): `<type>(<scope>): <subject>`, `type` one of `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`; subject short, imperative, no trailing period. One `git add <files>` call, then one `git commit` call, as in **Commands**.

A criterion no test can observe (docs text, a config value): skip red, make the change, record "no test: <reason>" under Assumptions, and prove it in Step 5.

## Step 5. Verify on the real surface

Check each criterion against the real artifact and record the evidence: command plus result, or file and line (rule: `rule-verify-the-real-thing`). Verify on the surface the user meets:
- UI change: start the project's dev server (the `dev` script in `package.json`, or the command in `CLAUDE.md`) on the port named in the brief's Constraints (`PORT=<n>`, or `--port <n>` for Vite), else the default port, open the page in the built-in browser (`mcp__Claude_Browser__*`), and check the default, empty, loading, and error states. Evidence: the URL and what you saw in each state. Stop the server after.
- API change: call the endpoint (`curl`) and read the real response.
- Data change: query the result, don't trust the migration's exit code.
- CLI or script: run it with real arguments.

"Inconclusive", "should work", a check on a different surface, or a green suite that never exercises the criterion is not a pass. Treat it as a failure: fix at the source (rule: `rule-fix-at-the-source`), re-run all Checks, commit.

## Step 6. Self-review

Read `git diff <task base>...HEAD` as a reviewer would:
- Bugs and unhandled edge cases.
- Callers of changed code you didn't update (`grep` for every renamed or changed symbol).
- Every Interfaces `Provides:` item exists with the exact name and signature in the brief.
- Changes outside the brief's scope.
- Debug leftovers: `console.log`, `print`, commented-out code, TODOs you added, temp files.
- Comments that narrate what the code does. Keep only comments that explain a non-obvious why.
- Layers a reader must trace: one-caller wrappers, needless indirection, mutable state with wide scope (rule: `rule-easy-to-follow`).

Fix what you find, commit, then repeat Step 5. At most 2 review-fix rounds (rule: `rule-bounded-loops`). If the same premise fails twice (the same check, the same criterion), stop: write down the assumption both fixes shared and put it in the Escalation (rule: `rule-question-the-assumption`). Don't try a third fix.

Then compare `git diff --stat <task base>...HEAD` with the brief's Estimate. More than twice the estimated lines: add an Assumption `size: estimated ~<n> lines, actual <m>: <why>`. It is a note for review, not a stop.

## Step 7. Report and push

Escalate when the brief is wrong or a **Limits** value is hit (rule: `rule-ask-with-context`). Keep partial commits only if every Check passes on them; otherwise `git reset --hard <task base>` and list what you tried. Inline, the next task starts from a green branch either way.

Write the report with the Write tool to `reports/<n>-<slug>.md` (inline) or the path in your prompt (given a brief). Exactly these `##` headings, in this order, and no other `##` heading anywhere:

```markdown
## Branch
simply/add-input-validation
## Commits
- a1b2c3d feat(users): return 400 when name is missing
## Criteria
| criterion | evidence |
| --- | --- |
| POST /users without name returns 400 | `curl -s -o /dev/null -w '%{http_code}' -d '{}' localhost:3000/users` -> 400 |

## Assumptions
none

## Escalation
none
```

Commits: run `git log --oneline <task base>..HEAD` as its own call and paste its output into the file; don't capture it in a shell variable. One Criteria row per criterion, every row with evidence; an unmet criterion's evidence is the exact failure. No `|` inside a cell. Escalation is `none` or three bullets: `- Unresolved:` the criterion or check with the exact failure, `- Tried:` each attempt in one line, `- Question:` one question whose answer unblocks the task. Validate and fix until it prints `ok`:

```bash
run_state.py check-report <report path>
git push -u origin HEAD
```

Inline: go back to Step 3 for the next pending task. Given a brief: stop here.

## Output

Inline: a table `task | commits | criteria met | escalation` and each escalation's question verbatim, then the hand-off. Given a brief: the report path only.

## Hand-off

Inline only:
1. `run_state.py set <run> pending=none stage=review` and `run_state.py log <run> "execute: <n> tasks done, <k> escalated"`.
2. `run_state.py get <run> mode`. If `prompt`: send the Output summary and end with "Reply **go** to continue to review, or tell me what to change." Wait.
3. If `auto`, or after **go**: read and follow `${CLAUDE_PLUGIN_ROOT}/skills/review/SKILL.md`.

## Guardrails

- Never open a PR: review opens them on approve, so a PR now ships unchecked code.
- Never weaken, skip, or delete a check or test to make it pass: escalate a check that cannot pass; weakening it hides the failure.
