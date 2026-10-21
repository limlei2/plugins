---
name: rule-validate-at-the-edges
description: "Apply when placing validation, error handling, or framework glue. Validate at system boundaries, trust internal types after that, and keep business logic in pure functions."
disable-model-invocation: true
---

# Validate at the Edges

Validate and handle errors where data enters the system: request handlers, CLI args, config files, external API responses, files on disk. Parse it into typed domain values there, then trust those types everywhere inside. Business logic is pure functions; the framework shell only calls them.

**Why:** Validation scattered through the call chain is redundant noise that still misses the one entry point nobody guarded, and logic tangled with the framework cannot be tested without it.

**Do:**
- Parse raw input into a domain type once, at the entry point; return an error there.
- Inside, pass the typed value; no re-checking for null or shape in deeper functions.
- Keep business rules in pure functions (input in, result out, no I/O) and test them directly.
- Return domain types from the public surface, never ORM rows, HTTP responses, or wire types.
- Ask of each check: is data crossing a boundary right here? If not, delete the check.

**Not this:**
- `if (!user) throw` in five functions that all receive a validated `User`.
- Price calculation inside an Express route handler.
- Reading `process.env` deep in business code instead of a parsed config object.

**In simply:** `/simply:tdd` before writing code. The simply scripts follow it: `check_handoff.py`, `check_log.py`, `check_briefs.py`, and `run_state.py` validate a file at the boundary so readers can trust it.
