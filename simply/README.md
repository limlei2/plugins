# simply

My personal skills for coding. Every skill runs only when you type it: `/simply:<skill>`.

| Skill | Use it to |
| --- | --- |
| [`/simply:start`](#the-pipeline) | Run a task through the pipeline: brainstorm → plan → tdd or subagents → review → PR |
| [`/simply:research`](#simplyresearch) | Research one question online and get one sourced recommendation |
| [`/simply:goodmorning`](#simplygoodmorning) | Start the day: where we left off, what changed overnight, what to do first |
| [`/simply:goodnight`](#simplygoodnight) | End the day: save everything tomorrow's session needs |
| [`/simply:give`](#simplygive) | Hand one in-progress task to a new chat or another agent |
| [`/simply:take`](#simplytake) | Resume a task someone handed over with `/give` |

The pipeline stages (`brainstorm`, `plan`, `tdd`, `subagents`, `review`) can also be typed on their own. Also included: [`/simply:new-skill`](#simplynew-skill).

## Before you start

- **Install:** `/plugin marketplace add limlei2/plugins`, then `/plugin install simply@limlei2-plugins`. To try it without installing, start Claude Code with `claude --plugin-dir <path-to>/simply`.
- **Needs:** `git`, `python3` (for the checker scripts), and `gh` signed in for anything that opens PRs or reads CI.
- **State lives in `.simply/`** in each project: `daily/` (logs), `handoffs/`, and `runs/` (pipeline runs). Commit `daily/` and `handoffs/` to share them across machines, or add `.simply/` to `.gitignore` to keep them local. `runs/` is always kept out of git status automatically, so it never blocks a clean-tree check.

A typical day:

```
/simply:goodmorning          → briefing, pick a first task
/simply:research <question>  → pick a library or approach before building
/simply:start <task>         → brainstorm → plan → build → review → PR
/simply:give                 → context full? hand off…
/simply:take <path>          → …and continue in a fresh chat
/simply:goodnight            → save the day for tomorrow
```

---

## The pipeline

**One task, from idea to PR, as a chain of stages.** Each stage is its own skill and hands off to the next by itself.

```
/simply:start [prompt] <task>
   │
   ▼
brainstorm ──► plan ──► you pick: tdd or subagents ──► tdd | subagents ──► review ──► approve → PR(s)
                ▲                                                            │
                └────────────── changes needed (max 2 loops, then asks you) ◄┘
```

```
/simply:start add rate limiting to POST /login               # auto: runs straight through
/simply:start prompt add rate limiting to POST /login        # prompt: pauses after every stage
```

**Two modes**
- **auto** (default): stages hand off with no pauses.
- **prompt**: after each stage you get its summary and findings; reply **go** to continue, or say what to change.

It always stops for three things: choosing tdd or subagents (asked on every run), approving PRs in prompt mode, and the loop limit.

**State:** every run lives in `.simply/runs/<date>-<slug>/`: `run.md` (mode, stage, loop count, chosen mode, pending tasks, a log), `design.md`, `tasks/` (one brief per task), `reports/` (evidence per task), `review.md`. Stages change `run.md` only through `run_state.py`, which refuses invalid values.

| Stage | What it does | Limits |
| --- | --- | --- |
| `start` | Checks the repo is clean, creates the run, picks auto or prompt | — |
| `brainstorm` | Reads only the code the task touches; writes `design.md` (goal, approach, decisions with reasons, out of scope, open questions). Decides instead of asking; can run `/simply:research` on one "which library" question | 1 question, 1 research, 60-line design |
| `plan` | Planning checkpoint (what must land first, what's independent, what's shared), one brief per task with checkable criteria, checked by a script. **Asks you: tdd or subagents**, with a recommendation | 1–5 tasks, 7 criteria each |
| `tdd` | One agent, one branch (`simply/<slug>`), tasks in order. For each criterion: failing test first, minimal code, green, commit. Verifies on the real surface (browser, curl, query), self-reviews, writes a report per task, pushes | 2 self-review rounds |
| `subagents` | One fresh worker per task in its own worktree, all at once; each worker runs `tdd` on its brief. Models by difficulty (opus / sonnet / haiku). Checks every report, retries a task once | 5 workers, 10 agents per run |
| `review` | The main agent reads every diff against its brief and re-runs the checks itself; writes `review.md`. **approve** → opens PR(s): one for tdd, one per task for subagents. **changes** → back to `plan` with only the fixes | 2 loops, 5 findings per task, 5 PRs |

**The PR** has a Conventional Commits title and these sections: Why · What changed · Scope · Verification (criterion → evidence, from the reports) · Assumptions.

**On a loop**, `plan` writes fix tasks for the review's findings only, reuses your tdd/subagents choice, and the fix lands on the same branch (tdd) or a new worker branch built on the old one (subagents); review then opens the PR from the newest branch.

---

## `/simply:research`

**One question, researched online, ending in one recommendation.** A single agent; it never edits files or starts other agents. `/simply:brainstorm` runs it for one which-library question.

```
/simply:research which job queue fits this repo: BullMQ, pg-boss, or Graphile Worker?
```

**What happens**

1. **Brief.** It turns the question into a brief: the goal, and the facts the answer needs as checkable questions ("last release date?", "supports SSR?"). It reads your repo's package files and `CLAUDE.md` so the research fits your stack. It shows the brief and keeps going; it asks you (once) only if it can't tell what's being asked. More than 4 options → it keeps the 4 most used and says which it dropped.
2. **Gather.** Official docs and changelogs first, then the project's repo (stars, last release, open issues), then package registries. Articles and discussions count only for experience and opinion, never as the only source for a fact.
3. **Verify.** A fact that decides the pick needs a second source, or is flagged single-source. When sources disagree it keeps both and notes which is newer. After 3 failed searches for a fact, it marks it `unknown` instead of guessing.
4. **Separate** facts (each with its source and the date or version it applies to) from inference (each with a high, medium, or low confidence) and unknowns.

**What you get**, always in this order: Answer · Findings (table of question, answer, source, as-of) · Inference · Unknowns · Sources · Recommendation (exactly one pick, the findings that decide it, and the one fact that would change it).

**Limits**

| Limit | Value |
| --- | --- |
| Options compared | 4 |
| Facts per option | 7 for one option; 5 each when comparing 2–4 |
| Searches + page fetches | 40 (20 when brainstorm runs it) |
| Searches per fact before `unknown` | 3 |
| Questions to you | 1 message, before searching |

---

## `/simply:goodmorning`

**Start of day briefing. Read-only:** it changes nothing except fetching from the remote.

```
/simply:goodmorning
```

**What happens**

1. Reads the newest log in `.simply/daily/` (written by `/goodnight`) and validates it.
2. Compares it with reality since then: new commits, branch and PR state, CI, and handoffs nobody has taken yet.
3. Flags each open item: **merged**, **gone**, **failing**, **moved** (someone pushed), **stale** (3+ days without commits), or **as left**.
4. Ranks open threads: failing first, then open handoffs, then last night's "Tomorrow" order.

**The briefing** (40 lines max): Where we left off · What changed since · Open threads (top 7, each with its next step) · Open questions · Suggested first task. Then it **waits** for you to confirm or pick something else.

No log yet? It says so and briefs you from git alone.

---

## `/simply:goodnight`

**End of day.** Saves everything tomorrow's `/goodmorning` needs.

```
/simply:goodnight
```

**What it gathers:** today's commits, your PRs and reviews, today's handoffs, this conversation, and (briefly) today's other Claude sessions in the same project.

**What it writes:** `.simply/daily/YYYY-MM-DD.md`, always these sections in this order: Summary · Done (each with how it was verified) · In progress (each with branch and exact next step) · Blocked · Decisions · Open questions · Tomorrow (top 5, ranked) · Skill notes · Handoffs · Durable facts saved. A script validates the file; running goodnight twice in a day updates the same file.

**Lasting facts** (a new convention, a gotcha) go into `CLAUDE.md` under `## Conventions and gotchas`, 5 max per run. If the project has no `CLAUDE.md` it uses `README.md`; it asks before creating `CLAUDE.md`.

**Skill notes:** where a skill misfired or you corrected the agent twice, it suggests a change. It never edits a skill itself.

It never commits the log or the doc changes.

---

## `/simply:give`

**Hand off one in-progress task** when context is filling up, you're switching chats, or another agent should continue.

```
/simply:give email-validation
```

The optional argument names the handoff; anything after it is passed on as a note to the receiver.

**What happens**

1. **Freezes the code state.** It records the branch and commit, and saves your uncommitted changes in a git stash, then immediately restores them. Your files look exactly as before, and nothing is committed.
2. **Writes the handoff** to `.simply/handoffs/<YYYY-MM-DD-HHMM>-<slug>.md`: Goal · Done so far (each verified) · In progress · Exact next step · Decisions and why · Dead ends (so nobody retries them) · Files involved · Code state · How to verify · Open questions · Note from giver.
3. **Checks it** with a script, then rereads it as a stranger would and fixes anything that only makes sense with this chat's history.

**Output:** the file path and a line to paste into the new chat: `/simply:take <path>`.

**Other machine?** The stash exists only in this clone. Commit and push your work first if the receiver is elsewhere.

---

## `/simply:take`

**Resume a handoff** from `/give`, after proving the code in front of you is the code the handoff describes.

```
/simply:take .simply/handoffs/2026-10-20-1711-email-validation.md
/simply:take                        # takes the newest open handoff
```

**What happens**

1. **Finds and validates** the handoff. An incomplete one stops here.
2. **Verifies the repo** with a script: branch, commit, stash, files, working tree. If the tree is clean and the giver's changes are in the stash, it applies the stash and checks again. On any mismatch it shows you an expected-vs-actual table with the fix for each, and **stops without fixing anything itself**.
3. **Restates** the goal and next step in one paragraph, then marks the handoff `Status: taken by <you> at <time>`.
4. **Continues** from the exact next step. It respects recorded decisions, doesn't retry dead ends, and stops when the handoff's checks pass, when it needs a decision the handoff doesn't cover, or when work would go beyond the listed files.

---

## `/simply:new-skill`

**Drafts a new skill** in this plugin, in the same style as the ones above: exact limits with reasons, numbered steps, fixed output, scripts for anything mechanical.

```
/simply:new-skill review a PR against our API conventions
```

---

## Rules

Every rule is a `rule-<name>` skill. You don't run them as commands: the skills above use them, the `rules` index tells Claude which one applies when, and you can steer with their names ("apply rule-verify-the-real-thing", "question the assumption"). Each rule file is read only when it applies.

There are 21 rules, grouped below. New rules are added only when Claude repeatedly misses something (`rule-enforce-dont-remind`).

| Group | Rules |
| --- | --- |
| Verifying and debugging | verify-the-real-thing · fix-at-the-source · question-the-assumption · test-what-users-see · small-green-steps · criteria-before-code · bounded-loops |
| Code and design | smallest-change · delete-first · easy-to-follow · validate-at-the-edges · design-it-in · script-repeated-work · enforce-dont-remind |
| Agents and workflow | no-shared-writes · keep-context-lean · decide-and-report · ask-with-context · state-lives-in-files · spend-review-where-mistakes-are-expensive · plan-strong-execute-cheap |

**Credits:** 15 of the working rules adapt ideas from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT License), rewritten and renamed for simply: verify-the-real-thing, fix-at-the-source, question-the-assumption, test-what-users-see, small-green-steps, smallest-change, delete-first, easy-to-follow, validate-at-the-edges, design-it-in, script-repeated-work, enforce-dont-remind, no-shared-writes, keep-context-lean, decide-and-report. The skill layout and the brief/worker pattern are also inspired by pstack.

---

## For maintainers

Every checker script has a self-test:

```bash
for t in simply/skills/*/scripts/*.py; do python3 "$t" --selftest; done
```

| Script | Used by | Checks |
| --- | --- | --- |
| `start/scripts/run_state.py` | every pipeline stage | creates runs, reads/sets `run.md` fields (validated), logs, checks task reports |
| `plan/scripts/check_briefs.py` | plan | brief sections, 1–5 tasks, 7 criteria, no file overlap in subagents mode |
| `goodnight/scripts/check_log.py` | goodnight, goodmorning | daily log format |
| `goodnight/scripts/recent_sessions.py` | goodnight | today's other sessions |
| `give/scripts/check_handoff.py` | give, take | handoff format |
| `take/scripts/verify_state.py` | take | repo matches the handoff |
