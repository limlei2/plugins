---
name: rule-plan-strong-execute-cheap
description: "Apply when splitting work between a planner and workers. A strong model writes the plan or brief; cheaper models execute it exactly and never rewrite it; a wrong brief is escalated, not patched."
disable-model-invocation: true
---

# Plan Strong, Execute Cheap

Judgment goes into the plan, done once by the strongest model. Workers on cheaper models execute the brief exactly: no new criteria, no wider scope, no reinterpretation. A worker that finds the brief wrong stops and escalates to the planner.

**Why:** A cheap worker that "improves" its brief makes decisions it lacks the context for, and a patched brief means the planner never learns its plan was wrong.

**Do:**
- Planner (main agent): pin every decision in the brief's Constraints so no worker has to remake it.
- Planner: check briefs with `check_briefs.py` before dispatch.
- Worker: follow the brief literally; ambiguity inside a valid brief gets the most literal reading, recorded as an assumption.
- Worker: a missing file, contradictory criteria, a check that cannot pass, or a needed file outside Work in is a wrong brief; escalate with `rule-ask-with-context`.
- Planner: fix the brief and spawn a fresh worker; never resume the old one.

**Not this:**
- A worker adding a criterion it thinks is missing.
- A worker editing a file outside Work in because the task "needs it".
- A worker weakening a check so it can pass.
- The planner editing the worker's PR instead of re-briefing.

**In simply:** `/simply:plan` writes the briefs; `/simply:subagents` workers follow `/simply:tdd` in given-a-brief mode and escalate in their report instead of rewriting the brief; a retry gets a fresh worker with a `## Fix` section.
