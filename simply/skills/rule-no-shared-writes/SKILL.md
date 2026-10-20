---
name: rule-no-shared-writes
description: "Apply when parallel agents or processes might write the same file, branch, port, or key. Give each its own copy first (worktree, file, port); serialize only when one shared writer is a real invariant."
disable-model-invocation: true
---

# No Shared Writes

When parallel actors might write the same thing, first ask whether they need the same thing at all. Usually they don't: give each its own branch, worktree, file, or port, and merge at the end. Lock or sequence only when one shared target is a real invariant.

**Why:** Concurrent writes to one target cause races that show up intermittently and cost far more to debug than separating up front; "be careful" instructions are not concurrency control.

**Do:**
- List every write target per actor: files, branches, lockfiles, ports, config keys.
- Give each parallel agent `isolation: "worktree"` and its own branch.
- Give each its own file or port (one brief file per task, dev server port `3101 + task index`).
- If two tasks must write one file, merge them into one task or run them in sequence, never in parallel.

**Not this:**
- Two workers editing the same `routes.ts` in parallel.
- Two workers both writing `state.json`, each "only its own field".
- Two dev servers both started on port 3000.
- Two sessions both editing the same handoff file without a `Status:` claim.

**In simply:** `/simply:factory` Step 1 (Shared state), `check_briefs.py`'s Work-in overlap check, worktree isolation in its Models table, and per-task ports. `/simply:take` claims a handoff with `Status: taken`.
