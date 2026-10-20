---
name: rule-db
description: "Rules for database schema design, migrations, and queries (Postgres plus Prisma, Drizzle, Knex, SQLAlchemy or raw SQL). Use whenever you add or change a table, column, index, constraint, or enum; write, edit, or run a migration; write or change a query, ORM model, repository, or seed; backfill or bulk-update data; or chase a slow page, slow endpoint, timeout, or lock that may come from a query, even if the user never says 'database'. For server logic use rule-backend; for endpoint shapes use rule-api-design."
paths:
  - "**/migrations/**"
  - "**/migrate/**"
  - "**/schema.prisma"
  - "**/prisma/**"
  - "**/drizzle/**"
  - "**/alembic/**"
  - "**/*.sql"
  - "**/db/**"
  - "**/models/**"
  - "**/repositories/**"
  - "**/seeds/**"
  - "**/knexfile.*"
---

# DB Rules

Rules for schema, migrations, and queries that change a decision. If the project's `CLAUDE.md` says otherwise, the project wins. Server logic is in `${CLAUDE_PLUGIN_ROOT}/skills/rule-backend/SKILL.md`; request/response shapes are in `${CLAUDE_PLUGIN_ROOT}/skills/rule-api-design/SKILL.md`.

"Large table" below means over 100,000 rows or over 1 GB; when you can't tell, check (`SELECT reltuples FROM pg_class WHERE relname = '<table>'` in Postgres) or treat it as large.

## Migrations

- Never edit a migration that has run anywhere shared (main branch, CI database, staging, production); add a new migration — why: other databases already ran the old text, so an edit makes them drift silently.
- Generate migrations with the project's tool (`prisma migrate dev`, `drizzle-kit generate`, `knex migrate:make`, `alembic revision --autogenerate`), then read the generated SQL before committing — why: generators turn renames into drop-and-add and lose data.
- Every migration has a working down/rollback, or a comment at the top stating why it can't (`-- irreversible: drops data in <column>`) — why: an unexplained one-way migration blocks rollback during an incident.
- One concern per migration: one table change, one index, or one backfill — why: a failure mid-file leaves a half-applied state that is hard to roll back.
- Rename or drop a column/table in three deploys: expand (add the new one, write both), migrate (backfill, switch reads), contract (drop the old) — why: during a rolling deploy the old code still reads the old column, and a same-deploy drop breaks it.
- Never drop or rename a column that code in the same deploy, or the deploy before it, still reads — why: rollback brings that code back.
- Add `NOT NULL` to a large table in steps: add nullable, backfill in batches of 1,000–10,000 rows with a commit per batch, then add the constraint (Postgres: `ADD CONSTRAINT ... CHECK (col IS NOT NULL) NOT VALID`, `VALIDATE CONSTRAINT`, then `SET NOT NULL`) — why: a single-statement backfill locks the table and bloats the WAL.
- Adding a column with a volatile default (`now()`, `gen_random_uuid()`) on a large table: add without default, backfill, then set the default — why: Postgres rewrites the whole table under an exclusive lock for volatile defaults (constants are fine on Postgres 11+).
- Index a large table with `CREATE INDEX CONCURRENTLY` (Postgres), in its own migration with the tool's transaction turned off (Prisma: hand-edit the SQL file; Knex: `exports.config = { transaction: false }`; Alembic: `with op.get_context().autocommit_block()`) — why: plain `CREATE INDEX` blocks writes for the whole build, and `CONCURRENTLY` fails inside a transaction.
- After a failed `CONCURRENTLY` build, drop the `INVALID` index before retrying — why: it stays behind, costs writes, and is never used.
- Set `lock_timeout` (e.g. `SET lock_timeout = '5s'`) at the top of any `ALTER TABLE` on a busy table — why: an ALTER waiting for a lock queues every query behind it and takes the app down.
- Adding a foreign key to a large table: `ADD CONSTRAINT ... NOT VALID`, then `VALIDATE CONSTRAINT` in a separate migration — why: validation then takes a weak lock instead of blocking writes.
- Schema migrations never contain data backfills on large tables; run those as a separate batched script or job — why: a migration runner usually holds one transaction and a deploy timeout.

