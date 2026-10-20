---
name: rule-delete-first
description: "Apply when sequencing a feature, refactor, or rewrite on existing code. Remove dead code, redundant layers, and stale references first, then build on the simpler base."
disable-model-invocation: true
---

# Delete First

Before adding to a system, remove what it no longer needs: dead code, unused exports, redundant checks, stub files. Land the removal first, then build the new thing on the smaller base.

**Why:** Building on top of dead or duplicated code makes the new code work around things that should not exist, and the cruft becomes harder to delete once something depends on it.

**Do:**
- Before the first new line, grep the area for unused functions, exports, flags, and files; delete the ones with zero callers.
- Commit the deletion as its own commit (`refactor(<scope>): remove ...`) with checks green, before the feature commit.
- Delete a doc, reference, or prompt section that adds nothing new instead of leaving a stub or a "see X" pointer.
- Support only the inputs the code actually receives today; drop guards for cases no caller produces.

**Not this:**
- Adding a new code path next to an old one "until we migrate".
- Commenting code out instead of deleting it; git keeps history.
- Polishing (naming, docs, tests) code that the same change will delete.

**In simply:** `/simply:build` Step 4 commits each working unit separately, so a removal commit lands before the addition. `/simply:new-skill` Step 2 checks for overlap before adding a skill.
