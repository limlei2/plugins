---
name: rule-ask-with-context
description: "Apply when a skill must ask the user or escalate. Interviews ask one question per message with what you found and your recommended answer; escalations say what is unresolved, what was tried, and one question, batched in one message."
disable-model-invocation: true
---

# Ask With Context

When you must stop for the user, the message must be answerable without scrolling back. There are two kinds. An **interview** (designing or planning) asks one question per message, each with what you found and the answer you'd pick, because each answer changes what the next question should be. An **escalation** (work is stuck) names what is unresolved and what you tried, batches every question into one message, and waits.

**Why:** A vague "how should I proceed?" costs the user a round of re-reading the session. In an interview, a list of questions gets skimmed and answered without thought; in an escalation, questions sent one at a time cost a round each.

**Do:**
- Ask only what `rule-decide-and-report` cannot decide: a product or preference choice, a wait point, an irreversible action, or a hit limit.
- Interview: **Found** (what the code says, with file:line), **Question** (one sentence), **My answer** (your pick and why). Check the code first; never ask what it answers. Stop when the user replies **skip**, and decide the rest.
- Escalation: **Unresolved** (the exact criterion, check, or error text), **Tried** (one line per attempt), **Question** (one, answerable in a word or a choice). Collect all questions first, send them in one message, and wait.
- Either way, offer the answer you'd pick, so "yes" is a valid reply.

**Not this:**
- "What do you want me to do?"
- An escalation split across three messages, or an interview message with three questions.
- An escalation with no error text or attempts listed.
- Asking a question already answered in the brief's Constraints or the handoff's Decisions.

**In simply:** `/simply:brainstorm` and `/simply:plan` interview one question at a time; a `/simply:tdd` report's Escalation (Unresolved, Tried, Question); `/simply:review` escalates after loop 2 and sends product questions to the user; `/simply:goodnight` asks once for all missing `next` fields.
