---
name: rule-script-repeated-work
description: "Apply when work is repeated, bulk, or needs re-checking: edits across many files, migrations, analyses, validations. Write the script that does or proves it, so anyone can rerun it."
disable-model-invocation: true
---

# Script Repeated Work

For non-trivial work, write a script, codemod, or check that does it or proves it, instead of doing it by hand. The script is the artifact a reviewer reruns. Skip it only for a couple of edits you can see at a glance.

**Why:** Hand-done work can only be re-verified by redoing it, and it drifts between units; a script does every unit the same way and reruns for free.

**Do:**
- Do the first unit by hand to learn the recipe, then script it and rerun it on that unit; the diff against your hand version must be empty.
- Make it safe to rerun: a second run changes nothing.
- Give every script a `--selftest` that checks a known-good example.
- Run a script that covers every unit yourself; do not fan out agents to hand-apply what one script does in one pass.
- Keep the smallest script that works (`rule-smallest-change`), never a framework.

**Not this:**
- Editing 30 call sites by hand when a `sed` or codemod does it.
- "I checked all the files" with no command anyone can rerun.
- Spawning 5 workers to apply the same mechanical rename.

**In simply:** `check_briefs.py`, `check_handoff.py`, `verify_state.py`, `check_log.py`, and `recent_sessions.py` are levers; `/simply:new-skill` requires deterministic work in `scripts/` with a `--selftest`.
