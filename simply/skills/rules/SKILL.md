---
name: rules
description: "Index of every rule-* skill in simply: working rules for how much to build, how to verify, how to debug, and how to run agents. Use it whenever planning a change, debugging a failure, deciding whether something is done, reviewing a diff, splitting work across agents, retrying after a failed fix, or deciding whether to ask the user — even if the user doesn't mention rules. Also use it when the user names a rule (\"verify the real thing\", \"question the assumption\", \"smallest change\")."
---

# Rules

Every rule is its own skill at `${CLAUDE_PLUGIN_ROOT}/skills/rule-<name>/SKILL.md`. This page says when each one applies. When a situation below matches, read that rule's file in full before acting, apply it, and name it in your reply with the decision it changed (for example: "rule-question-the-assumption: stopped after the second failed fix and tested the cache assumption"). Naming a rule without a changed decision means it wasn't applied.

## Verifying and debugging

| Rule | Apply when |
| --- | --- |
| `rule-verify-the-real-thing` | About to say something works, is done, or is fixed |
| `rule-fix-at-the-source` | A check fails or a bug is reported |
| `rule-question-the-assumption` | Two fixes built on the same assumption have failed |
| `rule-test-what-users-see` | Writing, changing, or keeping a test |
| `rule-small-green-steps` | Work has more than one step, or a run of similar edits |
| `rule-criteria-before-code` | Starting any implementation |
| `rule-bounded-loops` | Retrying, re-reviewing, or re-fixing anything |

## Code and design

| Rule | Apply when |
| --- | --- |
| `rule-smallest-change` | Choosing how big a change to make, or tempted to add a layer |
| `rule-delete-first` | Adding to code that has dead or redundant parts |
| `rule-easy-to-follow` | Code is hard to trace, or you're adding a wrapper |
| `rule-validate-at-the-edges` | Placing validation or error handling |
| `rule-design-it-in` | A new requirement doesn't fit the current design |
| `rule-script-repeated-work` | Doing repeated or bulk work by hand |
| `rule-enforce-dont-remind` | Correcting the same mistake a second time |

## Agents and workflow

| Rule | Apply when |
| --- | --- |
| `rule-no-shared-writes` | Parallel agents might write the same file, branch, or port |
| `rule-keep-context-lean` | About to read large outputs or many files in the main thread |
| `rule-decide-and-report` | About to ask "should I?" about reversible work |
| `rule-ask-with-context` | A skill must ask the user or escalate |
| `rule-state-lives-in-files` | The next session or agent will need this information |
| `rule-spend-review-where-mistakes-are-expensive` | Deciding how much checking or which model a task gets |
| `rule-plan-strong-execute-cheap` | Writing a brief for, or acting as, a worker agent |

## When two rules pull apart

- `rule-decide-and-report` covers reversible work only. A skill's explicit wait point (`/plan`'s tdd-or-subagents question, prompt-mode pauses, `/review` before opening PRs in prompt mode, `/goodmorning`'s final question) and anything irreversible still wait; ask per `rule-ask-with-context`.
- `rule-smallest-change` never cuts verification: `rule-verify-the-real-thing` still applies to the smallest change.
- `rule-bounded-loops` decides when to stop retrying; `rule-question-the-assumption` decides what to do instead.
