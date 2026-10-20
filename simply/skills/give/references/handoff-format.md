# Handoff Format

The contract between `/simply:give` (writer) and `/simply:take` (reader). Both follow this file exactly. Other skills read only the `Status:` line.

## Location

`<git root>/.simply/handoffs/<YYYY-MM-DD-HHMM>-<slug>.md`. The timestamp is local time when written, so filenames sort oldest to newest. The slug is the first word of `/give`'s argument if it matches `^[a-z0-9-]{3,40}$`, else 2–4 lowercase hyphenated words naming the task.

## Rules

- Line 3 is the status line, exactly one of:
  - `Status: open`
  - `Status: taken by <git config user.name> at <YYYY-MM-DD HH:MM>`
- Every heading below appears, in this order, even when empty. Write `None.` rather than deleting a section.
- Write for a reader with zero conversation history: full paths, exact commands, exact error text. No "as discussed", no "the bug", no pronouns pointing at the chat.
- Facts only. If something is a guess, say so in the line.

## Fields

| Heading | What goes in it |
|---|---|
| `# Handoff: <title>` | One-line task name. |
| `Status:` | See Rules. `/give` writes `open`; `/take` changes it. |
| `Created:` | `<YYYY-MM-DD HH:MM> by <git config user.name>`. |
| `## Goal` | The outcome when the task is done, and why it matters. 1-3 sentences. |
| `## Done so far` | One bullet per finished piece, each ending with `Verified: <command run or check made, and its result>`. Unverified work goes under In progress. |
| `## In progress` | What is half-done and in what state (compiles? tests red?). |
| `## Exact next step` | The single next action, concrete enough to start without thinking: file, function, command. |
| `## Decisions and why` | Choices made that the receiver must not silently reverse, each with its reason. |
| `## Dead ends` | Approaches already tried that failed, each with why, so they are not retried. |
| `## Files involved` | One bullet per file: ``- `<repo-relative path>`: <its role>``. `/take`'s verifier reads the backticked path, so it is required. |
| `## Code state` | `Branch:`, `Commit:` (full SHA of HEAD), `Stash:` (full stash commit SHA or `none`), `Dirty files:` (the `git status --porcelain` lines at handoff, or `none`). |
| `## How to verify` | Commands that prove the whole task works when finished, and what passing looks like. |
| `## Open questions` | Unresolved questions, and who can answer each (user, another agent, docs). |
| `## Note from giver` | Free text passed to `/give`, or `None.` |

## Example

```markdown
# Handoff: Retry failed webhook deliveries

Status: open
Created: 2026-10-20 16:42 by limlei2

## Goal
Failed webhook deliveries are retried with exponential backoff up to 5 times, so customers stop missing events when their endpoint blips.

## Done so far
- Added `attempts` and `next_attempt_at` columns via migration `db/migrations/0042_webhook_retry.sql`. Verified: `make migrate && psql -c '\d webhook_deliveries'` shows both columns.
- `backoff(attempt)` in `src/webhooks/retry.ts` returns 30s * 2^attempt capped at 1h. Verified: `npm test -- retry.test.ts` 6/6 pass.

## In progress
`src/webhooks/worker.ts` picks due rows but does not yet increment `attempts` on failure. Compiles; `worker.test.ts` has 1 failing test ("marks dead after 5 attempts") which is expected until this is done.

## Exact next step
In `src/webhooks/worker.ts`, inside `deliver()`'s catch block, update the row: `attempts = attempts + 1`, `next_attempt_at = now() + backoff(attempts)`, and set `status = 'dead'` when attempts reaches 5. Then run `npm test -- worker.test.ts`.

## Decisions and why
- Retry state lives on `webhook_deliveries`, not a separate queue table: one row per delivery keeps the admin UI query unchanged.
- Cap at 5 attempts (~31 min total): product asked for "under an hour".

## Dead ends
- BullMQ delayed jobs: rejected, adds Redis to a service that has none; ops said no.
- `setTimeout` in-process retries: lost on deploy restart, reproduced in staging.

## Files involved
- `db/migrations/0042_webhook_retry.sql`: new columns.
- `src/webhooks/retry.ts`: backoff math.
- `src/webhooks/worker.ts`: delivery loop, being edited.
- `test/webhooks/worker.test.ts`: the failing test that defines done.

## Code state
Branch: feat/webhook-retry
Commit: 3f9c2a1e8b7d6c5f4a3b2c1d0e9f8a7b6c5d4e3f
Stash: 9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b
Dirty files:
 M src/webhooks/worker.ts
?? test/webhooks/worker.test.ts

## How to verify
`npm test` all green, then `npm run e2e -- webhooks` shows "retried 3x then delivered" for the flaky-endpoint fixture.

## Open questions
- Should dead deliveries alert anyone? Ask the user.

## Note from giver
None.
```
