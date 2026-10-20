# limlei2-plugins

My Claude Code plugin marketplace. Each plugin lives in its own folder.

| Plugin | What it holds |
| --- | --- |
| [simply](simply/) | Personal skills for everyday tasks, run as `/simply:<skill>` |

## Layout

```
.claude-plugin/marketplace.json       lists every plugin in this repo
<plugin>/.claude-plugin/plugin.json   that plugin's manifest
<plugin>/skills/<name>/SKILL.md       one folder per skill
<plugin>/skills/<name>/references/    optional detail, loaded only when linked
```

## Try a plugin without installing

```bash
claude --plugin-dir /Users/user/Desktop/dev/plugins/simply
```

## Install

In Claude Code:

```
/plugin marketplace add /Users/user/Desktop/dev/plugins
/plugin install simply@limlei2-plugins
```

## Add a skill or plugin

- Skill: run `/simply:new-skill <what it should do>`, or copy `simply/skills/new-skill/`.
- Plugin: add `<plugin>/.claude-plugin/plugin.json` and `<plugin>/skills/`, then add an entry to `.claude-plugin/marketplace.json`.
