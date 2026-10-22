---
name: rule-spend-review-where-mistakes-are-expensive
description: "Apply when deciding how hard to check or which model to use for a task. Scale review to the cost of a mistake: a light check for mechanical work, full review and the strongest model for auth, payments, migrations, and concurrency."
disable-model-invocation: true
---

# Spend Review Where Mistakes Are Expensive

Review effort follows the cost of being wrong, not the size of the diff. A rename needs its checks to pass. A change to auth, permissions, payments, secrets, a data migration, or concurrency gets the strongest model, a full review, and evidence on the real surface.

**Why:** Uniform review either wastes the strong model on renames or lets a one-line auth bug through with the same glance a typo fix gets.

**Do:**
- Classify first: hard (auth, permissions, payments, secrets, concurrency or locking, data migration; file count alone is not hard), mechanical (rename, copy, config value, dependency bump, no logic change), standard otherwise.
- Hard: `model: "opus"`, `effort: "high"`; check each criterion on the real surface and read every changed line yourself.
- Mechanical: `model: "haiku"`, `effort: "low"`; the checks passing and a diff scan for out-of-scope files is enough.
- Standard: `model: "sonnet"`, `effort: "medium"`; the normal verify and self-review.
- A one-line change in a hard area is still hard.

**Not this:**
- A haiku worker on a "small" change to session token handling.
- An opus full review of a dependency bump.
- Merging a migration because the migration command exited 0.

**In simply:** `/simply:subagents`' Models table and hard/standard/mechanical classification. `/simply:tdd` verifies data changes by querying, not by exit code; `/simply:review` re-runs every brief's Checks itself.
