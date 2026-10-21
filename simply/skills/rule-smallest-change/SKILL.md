---
name: rule-smallest-change
description: "Apply when choosing how much code a change needs, or when tempted to add a layer, option, or helper. Make the smallest change that meets every criterion, and prefer deleting code to adding it."
disable-model-invocation: true
---

# Smallest Change

Make the smallest change that meets every criterion. Deleting code beats adding it, and existing code beats new code. Add nothing for a case nobody has asked for yet.

**Why:** Every speculative layer, flag, or wrapper is code someone must read, test, and keep working, and most "for later" code is never used.

**Do:**
- Before writing, check in order: does it need to exist, does the repo already have it, does the standard library or an installed dependency have it. Take the first yes.
- Put each decision in one place and pass the result; never repeat the same `if` in several callers.
- Count the diff (`git diff --stat`) before self-review; if a smaller diff meets the same criteria, switch to it.
- Write a known limit as a one-line comment: `shortcut: <the limit>, <when to upgrade>`.

**Not this:**
- A config option or parameter with exactly one value ever passed.
- An interface or base class with one implementation.
- A new helper that duplicates one already in `utils/`.
- "While I'm here" edits outside the brief's Work in files.

**In simply:** `/simply:tdd` writes the minimal code to pass each failing test; its 400-line, 10-file diff limit per task enforces it. `/simply:plan` asks for the smallest decomposition.
