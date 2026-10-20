---
name: rule-api-design
description: "Rules for HTTP API design: resource naming, status codes, one error shape, validation errors, cursor pagination, breaking changes and versioning, timestamps, ids, idempotency keys, PATCH vs PUT, and what errors may reveal. Use whenever adding, changing, or reviewing an endpoint, route, controller, handler, request or response shape, or OpenAPI spec, including when a feature quietly needs a new endpoint or a changed response field and the user never says API. For server internals (timeouts, jobs, logging) use rule-backend; for queries and schema use rule-db."
paths:
  - "**/routes/**"
  - "**/api/**"
  - "**/controllers/**"
  - "**/handlers/**"
  - "**/*.openapi.*"
  - "**/openapi.*"
---

# API Design Rules

Decisions for HTTP endpoints and their request/response shapes. The project's `CLAUDE.md` conventions win on any conflict, and existing API conventions in the codebase win over these defaults: match what the neighbouring endpoints already do.

## Naming

- Paths use plural nouns for collections (`/users`, `/users/{id}`), never verbs (`/getUser`, `/createOrder`) — why: the HTTP method already is the verb.
- Multi-word path segments are kebab-case (`/order-items`) — why: URLs are case-insensitive in places and underscores hide under link underlines.
- JSON field names follow the project's existing case; with none, camelCase — why: mixed casing in one API forces clients to map per endpoint.
- Nest at most one level (`/users/{id}/orders`); deeper lookups use a top-level resource with a filter (`/orders?userId=`) — why: deep nesting forces clients to know every parent id.
- Actions that are not CRUD use a sub-resource noun with POST (`POST /orders/{id}/cancellation`) — why: keeps paths nouns while making the side effect explicit.

## Methods and semantics

- GET never changes state — why: crawlers, prefetchers, and retries call GET freely.
- PUT replaces the whole resource; fields omitted are reset to defaults — why: that is what PUT means to every client and proxy; partial PUT surprises them.
- PATCH updates only the fields sent; `null` clears a field, an absent field is unchanged — why: distinguishing absent from `null` is the only way to clear a value.
- Default to PATCH for updates unless the client always holds the full resource — why: PUT with stale full objects overwrites concurrent edits.
- PUT and DELETE are idempotent: repeating them gives the same state; DELETE of a missing resource returns 404 or 204 consistently across the API — why: clients retry these without keys.

## Status codes

