---
name: rule-easy-to-follow
description: "Apply when shaping or reviewing code that is hard to follow. Count the layers a reader must trace and the state they must hold, then collapse one-caller wrappers and shrink mutable scope."
disable-model-invocation: true
---

# Easy to Follow

Code is as hard as the work a reader does to understand it. Count two things: layers between a question and its answer, and state the reader must keep in mind. Cut whichever is higher.

**Why:** Pass-through layers and wide mutable state make a reader open five files to answer "where does this value come from?", and that is where bugs hide.

**Do:**
- Inline any wrapper, adapter, or service with exactly one caller and no second implementation.
- Collapse a layer that forwards the same arguments to the next one unchanged.
- Shrink state scope in this order: return values over mutation, locals over fields, fields over module state, module state over globals.
- Derive a value instead of storing and syncing a second copy.
- Check: a new reader can answer "where does X come from?" and "what can change X?" in under 30 seconds.

**Not this:**
- `UserService.get()` that only calls `userRepo.get()`.
- A module-level mutable cache read by 6 functions.
- Storing `isEmpty` next to `items` and updating both.

**In simply:** `/simply:build` Step 6 self-review reads the diff for this. Its agent-side twin is `rule-keep-context-lean`.
