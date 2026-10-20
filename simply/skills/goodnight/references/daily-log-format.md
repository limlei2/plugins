# Daily Log Format

The contract between `/simply:goodnight` (writer) and `/simply:goodmorning` (reader). Change it here only, and keep both skills compatible.

## Location

`<git root>/.simply/daily/YYYY-MM-DD.md`, one file per local calendar day. A second goodnight on the same day rewrites that file, merging old and new items. It never creates a second file.

## Rules

- Headings are exactly the ones below, in this order, all present. A section with nothing in it holds the single line `- none`.
- Items are one line each. Fields inside an item are separated by ` | ` and written `key: value`. Keys are lowercase and fixed per section.
- Branches, SHAs, PR numbers, and paths are written in backticks exactly as git and `gh` print them, so the reader can pass them straight to commands.
- Nothing secret: no tokens, passwords, or customer data.

## Header

```
# Daily log YYYY-MM-DD

- project: <git root folder name>
- updated: <ISO 8601 local time with offset, e.g. 2026-10-20T18:42:00-07:00>
- head: `<current branch>` @ `<short sha>`
- branches: `<branch>` @ `<short sha>`, ... (every branch named in In progress or Blocked)
```

`updated` is the time of the latest goodnight run. The reader uses it as the "since" point for `git log --since` and `gh` queries. `branches` records each tip so the reader can tell which branches moved.

## Sections

| Heading | Item shape | Meaning |
|---|---|---|
| `## Summary` | 1 to 3 plain sentences | What the day was about and where it ended. |
| `## Done` | `- <what> \| verified: <how> \| ref: <sha or #PR>` | Finished work. `verified` names the evidence: test command and result, CI run, manual check. `unverified` is allowed and must be said. |
| `## In progress` | `- <what> \| branch: \`<b>\` \| pr: <#n or none> \| next: <exact next step>` | Started, not finished. `next` is one concrete action a fresh session can run without asking: a command, a file and function, a failing test name. |
| `## Blocked` | `- <what> \| blocker: <what is in the way> \| unblocks: <person, event, or action>` | Cannot proceed without something outside this session. |
| `## Decisions` | `- <decision> \| why: <reason> \| rejected: <alternatives or none>` | Choices made today that a later session must not relitigate. |
| `## Open questions` | `- <question> \| context: <why it matters>` | Questions only the user can answer. |
| `## Tomorrow` | `1. <task> \| why: <reason>` | Ranked, highest first. Numbered list, not bullets. |
| `## Skill notes` | `- <skill name> \| issue: <what went wrong> \| suggest: <proposed change>` | Where a skill misfired, missed a step, or the user corrected the same thing more than once. Suggestions only, never applied. |
| `## Handoffs` | `- \`<path>\`` | Files under `.simply/handoffs/` created today, path relative to git root. |
| `## Durable facts saved` | `- <file> \| <one-line fact>` | What goodnight wrote into CLAUDE.md or README this run, so the log shows it without duplicating it. |

## Example

```markdown
# Daily log 2026-10-20

- project: billing-api
- updated: 2026-10-20T18:42:00-07:00
- head: `feat/retry-webhooks` @ `a1b2c3d`
- branches: `feat/retry-webhooks` @ `a1b2c3d`, `fix/tz-invoices` @ `9f8e7d6`

## Summary
Shipped the invoice rounding fix and got webhook retries half done. Retry backoff works; dead-letter handling is not started.

## Done
- Fix cent rounding on multi-currency invoices | verified: `npm test -- invoices` 42 passed, CI green | ref: #311
- Review of Sam's rate-limit PR | verified: approved with 2 comments | ref: #308

## In progress
- Webhook retries with backoff | branch: `feat/retry-webhooks` | pr: none | next: add dead-letter write in `src/webhooks/retry.ts` `onGiveUp()`, then run `npm test -- webhooks`
- Invoice timezone bug | branch: `fix/tz-invoices` | pr: #314 | next: make `test/invoices/tz.test.ts` "renders in account tz" pass

## Blocked
- Staging deploy of retries | blocker: staging DB migration lock held | unblocks: Priya releases the lock

## Decisions
- Exponential backoff capped at 6 tries | why: provider times out after 1 hour | rejected: fixed 5-minute interval

## Open questions
- Should dead-lettered webhooks alert on-call or only log? | context: decides whether `onGiveUp()` needs the pager client

## Tomorrow
1. Finish dead-letter handling on `feat/retry-webhooks` | why: unblocks the PR
2. Fix tz test on #314 | why: reviewer waiting
3. Ping Priya about the staging lock | why: blocks deploy

## Skill notes
- simply:give | issue: did not include the failing test name in the handoff | suggest: add a "how to reproduce" field

## Handoffs
- `.simply/handoffs/2026-10-20-retry-webhooks.md`

## Durable facts saved
- CLAUDE.md | Run `npm run db:reset` before integration tests; they share one DB
```
