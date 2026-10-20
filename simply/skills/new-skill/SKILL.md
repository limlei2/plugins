---
name: new-skill
description: "Use for 'new skill', 'make a skill', 'add a skill to simply', or turning a workflow just done in this session into a reusable skill. Drafts simply/skills/<name>/SKILL.md in this plugins repo. Not for editing an existing skill's behavior mid-task."
argument-hint: "[what the skill should do]"
disable-model-invocation: true
---

# New Skill

Draft a new skill in this plugin from `$ARGUMENTS`. If `$ARGUMENTS` is empty, use the workflow from the current conversation.

## Step 1. Pin down the job

Work out three things: the task the skill performs, the phrases the user would type to trigger it, and what it hands back. If any is unclear after reading the conversation, ask once with all questions together.

## Step 2. Check for overlap

List `simply/skills/`. If an existing skill already covers the job, say which one and stop, or propose extending it instead.

## Step 3. Write `simply/skills/<name>/SKILL.md`

- `name`: lowercase, hyphens, matches the folder, a verb or verb-noun (`review-pr`, not `helper`).
- `description`: third person, under 1024 characters. What it does, when to use it with quoted trigger phrases, and when not to (name the sibling skill if one fits better). This is the only part Claude sees before the skill loads, so it decides whether the skill ever fires.
- `disable-model-invocation: true` when the skill has side effects (commits, sends, deletes) or should run only on command. Add `argument-hint` when it takes input, and `allowed-tools` only for narrow, specific commands.
- Body, in this order:
  1. `# Title` and one sentence of purpose.
  2. Numbered `## Step N.` sections. Exact commands for fragile steps, judgment for open ones. A check-and-fix loop for anything that can fail.
  3. `## Output`: what the final reply contains.
  4. `## Guardrails`: concrete failure modes to avoid, one line each.
- Write only what Claude would not already know. Keep the body under 200 lines. Move long reference material to `simply/skills/<name>/references/<topic>.md`, linked directly from SKILL.md, never nested deeper.
- One default approach per step, not a menu. One term per concept throughout.

## Step 4. Review

Read the draft as a fresh agent that only has the description: would it trigger on the user's phrases, and could it follow every step without guessing? Cut any sentence that changes no decision. Fix and re-read until both answers are yes.

## Output

The path of the new file, the description line, and the command to try it: `/simply:<name>`. Remind the user to restart or `/reload-plugins` so it appears.

## Guardrails

- Do not create agents, hooks, or scripts unless the job needs them.
- Do not copy generic advice Claude already follows ("write clean code").
- Do not put dates or version-specific facts in the body.
