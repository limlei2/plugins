---
name: rule-design-it-in
description: "Apply when a new requirement lands on an existing design. Fold it in as if it had been there from the start, not bolted on beside the old shape."
disable-model-invocation: true
---

# Design It In

When a requirement changes, ask what you would build if it had been known on day one, and move the design there. Then update every place that describes the old design. Deliver it in small, landable steps.

**Why:** Bolted-on requirements leave special cases, flags, and parallel code paths that each later change must work around, and the design stops making sense as a whole.

**Do:**
- Read every file the requirement touches before choosing an approach.
- Write one sentence: "From scratch with this requirement, the design would be ___." Compare it with the current design.
- Propagate the change through types, callers, tests, docs, examples, and format files, so nothing still describes the old shape.
- Ship the redesign as a sequence of commits or tasks, each leaving checks green (`rule-small-green-steps`).

**Not this:**
- `if (featureFlag) { newPath } else { oldPath }` left in permanently.
- Adding an optional field that half the code ignores.
- Updating the code but leaving the format file, README, or example on the old shape.

**In simply:** `/simply:factory` Step 1 plans blocking first steps (a shared type or schema) before parallel work. Changing a format like `handoff-format.md` means updating `/simply:give`, `/simply:take`, and `check_handoff.py` together.
