---
name: rule-small-green-steps
description: "Apply to any multi-step change: sweeps, migrations, runs of similar edits, stacked commits. Split it into small units that each end in a passing check, and don't start the next until the current one is green."
disable-model-invocation: true
---

# Small Green Steps

Each unit is a bracket: known-good state, one change, run the check, then move on. A red check is fixed in the unit that caused it, before anything is built on top. Commit order tells the same story for the reviewer.

**Why:** A break caught in the unit that caused it is localized for free; a break found after 10 edits must be bisected, and the later edits were built on a broken base.

**Do:**
- Start from green: run the checks on the base commit first, so a failure you see is one you caused.
- One unit = one logical change that leaves every check passing; commit it before starting the next.
- In a sweep of N similar edits, run the check after each edit, not once at the end.
- A red unit stops the sequence: fix it there or revert it; never start unit N+1 on red.
- Order commits so they read as an argument: failing test, then the fix; removal before reshape; scaffold before feature.

**Not this:**
- Editing 12 call sites, then running the test suite once.
- "I'll fix the type errors after the rest of the migration is in."
- A commit that leaves the build broken because the next commit repairs it.

**In simply:** `/simply:tdd` commits after each red→green cycle with checks passing; `/simply:plan` orders blocking work first so each task lands on a green base.
