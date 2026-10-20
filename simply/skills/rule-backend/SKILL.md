---
name: rule-backend
description: "Rules for server-side code: input validation at the boundary, pure business logic, timeouts and retries on external calls, idempotent jobs and webhooks, secrets, structured logging, error handling, and startup config. Use whenever writing, editing, or reviewing server, service, job, worker, queue, webhook, cron, or middleware code, or any code that calls a database, HTTP API, queue, or third-party SDK, even when the user does not mention backend rules. For endpoint shapes and status codes use rule-api-design; for schema, migrations, and queries use rule-db."
paths:
  - "**/server/**"
  - "**/services/**"
  - "**/jobs/**"
  - "**/workers/**"
  - "**/queues/**"
  - "**/lib/**"
  - "**/middleware/**"
  - "**/webhooks/**"
  - "**/cron/**"
---

# Backend Rules

Decisions for server-side code. The project's `CLAUDE.md` conventions win on any conflict.

Auto-load covers only the folders in `paths:`. Globs cannot say "every `src/**/*.ts` that is not UI", so server code in other folders (for example `src/index.ts`, `app/`) does not trigger this skill; `/simply:build` Step 4 reads it explicitly for any server change.

## Boundary discipline

- Validate every untrusted input (request body, query, headers, webhook payload, queue message, env, file contents) with a schema at the point it enters — why: one parse turns unknown data into a known type; checks scattered deeper miss paths.
- Use the project's validator; in Node/TS with none, use `zod` and derive the type from the schema (`z.infer`) — why: a hand-written type next to a schema drifts from it.
- After the boundary, trust the parsed type: no re-validation, no `any`/`unknown` casts, no defensive null checks for fields the schema requires — why: re-checks hide which layer owns validation and add dead branches.
- Reject unknown fields on writes (`.strict()` or equivalent) — why: silently dropped fields make client typos look like successes.
- Webhooks: verify the signature on the raw body before parsing, with a constant-time compare — why: parsing first lets forged payloads reach logic; `===` leaks timing.

## Structure

- Business logic lives in pure functions that take plain data and return plain data or a result; no DB, HTTP, clock, or random inside — why: pure logic is unit-testable without mocks and reusable from jobs and handlers.
- I/O (DB, HTTP, queue, filesystem, `Date.now()`, randomness) happens in the handler or service shell, which calls the pure core — why: keeps side effects in one visible place per flow.
- Handlers stay thin: parse, call service, map result to response — why: logic in handlers cannot be reused by jobs or tested without HTTP.
- Pass dependencies (clients, clock) as arguments or constructor params, not module-level singletons imported deep inside logic — why: tests can swap them without module mocking.

## External calls

- Every outbound call (HTTP, DB, cache, queue, SDK) has a timeout; default 10s for HTTP/SDK calls, 5s for cache — why: a call with no timeout hangs the request and holds a connection forever.
- In Node use `AbortSignal.timeout(10_000)` on `fetch`; set the SDK's own timeout option when it has one — why: `fetch` has no default timeout.
- Retry only idempotent operations (GET, PUT, DELETE, or POST with an idempotency key): 3 attempts max, exponential backoff from 200ms with full jitter, cap 5s — why: retrying a non-idempotent POST double-charges or double-creates.
- Retry only on network errors, 408, 429, 502, 503, 504; honor `Retry-After` — why: retrying 4xx validation errors never succeeds and wastes quota.
- Total time across retries stays under the caller's own timeout — why: retries that outlive the request do work nobody waits for.
- Run independent calls concurrently (`Promise.all`), dependent ones in sequence — why: serial independent awaits add their latencies together.

## Idempotency

