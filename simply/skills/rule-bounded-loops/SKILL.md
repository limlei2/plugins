---
name: rule-bounded-loops
description: "Apply to every retry, fix, review, or search loop. Give it a hard max before entering it; on hitting it, stop and escalate with what's unresolved, what was tried, and one question."
disable-model-invocation: true
---

# Bounded Loops

Every loop gets an exact maximum written down before the first iteration. Reaching it is not a signal to try harder; it is the signal to stop and hand the decision to someone with more context. The escalation carries three things: what is unresolved, what was tried, and one question whose answer unblocks the work.

**Why:** An unbounded loop converts tokens into repeated attempts on the same wrong idea, and the user learns about it from the bill instead of from a question they could have answered in one line.

**Do:**
- Set the number before starting: 2 self-review rounds, 1 retry per task, 3 searches per criterion, 10 agents per run.
- Count every iteration; the limit applies even when the next attempt "looks close".
- On hitting it, stop editing; commit and push partial work to the branch so nothing is lost.
- Escalate in exactly three parts: Unresolved (the exact failing check and output), Tried (one line per attempt), Question (one, specific, answerable).
- When the loop is a search, write the answer with what you have and mark the rest `unknown`.

**Not this:**
- "One more fix and it should pass" on round 3.
- Raising the limit mid-run because progress seemed close.
- An escalation that says "it's not working, what should I do?" with no attempts listed.
- Five questions in one escalation instead of the one that unblocks.

**In simply:** `/simply:review` loops back to plan at most 2 times, then escalates; `/simply:tdd` self-review stops after 2 rounds; `/simply:subagents` retries a task once; `/simply:research` stops after 3 searches per criterion; `/simply:take` stops at its listed conditions.