## Schema

- Every table has a primary key; default to `bigint` identity or UUID (v7 when available) and follow what the project already uses — why: without a key, replication, ORMs, and dedup all break.
- Every foreign key has an explicit `ON DELETE` (`RESTRICT` by default, `CASCADE` only for rows owned by the parent, `SET NULL` for optional links) — why: the default `NO ACTION` hides the decision, and an accidental `CASCADE` deletes far more than intended.
- Index every foreign key column (Postgres does not do it for you) — why: deleting a parent row otherwise scans the whole child table.
- Every table gets `created_at` and `updated_at` as `timestamptz NOT NULL DEFAULT now()`, stored in UTC — why: `timestamp` without time zone silently shifts when server or client zones differ.
- Keep `updated_at` current in one place (an ORM hook such as Prisma `@updatedAt`, or a DB trigger), not in each query — why: hand-set timestamps drift as soon as one write path forgets.
- Money is integer minor units (`bigint` cents) plus a currency column, or `numeric(19,4)`; never `float`, `real`, or `double precision` — why: binary floats can't represent 0.10 and sums drift.
- Use a DB enum or `CHECK (col IN (...))` for a small, fixed set that changes only with code (status, role); use a lookup table when values are added at runtime, carry extra fields, or exceed ~20 — why: removing a Postgres enum value needs a type rebuild, and a lookup table needs a join.
- Enforce invariants with constraints in the database: `UNIQUE` (including partial `UNIQUE ... WHERE deleted_at IS NULL`), `NOT NULL`, `CHECK`, foreign keys — why: a check in code alone loses to two concurrent requests.
- Case-insensitive uniqueness (emails, usernames) uses a unique index on `lower(col)` or the `citext` type — why: `UNIQUE(email)` allows `A@x.com` and `a@x.com` together.
- Columns are `NOT NULL` unless null has a distinct meaning you can name — why: nullable columns turn every read into a three-way branch.
- Text: `text` with a `CHECK (char_length(col) <= n)` when a limit matters, not `varchar(n)` guesses — why: in Postgres they perform the same, and changing a CHECK is cheaper than resizing a type.
- Soft delete (`deleted_at timestamptz`) only when the product needs restore or audit; then every unique constraint and hot index is partial on `deleted_at IS NULL` — why: otherwise deleted rows block re-creation and bloat indexes.

## Queries

- No N+1: load related rows with a join or one batched `WHERE id = ANY($1)` / `IN (...)` query (Prisma `include`, Drizzle `with`, SQLAlchemy `selectinload`) — why: a query per row turns one page load into hundreds of round trips.
- On hot paths, select only the columns you use (Prisma `select`, SQLAlchemy `load_only`), never `SELECT *` — why: wide rows waste I/O and block index-only scans.
- Every query on a large table filters or joins on an indexed column; add the index in the same change if it's missing — why: a sequential scan that is fast in dev times out in production.
- Composite index column order: equality columns first, then the range or sort column — why: an index on `(created_at, user_id)` can't serve `WHERE user_id = $1 ORDER BY created_at`.
- Parameterized queries only; never build SQL with string concatenation or template literals (Prisma `$queryRawUnsafe`, Knex `raw` with interpolation, SQLAlchemy `text()` with f-strings) — why: SQL injection.
- Dynamic identifiers (sort column, table name) come from a hard-coded allowlist, never from input — why: identifiers can't be parameterized.
- Paginate with keyset/cursor (`WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT n`) once a list can pass ~1,000 rows; `OFFSET` only below that — why: `OFFSET` reads and discards every skipped row, and rows shift between pages.
- Every list query has a `LIMIT` and a deterministic `ORDER BY` ending in a unique column — why: unbounded queries grow with the data, and ties reorder between pages.
- Run `EXPLAIN (ANALYZE, BUFFERS)` on every new or changed query that touches a large table, against realistic data volume, and fix any `Seq Scan` on that table — why: the planner picks different plans on 100 rows and 10 million rows.
- Use `EXISTS` not `COUNT(*) > 0` to test presence — why: count reads every match, exists stops at the first.
- Upserts use `INSERT ... ON CONFLICT` (Prisma `upsert`, Drizzle `onConflictDoUpdate`), not select-then-insert — why: select-then-insert races and creates duplicates or unique violations.
- Bulk writes go in one multi-row statement or batches of 1,000–10,000 rows, not a loop of single-row inserts — why: per-row round trips dominate the runtime.