- Every job, webhook handler, and queue consumer is safe to run twice with the same input — why: every queue and webhook sender delivers at least once.
- Dedupe with an idempotency key (the provider's event id, or a key the producer sets) stored with a unique constraint, checked in the same transaction as the write — why: a check-then-write outside a transaction races under concurrent delivery.
- Keep processed keys at least 24h, or as long as the sender's retry window if longer — why: shorter retention lets late retries through.
- Prefer upserts and "set state to X" over "increment" or "append" in retried code — why: set-to-value is naturally idempotent; increments double.
- Side effects that cannot be deduped (email, payment) run after the dedupe write commits, and pass the key to the provider — why: a crash between effect and record repeats the effect.

## Background jobs

- Jobs take ids, not full objects, and reload current state when they run — why: payloads go stale between enqueue and run.
- Each job has a max runtime (default 5 min) and a max attempts count (default 5), then goes to a dead-letter queue or failed state with the error — why: unbounded retries hide permanent failures and burn resources.
- Batch jobs process in chunks (default 500 rows) and checkpoint progress — why: a crash restarts from the checkpoint, not from zero.
- Scheduled jobs take a lock (DB advisory lock or the queue's unique-job option) so two instances don't run the same schedule — why: horizontal scaling runs every cron once per instance.

## Secrets and config

- Secrets come only from env vars or the platform's secret manager; never in code, fixtures, or committed `.env` files — why: committed secrets leak through git history forever.
- Load and validate all config once at startup with a schema; required values missing means the process exits non-zero with the variable name — why: failing at boot beats failing on the first request that needs the value.
- Every optional setting has a default in the config schema, not at the use site — why: defaults scattered in code disagree with each other.
- Code reads the parsed config object, never `process.env` directly outside the config module — why: one module is the only place to see every setting.
- Never log, return, or put in error messages a secret, token, password, or full connection string; redact by key name in the logger — why: logs are shipped to third parties and kept for months.

## Logging

- Use the project's structured logger (JSON in production); in Node with none, use `pino` — why: string logs cannot be queried by field.
- Every log line in a request or job carries `requestId` (or `jobId`), taken from the incoming `x-request-id` header or generated, and passed down via child logger or async context — why: without it you cannot follow one request across lines and services.
- Forward the request id on outbound calls as `x-request-id` — why: traces stop at service boundaries otherwise.
- No PII in logs (email, name, phone, address, IP, tokens, request bodies); log ids instead — why: PII in logs is a compliance breach and cannot be deleted per user.
- Levels: `error` = needs a human, `warn` = degraded but handled, `info` = one line per request/job outcome, `debug` = off in production — why: everything at `info` makes alerts useless.

## Errors

- Never swallow an error: every `catch` rethrows, returns a typed failure, or logs at `error` and changes the outcome — why: an empty catch turns a failure into silent wrong data.
- One application error class (or result type) with a stable `code` string, an HTTP-agnostic `message`, and optional `details` — why: one shape lets one mapper handle every error.
- Map application errors to HTTP responses in exactly one place (error middleware or a single wrapper) per rule-api-design — why: per-handler mapping drifts into inconsistent status codes.
- Unknown errors map to 500 with a generic message; the stack and cause go to the log only — why: stacks in responses leak internals.
- Wrap errors with context (`new AppError(..., { cause })`) instead of replacing them — why: replacing loses the original stack.
- Handle `unhandledRejection` and `uncaughtException` by logging and exiting non-zero; let the supervisor restart — why: continuing after an unknown failure runs on corrupt state.

## Data access

- No query inside a loop over rows (N+1); batch by ids or join. Query, schema, index, and migration rules live in `rule-db` — why: N+1 turns one request into hundreds of round trips.
- Multi-step writes that must succeed together run in one transaction, and no external HTTP call happens inside it — why: an HTTP call inside a transaction holds locks for the call's duration.

## Shutdown

- On `SIGTERM`, stop accepting work, finish in-flight requests and jobs within 25s, close pools, exit — why: orchestrators kill at 30s and in-flight work is lost.

## Done checklist

`/simply:build` Step 5 checks each line against the diff and a real run:

- [ ] Every new input path parses with a schema at the boundary; an invalid input returns the validation error, shown by a real call.
- [ ] Every new outbound call has a timeout; retries only on idempotent ops, bounded.
- [ ] Every new job, webhook, or consumer dedupes by idempotency key; running it twice with the same input changes state once (shown by running it twice).
- [ ] No secret or PII in code, logs, or responses (`grep` the diff for keys, tokens, emails in log calls).
- [ ] New log lines are structured and carry the request or job id.
- [ ] No empty or log-and-continue `catch`; new errors use the project's error class and the central mapper.
- [ ] New config is in the startup schema with a default or a required check; booting without a required value fails with its name.
- [ ] No query in a loop (see `rule-db` checklist).
- [ ] Business logic added is in pure functions with a unit test.

## Not covered

- Endpoint paths, status codes, error body, pagination, versioning: `rule-api-design`.
- Schema, migrations, indexes, query shape: `rule-db`.
- UI code: `rule-frontend`.
- Auth design (session vs token, password storage), infra, deploy, and observability tooling choice.
