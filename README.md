# limlei2-plugins

My Claude Code plugin marketplace. Each plugin lives in its own folder.

| Plugin | What it holds |
| --- | --- |
| [simply](simply/) | My personal skills for coding, run as `/simply:<skill>` |

## simply skills

Full usage guide: **[simply/README.md](simply/README.md)**.

| Skill | What it does |
| --- | --- |
| `/simply:start [prompt] <task>` | Pipeline: brainstorm → plan → tdd or subagents → review → PR(s); auto or pause-after-each-stage |
| `brainstorm`, `plan`, `tdd`, `subagents`, `review` | The pipeline stages; each hands off to the next, and each can be typed on its own |
| `/simply:research` | One question researched online, sourced, with one recommendation |
| `/simply:goodmorning` | Start of day: reads last night's log, checks it against git/PRs/CI, suggests a first task |
| `/simply:goodnight` | End of day: writes the daily log and saves lasting facts to `CLAUDE.md` |
| `/simply:give` | Hands one in-progress task to a new chat or agent |
| `/simply:take` | Resumes a handoff after verifying the repo matches it |
| `/simply:cleanup` | After runs finish: rundown, one go, deletes run branches and temp files, updates `AGENTS.md`/`README.md`, suggests workflow fixes |
| `/simply:new-skill` | Drafts a new skill in the house style |
| `rules` + 21 `rule-*` | Working rules the skills cite at each step; see the guide |

The skills write their state to `.simply/` in each project (`daily/`, `handoffs/`, `runs/`). Commit it to share logs and handoffs across machines, or add `.simply/` to the project's `.gitignore` to keep them local.

## Layout

```
.claude-plugin/marketplace.json       lists every plugin in this repo
<plugin>/.claude-plugin/plugin.json   that plugin's manifest
<plugin>/skills/<name>/SKILL.md       one folder per skill
<plugin>/skills/<name>/references/    formats and detail, loaded only when linked
<plugin>/skills/<name>/scripts/       checkers run by the skills; each has --selftest
```

## Try a plugin without installing

```bash
claude --plugin-dir /Users/user/Desktop/dev/plugins/simply
```

## Install

In Claude Code:

```
/plugin marketplace add limlei2/plugins
/plugin install simply@limlei2-plugins
```

## Test the scripts

```bash
for t in simply/skills/*/scripts/*.py; do python3 "$t" --selftest; done
```

## Add a skill or plugin

- Skill: run `/simply:new-skill <what it should do>`.
- Plugin: add `<plugin>/.claude-plugin/plugin.json` and `<plugin>/skills/`, then add an entry to `.claude-plugin/marketplace.json`.

## Credits

Parts of `simply` adapt ideas from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT License). See [simply/README.md](simply/README.md#rules).

## Conventions and gotchas

- The installed plugin updates only from GitHub `main`, not local branches: run `claude plugin marketplace update limlei2-plugins`, then `claude plugin update simply@limlei2-plugins`, then restart Claude Code.
