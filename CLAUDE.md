@AGENTS.md

## Claude Code notes

- The installed `simply@limlei2-plugins` can lag this working copy. Test edits with `claude --plugin-dir ./simply` and `/reload-plugins`, not the installed `/simply:*` commands.
- `${CLAUDE_PLUGIN_ROOT}` resolves to `simply/`. Substitute it when running a skill's command by hand.
- Draft new skills with `/simply:new-skill <what it should do>`.
- `/simply:goodnight` appends durable facts to this file under `## Conventions and gotchas` (it creates the heading if missing).
