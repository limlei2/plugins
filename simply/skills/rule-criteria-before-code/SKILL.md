---
name: rule-criteria-before-code
description: "Apply before writing any code for a task. Write checkable 'done' criteria first; a criterion that can't be checked against the real artifact isn't one."
disable-model-invocation: true
---

# Criteria Before Code

Before the first edit, write down what done looks like as a list of statements, each checkable by a command's output, a file's content, or a behavior you can trigger. Code is written to meet that list, and the work ends when every item has evidence. A criterion you cannot check is a wish; rewrite it or drop it.

**Why:** Without criteria written first, "done" is decided after the fact by whatever the code happens to do, scope grows mid-task, and verification has nothing fixed to verify against.

**Do:**
- Write 1 to 7 criteria; more than 7 means the task is two tasks.
- Phrase each as an observable fact with exact values: "`?limit=500` returns 200 items", not "pagination is robust".
- Next to each criterion, know the check that proves it: the command, the URL and state, or the query.
- Include the failure cases the user will hit: invalid input, empty state, error response.
- Freeze the list once work starts; a criterion that turns out wrong is an escalation or a new task, not a silent edit.

**Not this:**
- "Code is clean and well-tested."
- "Performance is improved" with no number and no command that measures it.
- Writing the criteria after the code, by describing what the code does.
- Adding a criterion mid-implementation because something extra seemed nice.

**In simply:** /build Step 1 (brief Criteria) and Step 2 (each check can run), /factory Steps 1-2 (7 criteria max per brief, checked by `check_briefs.py`), /research Step 1 (criteria as checkable questions), the format in `${CLAUDE_PLUGIN_ROOT}/skills/build/references/brief.md`.