- `200` read or update with a body; `201` create, with a `Location` header of the new resource and the resource in the body — why: clients use `Location` instead of building URLs.
- `204` success with no body (DELETE, actions with nothing to return); never send a body with 204 — why: some clients and proxies fail on a 204 body.
- `400` malformed request or failed validation — why: the client must change the request.
- `422` for semantically invalid but well-formed input only if the project already uses it; otherwise use `400` for all validation — why: mixing both for the same failure confuses clients.
- `401` missing or invalid credentials; `403` authenticated but not allowed — why: 401 tells the client to re-authenticate, 403 tells it not to retry.
- `404` resource does not exist, or exists but the caller may not know it does (return 404, not 403, for other tenants' resources) — why: 403 confirms the id exists.
- `409` conflict with current state (duplicate unique value, version mismatch, idempotency key reused with a different body) — why: tells the client to re-read before retrying.
- `429` rate limited, with a `Retry-After` header in seconds — why: without it clients retry immediately and make it worse.
- `500` unexpected server error only; never use 500 for client mistakes — why: 5xx triggers alerts and client retries.

## Error shape

- One error body for every non-2xx response: `{ "error": { "code": "VALIDATION_FAILED", "message": "...", "details": [...] } }`; if the project already has an error shape, use theirs everywhere instead — why: clients write one error parser.
- `code` is a stable UPPER_SNAKE string clients can switch on; `message` is human-readable and may change — why: clients that parse messages break on rewording.
- Validation errors list every failing field at once: `details: [{ "field": "email", "code": "INVALID_FORMAT", "message": "..." }]`, `field` as a dot path (`items.0.qty`) — why: one-error-at-a-time makes users submit a form N times.
- Errors never include stack traces, SQL, internal hostnames, file paths, library names, or raw upstream error text — why: these map the attack surface.
- Auth failures use the same message whether the user or the password was wrong — why: different messages enumerate accounts.
- The mapping from application errors to this shape lives in one place (see rule-backend) — why: per-handler mapping drifts.

## Pagination and lists

- Every list endpoint is paginated from its first version — why: adding pagination later is a breaking change.
- Cursor pagination: `?limit=` (default 50, max 200, larger values clamped to 200) and `?cursor=`; response `{ "data": [...], "nextCursor": "..." | null }` — why: offsets skip or repeat rows when data changes and get slow on deep pages.
- Cursors are opaque strings (base64 of the sort key plus id) — why: clients that parse cursors break when you change the sort.
- Sort is stable with `id` as the final tiebreaker — why: ties on the sort key make pages skip rows.
- `null` `nextCursor` means the last page; don't return a total count unless asked — why: `COUNT(*)` on large tables is slow on every page.

## Data formats

- Timestamps are ISO 8601 strings in UTC with `Z` (`2026-01-31T14:05:00.000Z`); field names end in `At` (`createdAt`) — why: epoch numbers lose units and local offsets break comparisons.
- Date-only values use `YYYY-MM-DD` — why: a timestamp for a date shifts a day across time zones.
- Ids are strings in JSON, even when numeric in the database — why: 64-bit ints lose precision in JavaScript past 2^53.
- Money is an integer in minor units plus a currency code (`{ "amount": 1999, "currency": "USD" }`) — why: floats round incorrectly.
- Enums are UPPER_SNAKE or lowercase strings matching the project, never integers — why: integer enums are unreadable and reorder-fragile.
- Absent optional fields are `null`, not omitted, in responses — why: clients can tell "no value" from "old server".

## Idempotency

- POSTs that create payments, orders, or anything charged or sent accept an `Idempotency-Key` header (client-generated UUID) — why: a network retry otherwise creates a second charge.
- Same key and same body returns the stored original response; same key and different body returns 409 — why: replay must be safe and misuse must be loud.
- Store keys at least 24h, scoped per authenticated caller — why: shared scope lets one client replay another's response.

## Compatibility and versioning

- Breaking changes need a new version (`/v2/...` path or the project's versioning scheme) and the old version keeps working until clients migrate — why: deployed clients cannot update with the server.
- Breaking means: removing or renaming a field, endpoint, or enum value; changing a field's type or format; making an optional request field required; tightening validation (shorter max, new required format); changing a status code or error `code`; changing default sort or page size — why: each breaks a client that worked yesterday.
- Not breaking: adding an optional request field, adding a response field, adding an endpoint, loosening validation — why: tolerant clients ignore unknowns.
- Adding a new enum value to a response is breaking unless clients are documented to handle unknown values — why: exhaustive switches crash on the new value.
- When an OpenAPI spec exists, update it in the same change as the endpoint — why: a stale spec generates broken clients.

## Done checklist

`/simply:build` Step 5 calls each new or changed endpoint with `curl` and reads the real response:

- [ ] Paths are plural kebab-case nouns; methods match semantics.
- [ ] Create returns 201 with `Location`; empty responses return 204 with no body.
- [ ] An invalid request returns 400 (or the project's 422) with every bad field in `details` at once (shown with a body that has 2+ bad fields).
- [ ] Unauthenticated returns 401, forbidden returns 403, other tenant's id returns 404.
- [ ] Every error response matches the one error shape and contains no stack, SQL, or internal names.
- [ ] Lists accept `limit` and `cursor`, clamp `limit` to 200, return `nextCursor`, and paging through returns each row once.
- [ ] Timestamps are ISO 8601 UTC with `Z`; ids are strings.
- [ ] Payment/order creation honors `Idempotency-Key` (same request twice creates one record).
- [ ] No breaking change to an existing endpoint without a new version; OpenAPI spec updated if present.

## Not covered

- Timeouts, retries, logging, jobs, config: `rule-backend`.
- Schema, migrations, query performance: `rule-db`.
- GraphQL, gRPC, and WebSocket protocols; auth scheme choice; rate-limit numbers; API gateway setup.
