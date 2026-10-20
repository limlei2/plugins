---
name: rule-question-the-assumption
description: "Apply when 2 fixes that share one premise have failed the same check. Write the premise down and test it directly before writing a third fix."
disable-model-invocation: true
---

# Question the Assumption

Two failed fixes on one premise are two pieces of evidence that the premise is wrong. Stop fixing. Write the one sentence both fixes assumed, then run one observation that would come out differently if that sentence were false.

**Why:** A third fix on the same premise spends effort exactly where the evidence says the cause is not, and each attempt adds code that must later be removed.

**Do:**
- Count: same check or same criterion failed after 2 fixes means stop. No third fix before the premise is tested.
- Write the premise as one falsifiable sentence: "The cache is invalidated on save."
- Design one test of it: a log line, a query, a minimal repro; it must give a different result if the premise is false.
- Look at which cases fail and which pass, not only how badly; the pattern usually names the real cause.
- Premise false: drop both fixes and look for what the failures share. Premise true: ask the next "why" per rule-fix-at-the-source.
- In /build, a premise you cannot test inside the brief goes into the escalation, stated verbatim.

**Not this:**
- Fix 3: "maybe it needs a longer timeout" after two timeout tweaks failed.
- Reverting fix 2 and trying fix 1 again with a small variation.
- Testing the premise by reasoning about the code instead of observing it running.

**In simply:** /build Limits (2 self-review rounds) and Step 6 (same premise fails twice: stop and escalate), /factory Step 6 (1 retry, then the user).