## Transactions

- Keep transactions short: no HTTP calls, queue publishes, emails, file I/O, or user waits inside one — why: locks are held for the full network latency, and a timeout leaves rows locked.
- Side effects that must follow a commit (emails, events) run after commit or through an outbox table written in the same transaction — why: a rollback can't unsend an email.
- Lock rows in a consistent order (e.g. ascending primary key) whenever a transaction locks more than one row — why: opposite orders deadlock.
- Use `SELECT ... FOR UPDATE` (or an atomic `UPDATE ... SET n = n - 1 WHERE n > 0`) for read-modify-write on shared rows — why: read-then-write in code loses concurrent updates.
- Retry only on serialization failure (`40001`) and deadlock (`40P01`), 3 attempts max with jittered backoff, re-running the whole transaction — why: retrying other errors repeats bugs and duplicates side effects.
- Set `statement_timeout` (e.g. 30s for web requests) and `idle_in_transaction_session_timeout` on the app's connection — why: one runaway query or abandoned transaction holds locks and connections indefinitely.

## Data safety

- Any `DELETE` or `UPDATE` without a narrow `WHERE`, any `TRUNCATE`, `DROP TABLE`, or `DROP COLUMN`, and any bulk data change on a shared database needs explicit user approval in chat before it runs — why: it can't be undone from the code.
- With that request, state the row count it will touch (run the same `WHERE` as a `SELECT count(*)` first) and the rollback: a backup or snapshot name, or a copy table (`CREATE TABLE <t>_backup_<yyyymmdd> AS SELECT ...`) — why: the user approves a number, not a guess.
- Run destructive one-off statements inside a transaction, check the affected row count, then `COMMIT`; `ROLLBACK` if it differs from the count you stated — why: catches a wrong `WHERE` before it lands.
- Seeds never run against production: the seed script checks the environment or database URL and exits non-zero on a production match — why: seeds truncate or overwrite real data.
- Never point local tools, tests, or migrations-in-development at a production `DATABASE_URL` — why: `prisma migrate dev` and `migrate reset` drop data.
- Never put real customer data in seeds, fixtures, or test snapshots — why: it leaks through the repo.

## Done checklist

/build Step 5 ("Data change: query the result, don't trust the migration's exit code") checks:

- [ ] Migration runs up on a fresh database and on a copy with existing data.
- [ ] Migration runs down, then up again, cleanly; or the file states why it is irreversible.
- [ ] Queried the result: the schema (`\d <table>` or the ORM's introspection) shows the expected columns, types, constraints, and indexes; backfilled rows checked with a `SELECT count(*)` where the new invariant fails, expecting 0.
- [ ] Indexes built with `CONCURRENTLY` are valid (`SELECT indexrelid::regclass FROM pg_index WHERE NOT indisvalid` returns none).
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` output recorded for every new or changed query on a large table, with no `Seq Scan` on it.
- [ ] No N+1: query count for the changed endpoint or job checked in the query log, not assumed.
- [ ] Every destructive data change has the user's approval, the row count, and the rollback note in the PR.

## Not covered

- Service structure, error handling, jobs, and caching: `rule-backend`.
- Endpoint design, pagination response shape, and error formats: `rule-api-design`.
- Database operations: provisioning, replication, backups setup, connection-pool sizing, and engine upgrades.
- Analytics and warehouse modeling (star schemas, dbt).
- Engine-specific tuning beyond the short Postgres notes here.
