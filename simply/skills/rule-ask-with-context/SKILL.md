---
name: rule-ask-with-context
description: "Apply when a skill must ask the user or escalate. Interviews send rounds of up to 4 multiple-choice questions with your pick first; escalations say what is unresolved, what was tried, and one question, batched in one message."
disable-model-invocation: true
---

# Ask With Context

When you must stop for the user, the message must be answerable without scrolling back. There are two kinds. An **interview** (designing or planning) sends rounds of multiple-choice questions the user can flip through and answer in one go: each question carries what you found and the options, your pick first. The next round follows from the answers. An **escalation** (work is stuck) names what is unresolved and what you tried, batches every question into one message, and waits.

**Why:** A vague "how should I proceed?" costs the user a round of re-reading the session. Questions sent one per message cost a round trip each; a wall of prose questions gets skimmed. Cards with concrete options get answered quickly and accurately.

**Do:**
- Ask only what `rule-decide-and-report` cannot decide: a product or preference choice, a wait point, an irreversible action, or a hit limit.
- Interview round: one `AskUserQuestion` call with 1-4 questions (its maximum). Each question: `question` is one sentence, plus `(found: <file>:<line> <what it says>)` when the code bears on it; `header` is a 12-character-max label; 2-4 `options`, each a concrete answer with a one-line `description` of what it means; your pick is the first option, its label ending ` (Recommended)`. `multiSelect: true` only when the answers really combine. The user's own words go through the tool's built-in Other box, so never add an "Other" option.
- Batch only questions that don't depend on each other: if one answer changes another question's options, ask it in the next round.
- Broad branches (who, why, success, what it must not do) get cards too: offer your 2-4 best concrete guesses, and read an Other answer as the user's intent in their own words. Play back what you understood as text above the next round's cards.
- Never ask what the code answers. Stop when the user types **skip** in any Other box, and decide the rest.
- No `AskUserQuestion` tool in this session: send the same round as one message, numbered, each question with lettered options and your pick marked `(recommended)`, so "1a 2b 3a" is a full reply.
- Escalation: **Unresolved** (the exact criterion, check, or error text), **Tried** (one line per attempt), **Question** (one, answerable in a word or a choice). Collect all questions first, send them in one message, and wait.
- On every question, offer the answer you'd pick, so accepting the defaults is a valid reply.

**Not this:**
- "What do you want me to do?"
- One question per message when the next question doesn't depend on its answer.
- Open-ended prose questions with no options.
- An escalation split across three messages, or one with no error text or attempts listed.
- Asking a question already answered in the brief's Constraints or the handoff's Decisions.

**In simply:** `/simply:brainstorm` and `/simply:plan` interview in rounds of up to 4 cards, and brainstorm sends its builder check's leftovers the same way; a `/simply:tdd` report's Escalation (Unresolved, Tried, Question); `/simply:review` escalates after loop 2 and sends product questions to the user; `/simply:goodnight` asks once for all missing `next` fields.
