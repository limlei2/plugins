---
name: new-skill
description: "Drafts a new skill in this plugin, following the house style."
argument-hint: "[what the skill should do]"
disable-model-invocation: true
---

# New Skill

Draft a new skill in `simply/skills/<name>/` from `$ARGUMENTS`. If `$ARGUMENTS` is empty, use the workflow from the current conversation. `/simply:build` is the reference example of the house style; read it before writing.

**Rules:** a step marked (rule: `rule-x`) applies that rule. Before doing the step, read `${CLAUDE_PLUGIN_ROOT}/skills/rule-x/SKILL.md` (once per session); the label alone is not the rule.

## Step 1. Pin down the job

Work out four things: the task the skill performs, what it hands back, what it must never do, and whether another skill reads its output. If any is unclear after reading the conversation, ask once with all questions together, then wait.

## Step 2. Check for overlap

List `simply/skills/`. If an existing skill already covers the job, say which one and stop, or propose extending it instead.

## Step 3. Write `simply/skills/<name>/SKILL.md`

**Frontmatter**
- `name`: lowercase, hyphens, matches the folder, a verb or verb-noun (`review-pr`, not `helper`).
- `description`: one sentence: what it does, and which sibling skill to use instead when one fits better.
- `disable-model-invocation: true` by default: skills here run only when the user types them. Leave it off only for background rules that should load on their own (then the description must list the situations that trigger it, and `paths:` should limit it to matching files).
- `argument-hint` when it takes input.

**Body, in this order**
1. `# Title` and one sentence of purpose.
2. `## Modes`, if it runs both standalone and as a `/simply:factory` worker. The worker mode never asks the user and never spawns agents.
3. `## Limits`: a table `Limit | Value | Why` for every count that can run away (rounds, retries, agents, searches, diff size, items in a list). The Why is one line saying what goes wrong past the limit.
4. Numbered `## Step N.` sections. Exact commands for fragile steps, in fenced `bash` blocks. A check-and-fix loop for anything that can fail.
5. `## Output`: the exact sections of the final reply.
6. `## Guardrails`: concrete failure modes, one line each.

**House rules**
- Exact values, not judgment: "5 max", `model: "sonnet"`, `effort: "medium"`, not "a few" or "a cheaper model". Spawning agents uses exact Agent tool values (`subagent_type`, `model`, `effort`, `isolation`) in a table.
- Point at other skills' files with `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/...`, never a relative `../` path.
- If another skill reads this skill's output, define the format once in `references/<name>-format.md` with a filled-in example, and add `scripts/check_<name>.py` that validates it, with a `--selftest` that checks the example. Both skills run the script.
- Deterministic work (parsing, validating, comparing state) goes in `scripts/`, not in prose the model re-derives each run. Every script gets a `--selftest` (rule: `rule-script-repeated-work`).
- Cite the rule a step applies as (rule: `rule-x`) at that step, and include the **Rules** line from `/simply:build` under the title. Pick rules from `${CLAUDE_PLUGIN_ROOT}/skills/rules/SKILL.md`.
- Write only what Claude would not already know. Keep the body under 200 lines; move long material to `references/`, linked directly from SKILL.md.

## Step 4. Check

```bash
claude plugin validate ${CLAUDE_PLUGIN_ROOT}
for t in ${CLAUDE_PLUGIN_ROOT}/skills/<name>/scripts/*.py; do python3 "$t" --selftest; done
```

Then read the draft as a fresh agent: could it follow every step without guessing? Every "some", "a few", "as needed", "if appropriate" is a guess; replace it with a value. Fix and re-read until there are none.

## Output

The path of the new skill, its description line, any scripts with their self-test result, and the command to try it: `/simply:<name>`. Remind the user to restart or `/reload-plugins` so it appears.

## Guardrails

- Do not create agents, hooks, or scripts unless the job needs them.
- Do not copy generic advice Claude already follows ("write clean code").
- Do not put dates or version-specific facts in the body.
