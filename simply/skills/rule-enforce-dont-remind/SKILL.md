---
name: rule-enforce-dont-remind
description: "Apply when the same correction or instruction comes up a second time. Turn it into a lint, check, test, or script that fails on the mistake, not more prose."
disable-model-invocation: true
---

# Enforce, Don't Remind

The second time you correct the same mistake, stop writing it down and make it impossible or loud: a lint rule, a script check, a test, a schema field. If a structural fix exists, use only that and delete the prose rule it replaces.

**Why:** Prose rules get skimmed, compressed, or lost to the next session, so the same mistake repeats; a check fails every time, for every agent.

**Do:**
- Count: a correction seen twice (in chat, Skill notes, or review) becomes a structural fix.
- Pick the cheapest enforcement in order: a type, a lint rule, a script check, a test.
- Add the case to the script's `--selftest` so the check itself is proven.
- When the lesson needs judgment and cannot be checked, move it up to the skill's Guardrails with one concrete failure example.

**Not this:**
- A third "remember to..." line in `CLAUDE.md` for the same mistake.
- A guardrail saying "keep briefs under 7 criteria" with no checker enforcing it.
- Keeping the prose rule after the lint already enforces it.

**In simply:** `/simply:goodnight` records repeated corrections as Skill notes, which become checks in a skill's `scripts/`. `check_briefs.py` enforces the 7-criteria and no-overlap rules; `run_state.py` refuses invalid run fields.
