# simply

My personal skills for coding. Every skill runs only when you type it: `/simply:<skill>`.

| Skill | Use it to |
| --- | --- |
| [`/simply:build`](#simplybuild) | Take one task all the way to one verified PR |
| [`/simply:factory`](#simplyfactory) | Split work into 2–5 parallel tasks, each done by its own `/build` worker |
| [`/simply:research`](#simplyresearch) | Research one question online and get one sourced recommendation |
| [`/simply:goodmorning`](#simplygoodmorning) | Start the day: where we left off, what changed overnight, what to do first |
| [`/simply:goodnight`](#simplygoodnight) | End the day: save everything tomorrow's session needs |
| [`/simply:give`](#simplygive) | Hand one in-progress task to a new chat or another agent |
| [`/simply:take`](#simplytake) | Resume a task someone handed over with `/give` |

Also included: [`/simply:new-skill`](#simplynew-skill).

## Before you start

- **Install:** `/plugin marketplace add limlei2/plugins`, then `/plugin install simply@limlei2-plugins`. To try it without installing, start Claude Code with `claude --plugin-dir <path-to>/simply`.
- **Needs:** `git`, `python3` (for the checker scripts), and `gh` signed in for anything that opens PRs or reads CI.
- **State lives in `.simply/`** in each project: `daily/` (logs), `handoffs/`, and `factory/` (briefs). Commit it to share logs and handoffs across machines, or add `.simply/` to `.gitignore` to keep them local.

A typical day:

```
/simply:goodmorning          → briefing, pick a first task
/simply:research <question>  → pick a library or approach before building
/simply:build <task>         → one PR        (or /simply:factory for several at once)
/simply:give                 → context full? hand off…
/simply:take <path>          → …and continue in a fresh chat
/simply:goodnight            → save the day for tomorrow
```

---

## `/simply:build`

**One task → one verified PR.** A single agent does everything; it never starts other agents.

```
/simply:build POST /users should return 400 when name is missing or email has no @
```

**What happens**

1. **Brief.** It writes a brief: one-sentence goal, a checklist of criteria that define "done", which files it will and won't touch, and the exact check commands. It shows you the brief and keeps going. It asks you (once, in one message) only if it can't work out the goal, a single checkable criterion, or which files to touch.
2. **Check the brief.** Missing files, contradicting criteria, or checks that can't run → it stops and tells you instead of guessing.
3. **Branch.** Creates `build/<slug>` from the latest default branch. Your working tree must be clean; it won't stash for you.
4. **Implement** the smallest change that meets the criteria, committing as it goes (`type(scope): subject`).
5. **Verify** every criterion on the real thing: UI in the browser (default, empty, loading, error states), APIs with `curl`, data by querying it, CLIs by running them. "Should work" counts as a failure.
6. **Self-review** the diff like a reviewer: bugs, missed callers, debug leftovers, out-of-scope changes. Fix, re-verify.
7. **Ship or escalate.** Pushes and opens a ready-for-review PR, or stops and reports what's unresolved, what it tried, and one question for you.

**The PR** has a Conventional Commits title and these sections: Why · What changed · Scope · Verification (criterion → evidence table) · Assumptions.

**Limits**

| Limit | Value |
| --- | --- |
| Criteria per brief | 7 |
| Self-review rounds | 2 (same failure twice → escalate) |
| Diff size | 400 changed lines, 10 files (bigger → it proposes a `/factory` split) |
| Questions to you | 1 message, before any code |

---

## `/simply:factory`

**Several independent tasks at once.** You plan with the main agent; cheaper worker agents each run `/build` on one task in their own worktree; the main agent checks every result itself.

```
/simply:factory add a slugify helper in src/slug.js, and a GET /health endpoint
/simply:factory research which date library should we use: date-fns, dayjs, or luxon?
```

The first word picks the mode: `research`, or `build` (the default).

**Before running:** your main checkout must be on the up-to-date default branch, because every worktree branches from it.

**What happens**

1. **Plan.** It writes a 4-point checkpoint: what must happen first, which tasks are independent, what they'd share, and why this many tasks. If something must land first (a schema change, a shared type), it runs **only that** and stops; run `/factory` again once it merges.
2. **Briefs.** One brief per task, saved to `.simply/factory/<run>/`, then checked by a script (sections, criteria count, no two tasks touching the same files).
3. **Confirm.** It shows you the plan and a table of task, class, model, effort, and files, then **waits for you**.
4. **Dispatch.** All workers start at once.
5. **Check.** It reads every PR diff against its brief itself; a worker's report isn't trusted as evidence.
6. **Retry once.** A failed task gets one fresh worker with an exact fix. After that, or for product/preference questions, it asks you.
7. **Report.** A table of task, model, branch, PR, verdict, and escalations. With 3+ PRs, one reviewer also checks the PRs against each other for conflicts.

**Models used**

| Task | Model | Effort |
| --- | --- | --- |
| Hard (auth, payments, secrets, concurrency, migrations, >5 files) | opus | high |
| Standard | sonnet | medium |
| Mechanical (renames, copy, config, dependency bumps) | haiku | low |
| Research worker | sonnet | medium |
| Cross-PR reviewer | opus | high |

**Limits:** 2–5 build workers (2–6 research), 1 retry per task, 11 agents total per run (12 for research). More tasks than that → it runs the first batch and lists the rest as "next run".

**Research mode** sends read-only workers out, one per option or question, then combines their findings into one comparison table and one recommendation, with facts kept separate from its own inferences.

---

## `/simply:research`

**One question, researched online, ending in one recommendation.** A single agent; it never edits files or starts other agents. `/factory research` runs it in parallel, one worker per option.

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
| Searches + page fetches | 40 (15 as a `/factory` worker) |
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
| `factory/scripts/check_briefs.py` | factory | brief sections, criteria count, no file overlap |
| `goodnight/scripts/check_log.py` | goodnight, goodmorning | daily log format |
| `goodnight/scripts/recent_sessions.py` | goodnight | today's other sessions |
| `give/scripts/check_handoff.py` | give, take | handoff format |
| `take/scripts/verify_state.py` | take | repo matches the handoff |
