---
name: rule-fix-at-the-source
description: "Apply when a check fails or a bug shows up. Trace the symptom to the first place the system went wrong and fix it there; a guard is a fix only when the state it handles is legitimate."
disable-model-invocation: true
---

# Fix at the Source

The symptom is where a bad state became visible; the root cause is the first decision that produced it or failed to handle it. Fix that decision. Before adding a guard, ask whether the system is allowed to be in the state the guard catches: if yes, handling it is the fix; if no, the guard hides the bug.

**Why:** A fix at the symptom leaves the fault in place to surface elsewhere, and each unnamed workaround makes the next bug harder to trace.

**Do:**
- Reproduce the failure with one exact command before editing anything.
- Ask "why" at each step back until the answer is a wrong decision in code, not a consequence of an earlier one.
- When stuck, instrument: print the actual state at the boundary, read the full error. Do not guess.
- If it fails only after a restart, check persisted state first: config, caches, lock files, serialized data.
- `grep` for the same faulty pattern and fix every instance, not just the one that failed.
- After the fix, re-run the reproduction command and every check.

**Not this:**
- `if (user == null) return []` where `user` should never be null; find who passed null.
- Wrapping a flaky call in a retry, or catching and swallowing the error, to turn a check green.
- Clamping an out-of-range value at render time instead of where it was computed.
- A workaround that needs a paragraph of comment to justify it.

**In simply:** /build Step 5 (when a check fails) and Step 6 (self-review fixes); rule-question-the-assumption takes over after 2 failed fixes on one premise.
