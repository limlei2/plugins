---
name: rule-ask-with-context
description: "Apply when a skill must ask the user or escalate. Say what is unresolved, what was tried, and one specific question, with all questions batched in one message."
disable-model-invocation: true
---

# Ask With Context

When you must stop for the user, the message must be answerable without scrolling back. Name what is unresolved, what you already tried, and ask one specific question. Batch every question into one message, sent before work starts or at the escalation point, then wait.

**Why:** A vague "how should I proceed?" costs the user a round of re-reading the session, and questions sent one at a time cost a round each.

**Do:**
- Ask only what `rule-decide-and-report` cannot decide: a product or preference choice, a wait point, an irreversible action, or a hit limit.
- Use three parts: **Unresolved** (the exact criterion, check, or error text), **Tried** (one line per attempt), **Question** (one, answerable in a word or a choice).
- Offer the options you see and the one you'd pick, so "yes" is a valid answer.
- Collect all questions first, send them in one message, and wait.

**Not this:**
- "What do you want me to do?"
- Three separate messages, each with one question.
- An escalation with no error text or attempts listed.
- Asking a question already answered in the brief's Constraints or the handoff's Decisions.

**In simply:** `/simply:brainstorm` asks at most one message; a `/simply:tdd` report's Escalation (Unresolved, Tried, Question); `/simply:review` escalates after loop 2 and sends product questions to the user; `/simply:goodnight` asks once for all missing `next` fields.
