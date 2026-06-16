---
name: rust-unwrap-audit
description: Audit unwrap/expect-style calls in non-test Rust code and replace panicking ones with proper error handling. Use when asked to remove unwraps, harden panic paths, propagate errors idiomatically, or audit .unwrap()/.expect() usage. Extracted from the yee-haw housekeeping catalog (ConcernId::UnwrapAudit).
---

# Rust: Unwrap / Expect Audit

Audit every use of unwrap/expect-style calls in non-test code:
1. For each occurrence, determine if the unwrap can actually panic at runtime
2. Replace panicking unwraps with proper error handling:
   - Use the language's idiomatic error propagation
   - Add context to errors explaining what operation failed
   - Use pattern matching when the error case needs specific handling
3. **Pay special attention to `.expect()` in startup / boot-time code.**  A panic on startup can leave the system in a half-initialized state.  Replace boot-time `.expect()` on recoverable failures (e.g. undecryptable stale state files, missing optional artifacts) with `if let Err(e) = ... { warn!(...) }` — log and continue rather than aborting the process.  Reserve `.expect()` at startup only for invariants whose failure means the system cannot function at all and must abort immediately.
4. **Look for best-effort self-healing opportunities.**  If a stale file or corrupt cache prevents a routine operation (startup purge, cleanup), the correct response is to warn and continue with a fresh state, not to panic.  Evaluate whether replacing the panicking path with "log and replace" (self-healing) or "log and skip" (best-effort) is safe for that specific subsystem.
5. Keep explicit expects only where the invariant is truly guaranteed and document why
6. Leave unwraps in test code alone — they are fine there

Do not change logic or control flow beyond replacing the error handling.
Commit with a summary of how many unwraps were replaced and how many boot-time panics were downgraded to warnings.

## Rust specifics

Use `?` with the crate's error type where possible.
Use `ok_or_else(|| ...)` or `map_err(|e| ...)` for context.
Use `if let` or `match` when the None/Err case needs specific handling.
Keep `.expect("reason")` only where the invariant is truly guaranteed.
Leave `.unwrap()` in test code (#[cfg(test)]) alone — it's fine there.

For boot-time `.expect()` replacements, the canonical pattern is:
```rust
if let Err(err) = potentially_failing_cleanup_op() {
    warn!(?err, "could not clean up stale state, continuing");
    // Do not propagate the error — the system can operate without this cleanup
}
```
Use `warn!` (not `error!`) because the condition is expected and recoverable.  If the operation is genuinely critical (missing database, bad config), keep the `.expect()` but document the invariant.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **10**
as "relevant":

| Pattern | Weight |
|---|---|
| `.unwrap()` | 1 |
| `.expect(` | 1 |
| `unwrap_or(` | 1 |
