---
name: start
description: "Starts a pipeline run for one task: brainstorm, plan, tdd or subagents, review, then PRs. Add `prompt` first to pause for your go after each stage."
argument-hint: "[prompt] <task>"
disable-model-invocation: true
---

# Start

Open a pipeline run for one task and hand it to brainstorm. The run's state lives in files, not in this conversation (rule: `rule-state-lives-in-files`).

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

Pipeline: start → brainstorm → plan → tdd | subagents → review → approve (PRs open) or changes → back to plan, at most 2 loops, then escalate. The run folder and `run.md` fields are defined in `${CLAUDE_PLUGIN_ROOT}/skills/start/references/run-format.md`. Every state change goes through `run_state.py`; never edit `run.md` by hand.

```bash
RS="${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/run_state.py"   # path only, so "$RS" works in bash and zsh; each Bash call starts fresh, so repeat this line
```

**Commands:** write every file (reports, briefs, `design.md`, PR bodies) with the Write tool, never `cat > … <<EOF`, `echo >`, or `printf >`. One step per Bash call: no `cd "$PWD"`, and don't chain unrelated steps with `;` or `&&`. Commit messages go in separate `-m` flags with no newline inside a quote: `git commit -m "<subject>" -m "Co-Authored-By: …"`. Why: Claude Code can't check heredocs or multi-line quoted strings, so each such call stops the run for a permission prompt the user can't permanently allow.

## Limits

| Limit | Value | Why |
| --- | --- | --- |
| Questions to the user | 1 message, only when the task is empty | Every other unclear point is brainstorm's job; asking here asks twice. |
| Pauses in this skill | 0, in both modes | Start only records the run; there is nothing yet for the user to approve. Brainstorm is the first stage that pauses in prompt mode. |

## Step 1. Parse the arguments

- First word of `$ARGUMENTS` is `prompt`: mode is `prompt`, the task is the rest.
- Otherwise: mode is `auto`, the task is all of `$ARGUMENTS`.

Empty task: ask once "What should this run build?" and wait. Use the reply as the task, verbatim.

## Step 2. Check the repo

```bash
ROOT=$(git rev-parse --show-toplevel) || { echo "not a git repo"; exit 1; }
test -z "$(git -C "$ROOT" status --porcelain -- . ':!.simply')" || { echo "dirty tree"; exit 1; }
```

- Not a git repo: stop. Tell the user the pipeline needs a git repository.
- Dirty tree: stop. Tell the user to commit or stash first, and list the changed files from `git status --porcelain -- . ':!.simply'`. Don't stash for them. `.simply/` is left out on purpose: uncommitted daily logs and handoffs are normal and don't touch code.

## Step 3. Create the run

```bash
RUN=$("$RS" new "$ROOT" <auto|prompt> "<task>")
"$RS" check "$RUN"
```

`new` writes `run.md` with `stage=brainstorm`, `loop=0`, `execute=none`, `pending=none`, and the task verbatim. If `check` prints errors, stop and show them; don't patch `run.md`.

## Output

One short block, nothing else:
- **Run:** the `$RUN` path.
- **Mode:** `auto` or `prompt`.
- **Next:** brainstorm writes `design.md`, then plan writes the task briefs and asks you to choose tdd or subagents, then the tasks run and get reviewed before any PR opens.
- Prompt mode only: "I'll pause after each stage and wait for your **go**."

## Hand-off

1. Nothing to log or set: `new` already logged `start: mode <mode>` and set `stage=brainstorm`.
2. Don't pause, in either mode.
3. Read and follow `${CLAUDE_PLUGIN_ROOT}/skills/brainstorm/SKILL.md`.

## Guardrails

- Never stash, reset, or commit the user's changes to get a clean tree.
- Never create a second run for the same task in one session; a stage typed later finds this run with `run_state.py latest`.
- Never edit `run.md` by hand; a field `set` refuses is a bug to report, not to work around.
- Never start planning or coding here. Start creates the run and hands off.
