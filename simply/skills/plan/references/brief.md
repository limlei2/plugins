# The brief

A brief is the contract for one task. `/simply:plan` writes one per task; `/simply:tdd` executes them, directly or as a `/simply:subagents` worker. Plan with a strong model, execute with a cheap one: the worker never rewrites the brief.

## Format

```markdown
## Goal
<one sentence: the outcome, not the steps>

## Criteria
- [ ] <checkable statement; together these are the definition of done>

## Files
- Work in: <paths or globs>
- Do not touch: <paths or globs>

## Checks
- `<exact command>`  <!-- tests, lint, typecheck; each must pass -->

## Constraints
- <decision already made, or what is out of scope>

## Context
<the user's original request, verbatim. Reference only: Criteria win when they disagree.>
```

## Rules for the writer

- Every criterion is checkable against the real artifact: a command's output, a file's content, a behavior you can trigger. "Clean code" is not a criterion.
- Checks are exact commands that run from the repo root. If the repo has none, say `none` and make the criteria carry the verification.
- Files lists both sides. In subagents mode, two briefs never share a "Work in" path (`check_briefs.py --parallel` enforces it).
- Constraints records every decision the planner made so the worker doesn't remake it.

## Example

```markdown
## Goal
`GET /api/users` supports cursor pagination.

## Criteria
- [ ] `?limit=N` returns at most N users (default 50, max 200).
- [ ] Response includes `nextCursor`, null on the last page.
- [ ] `?cursor=<nextCursor>` returns the following page with no overlap or gap.
- [ ] Invalid cursor returns 400 with `{"error": "invalid cursor"}`.
- [ ] A test covers each of the four behaviors above.

## Files
- Work in: `src/routes/users.ts`, `src/routes/users.test.ts`
- Do not touch: `src/db/schema.ts`, any other route

## Checks
- `npm test -- users`
- `npm run lint`
- `npx tsc --noEmit`

## Constraints
- Cursor is the base64 of the last user's `id`; no offset pagination.
- No new dependencies.
- Client-side changes are out of scope.

## Context
"the users list is way too slow once we have thousands of rows, add pagination to the users endpoint"
```
