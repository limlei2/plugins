# AGENTS.md

A Claude Code plugin marketplace, `limlei2-plugins` (github.com/limlei2/plugins), holding one plugin: `simply`, personal coding-workflow skills. The content is Markdown prompts (`SKILL.md`) plus five Python 3 stdlib checker scripts. There is no app code, build, package manager, lint, or CI. The skills need `git`, `python3`, and `gh` (for PRs and CI) at runtime.

## Layout

```
.claude-plugin/marketplace.json        lists every plugin in the repo
README.md                              marketplace overview: skill table, install, credits
simply/.claude-plugin/plugin.json      plugin manifest (name, version, description)
simply/README.md                       full user guide: one section per skill, limits, models, rules
simply/skills/<name>/SKILL.md          one folder per skill; frontmatter + instructions
simply/skills/<name>/references/       formats and long detail, loaded only when SKILL.md links them
simply/skills/<name>/scripts/          stdlib Python checkers, each with --selftest
```

## Skills

Command skills run only when the user types `/simply:<name>`:

| Skill | Does | Writes |
| --- | --- | --- |
| `build` | One task → brief → implement → verify → self-review → one PR, or an escalation. Never spawns agents. Also runs as a factory worker ("given a brief" mode). | branch `build/<slug>`, commits, PR |
| `factory` | Plans 2–5 independent tasks, writes briefs, waits for the user to confirm, then dispatches parallel `build` workers in worktrees (or `research` workers), checks every result itself, retries once. The only skill that spawns agents. | `.simply/factory/<run>/*.md` |
| `research` | One question → sourced findings → one recommendation. Never edits files. | nothing |
| `goodnight` | End of day: writes the daily log, saves durable facts to the project's `CLAUDE.md`. | `.simply/daily/YYYY-MM-DD.md`, `CLAUDE.md` |
| `goodmorning` | Reads the newest daily log and compares it with git, PRs, CI, and handoffs. Read-only apart from `git fetch`. | nothing |
| `give` | Freezes one in-progress task (stash + reapply) into a handoff file. | `.simply/handoffs/<YYYY-MM-DD-HHMM>-<slug>.md` |
| `take` | Verifies the repo matches a handoff, claims it, continues from its exact next step. | the handoff's `Status:` line |
| `new-skill` | Drafts a new skill in this plugin in the house style. | `simply/skills/<name>/` |

Rules: `rules` is an index (the only skill without `disable-model-invocation`, so Claude loads it on its own) that says when each of the 21 `rule-*` skills applies. Skills cite a rule at a step as `(rule: rule-x)` and read it by path: `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md`. The rules apply to work in this repo too.

## File contracts

Three formats are each defined once and shared by a writer, a reader, and a checker that both sides run:

| Format | Defined in | Writer | Reader | Checker |
| --- | --- | --- | --- | --- |
| Brief | `simply/skills/build/references/brief.md` | factory, build Step 1, research Step 1 | build, research (worker mode) | `factory/scripts/check_briefs.py` |
| Handoff | `simply/skills/give/references/handoff-format.md` | give | take; goodmorning reads only `Status:` | `give/scripts/check_handoff.py`, `take/scripts/verify_state.py` |
| Daily log | `simply/skills/goodnight/references/daily-log-format.md` | goodnight | goodmorning | `goodnight/scripts/check_log.py` |

Change a format, its writer, its reader, and its checker in one change (`rule-design-it-in`). `check_handoff.py` and `check_log.py` self-test against the fenced `markdown` example in their format file, so editing that example changes what the self-test checks.

## Sync points

These values are repeated across files on purpose (each skill must stand alone). Change one, then `grep -rn '<old value>' README.md simply/` and update every hit.

- **Limits:** 7 criteria per brief; 2–5 build / 2–6 research workers; 11 / 12 agents per run; 2 self-review rounds; 1 retry per task; 40 searches (15 as a worker), 3 per fact; 4 options compared. They appear in the skills' `## Limits` tables, `simply/README.md`, the root `README.md`, rule files (`rule-bounded-loops`, `rule-criteria-before-code`, `rule-smallest-change`, `rule-enforce-dont-remind`), and the defaults in `check_briefs.py`.
- **Models:** factory's `## Models` table and task classification (hard → opus/high, standard → sonnet/medium, mechanical → haiku/low) are repeated in `simply/README.md` and `rule-spend-review-where-mistakes-are-expensive`.
- **Skill list:** the root `README.md` table, and the table plus one `##` section per skill in `simply/README.md`.
- **Rule count (21):** root `README.md`, `simply/README.md` ("There are 21 rules" and its group table), and the `rules/SKILL.md` tables. The pstack credits in `simply/README.md` name the 15 rules adapted from pstack.
- **Exact strings other skills grep for:** `Status: open` / `Status: taken by <name> at <YYYY-MM-DD HH:MM>` (give, take, goodmorning, `check_handoff.py`); `## Conventions and gotchas` (goodnight, `simply/README.md`); dev-server port `3101 + task index` (factory, `rule-no-shared-writes`).

