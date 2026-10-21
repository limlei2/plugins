---
name: rule-test-what-users-see
description: "Apply when you write, change, or keep a test. Assert what users of the code can observe, so the test fails when behavior breaks and survives a refactor."
disable-model-invocation: true
---

# Test What Users See

Behavior is what a caller, end user, or external service can observe: return values, error types, state read back, requests sent, rows written. Implementation is everything else: private helpers, call order, intermediate data. Assert behavior only, with an expected value taken from the requirement, not from a run of the code.

**Why:** A test pinned to internals breaks on every refactor and still misses real bugs; a test with a loose or self-derived assertion passes while the feature is broken.

**Do:**
- Run two thought edits on each test: break the behavior (wrong value, skipped effect, effect twice) and it must fail; restructure internals with the same output and it must pass.
- Drive the code through its public interface with one concrete input per case.
- Write expected values by hand from the criterion (`limit=2` returns exactly 2 items), never by copying current output.
- Mocking an external service is fine; assert the payload it receives, since that service observes it.
- For "never does X", pair the no-call assertion with a case where X happens, to prove the test can see it.
- Assert the error type callers branch on, not the exact message wording.

**Not this:**
- `expect(service._buildQuery).toHaveBeenCalled()`: an internal helper no user sees.
- `expect(result).toBeTruthy()` when the contract promises a specific list.
- Expected value computed by calling the function under test.
- A snapshot of an entire component tree for a change to one label.

**In simply:** `/simply:tdd` writes each criterion's failing test first and counts a green suite only if a test exercises the criterion; brief Criteria like "A test covers each behavior above".
