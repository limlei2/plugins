---
name: rule-verify-the-real-thing
description: "Apply before calling any criterion, task, or worker result done. Verify against the real artifact (run it, read the actual value, inspect the diff), never a proxy, a self-report, or 'it compiles'."
disable-model-invocation: true
---

# Verify the Real Thing

Done means you observed the real thing doing the right thing. Run the feature on the surface the user meets, read the value where it actually lives, and read the diff that actually landed. Anything else is a guess with a confident tone.

**Why:** Proxies (exit codes, green suites that never touch the criterion, file mtimes, an agent's "all checks pass") drift from reality silently, and the gap is found by the user instead of by you.

**Do:**
- Record evidence per criterion as `command + output` or `file:line`; a criterion with no evidence row is unmet.
- Check on the user's surface: UI in the browser (default, empty, loading, error states), API with `curl`, data with a query, CLI with real arguments.
- Read a subagent's diff (`gh pr diff <n>`) before accepting its report; its summary is a claim.
- When a check is repeatable, script it and keep the command, so a reviewer re-runs it instead of trusting you.
- When an observation contradicts the code, suspect the observation method first (stale cache, wrong port, wrong branch), then the code.

**Not this:**
- "Migration exited 0, so the column exists." Query the column.
- "Tests pass" when no test exercises the changed criterion.
- "Should work", "inconclusive", or a check on a different surface, reported as a pass.
- Forwarding a worker's "done" as your verdict without reading its diff.

**In simply:** `/simply:tdd` verifies each criterion on the real surface and records it in the report; `/simply:review` reads every diff and re-runs the Checks itself; `/simply:research` Step 3 (second source for deciding facts); `/simply:take` Step 2 (verify state before trusting the handoff).
