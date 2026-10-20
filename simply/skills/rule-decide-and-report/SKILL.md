---
name: rule-decide-and-report
description: "Apply when tempted to ask 'should I do X?' about reversible work. Decide, act, and report what you did and why; explicit wait points in a skill and irreversible actions still stop for the user."
disable-model-invocation: true
---

# Decide and Report

The user reviews after the fact. For reversible work (editing code, writing files, splitting tasks, choosing between two reasonable readings) pick one, do it, and report the choice and the reason. A wrong reversible choice costs less than a stalled session.

**Why:** Every "should I?" stops the work until the user returns, and most of them have an obvious answer the agent could have taken and noted.

**Do:**
- On ambiguity, take the most literal reading, record it as an assumption, and continue.
- Report choices in the output: what you decided, why, and how to undo it.
- Stop and wait at every explicit wait point a skill defines, with no exceptions.
- Stop for irreversible or outward-facing actions: force-push, deleting data, sending messages, merging, publishing.
- When you must ask, ask once, before work starts, in the format of `rule-ask-with-context`.

**Not this:**
- "Should I add a test for this?" on a task whose criteria need one.
- "Want me to continue?" after each step.
- Skipping `/simply:factory`'s Step 3 confirm because this rule says not to block.

**In simply:** `/simply:build` writes the brief and continues without waiting, and records literal readings under Assumptions. Wait points it never overrides: `/simply:factory` Step 3 (confirm before dispatch), `/simply:goodmorning` (wait for the user to pick the first task), `/simply:take` on a mismatch.
