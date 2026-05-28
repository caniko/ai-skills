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
3. Keep explicit expects only where the invariant is truly guaranteed and document why
4. Leave unwraps in test code alone — they are fine there

Do not change logic or control flow beyond replacing the error handling.
Commit with a summary of how many unwraps were replaced.

## Rust specifics

Use `?` with the crate's error type where possible.
Use `ok_or_else(|| ...)` or `map_err(|e| ...)` for context.
Use `if let` or `match` when the None/Err case needs specific handling.
Keep `.expect("reason")` only where the invariant is truly guaranteed.
Leave `.unwrap()` in test code (#[cfg(test)]) alone — it's fine there.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **10**
as "relevant":

| Pattern | Weight |
|---|---|
| `.unwrap()` | 1 |
| `.expect(` | 1 |
| `unwrap_or(` | 1 |
