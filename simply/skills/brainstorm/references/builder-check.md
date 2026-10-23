# Builder check

Brainstorm Step 6 spawns one fresh agent to read `design.md` as the person who must plan from it. It never sees the interview, so it finds what the design assumes but doesn't say.

## Agent values

| `subagent_type` | `model` | `effort` | `isolation` |
| --- | --- | --- | --- |
| `general-purpose` | `sonnet` | `medium` | omit (it only reads) |

## Prompt

Fill in the two absolute paths, then send it verbatim:

```
You are a senior software engineer. You've been handed a design document and asked to plan the work it describes. You cannot talk to the person who wrote it.

Read <abs path to design.md>. You may read any file in <abs repo root> to understand the code it refers to. Do not edit anything, and do not spawn agents.

Report only the questions you'd still need answered before you could plan this well: places where you'd have to guess and a wrong guess would change what gets built. For each, one line: the question, then " — because " and why the answer changes the plan. Rank them, most important first. 7 max.

Skip anything the document leaves to the builder, anything the code answers, anything you could reasonably decide yourself, and wording nitpicks.

If nothing important is left, reply exactly: nothing important left
```

## Sorting the reply

Every question goes in exactly one pile:

| Pile | Test | What you do |
| --- | --- | --- |
| Answered | The interview or the code already answers it | Write the answer into `design.md` as a Decision tagged `(you)` or `(code: <file>:<line>)` |
| Minor | A sensible builder could settle it without changing what gets built | Decide it, add a Decision tagged `(my call)` |
| Theirs | Only the user can answer it, and the answer changes what gets built | Ask it in the one batched round |

Ask the Theirs pile as interview cards (format in `rule-ask-with-context`), most important first, 4 per `AskUserQuestion` call: up to 7 questions is 2 calls, the second sent right after the first is answered. Your pick is each card's first option, so accepting every default is a full reply. This is one round of questions, not a new interview: a follow-up an answer raises goes in Open questions.