## Writing a skill

`simply/skills/new-skill/SKILL.md` Step 3 is the source of truth, and `build/SKILL.md` is the reference example. In short:

- Frontmatter: `name` matches the folder (verb or verb-noun); `description` is one sentence plus which sibling skill to use instead; `argument-hint` if it takes input; `disable-model-invocation: true`.
- Body order: `# Title` + one-sentence purpose, the **Rules** line copied from `build`, `## Modes` (if it can be a factory worker), `## Limits` as `Limit | Value | Why`, numbered `## Step N.`, `## Output` (the exact sections of the final reply), `## Guardrails`.
- Exact values, never "a few" or "as needed". Spawning agents uses exact Agent tool values (`subagent_type`, `model`, `effort`, `isolation`) in a table.
- Cross-skill paths use `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/...`, never `../`.
- Worker mode never asks the user and never spawns agents.
- Under 200 lines; move long material to `references/`. Only write what Claude would not already know. No dates or version-specific facts.
- If another skill reads this skill's output, define the format in `references/<name>-format.md` with a filled example and add `scripts/check_<name>.py`.

Rule files share one ~25-line shape: frontmatter (`disable-model-invocation: true`), `# Title`, one paragraph, `**Why:**`, `**Do:**`, `**Not this:**`, `**In simply:**` (where the plugin applies it). Add a rule only when the same mistake has come up twice (`rule-enforce-dont-remind`).

## Scripts

- Python 3 stdlib only, `#!/usr/bin/env python3`, a module docstring saying what it checks and its exit codes or usage.
- Checkers expose `check(...)` returning a list of error strings; the CLI prints `ok` or one error per line and exits 0 or 1. `verify_state.py` adds exit 2 (`NEEDS_APPLY`: apply the recorded stash, then re-run).
- `--selftest` is handled first in `__main__`, uses `tempfile` (or the format file's example), prints `selftest ok`, and never touches the repo. Bad arguments exit with a `usage:` line.
- Scripts never modify the user's repo; `verify_state.py` prints fixes for the user to run.
- A known limit is a one-line comment: `# shortcut: <the limit>, <when to upgrade>`.

## Commands

```bash
for t in simply/skills/*/scripts/*.py; do python3 "$t" --selftest; done   # all five must print "selftest ok"
claude --plugin-dir ./simply                                              # load this working copy
claude plugin validate ./simply                                           # same check new-skill Step 4 runs
```

Try skills that touch git (`build`, `give`, `take`, `goodnight`, `goodmorning`) in a scratch repo, not this one.

## Change checklists

- **Add a skill:** run `/simply:new-skill`, then add it to the root `README.md` table and to `simply/README.md` (table + section).
- **Add or remove a rule:** the rule folder, its row in `rules/SKILL.md`, the group table and count in `simply/README.md`, the count in the root `README.md`. On removal, `grep -rn 'rule-<name>' simply/` and drop every citation.
- **Change a format:** the format file, writer skill, reader skill, and checker (plus its self-test) together.
- **Change a limit or model:** see Sync points.
- **Add a plugin:** `<plugin>/.claude-plugin/plugin.json`, `<plugin>/skills/`, an entry in `.claude-plugin/marketplace.json`, a row in the root `README.md`.
- **Version:** bump the minor `version` in `simply/.claude-plugin/plugin.json` when skill behaviour changes; doc-only edits leave it.
- **Commits:** history so far is short lowercase messages directly on `main`. The Conventional Commits and PR flow inside `build` is for the projects it runs in, not this repo.

## Don't

- Add third-party Python packages or any build step.
- Remove `disable-model-invocation: true` from a command skill.
- Copy generic advice into a skill ("write clean code").
- Drop the pstack attribution (MIT, Lauren Tan) from either README.
