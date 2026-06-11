---
name: rust-error-messages
description: Audit error messages throughout a Rust codebase for clarity and actionability — say what failed, include the offending value, suggest what to do. Use when asked to improve error messages, make errors more actionable, audit Display/Error impls, or clean up vague "failed"/"invalid" strings. Extracted from the yee-haw housekeeping catalog (ConcernId::ErrorMessages).
---

# Rust: Error Messages

Audit error messages throughout the codebase for clarity and actionability:
1. Find all error strings in error-producing positions
2. For each error message, check:
   - Does it say WHAT failed? (not just "invalid input" but "config path does not exist")
   - Does it include the offending VALUE? (the path that was missing, the key that was unknown)
   - Does it suggest what to DO? ("did you mean ...?", "expected one of: ...")
3. Improve vague messages: replace generic strings like "failed", "invalid", "error"
   with specific descriptions
4. Ensure error chains are not lost: wrapping should add context, not replace the underlying error
5. Audit `Display` and `std::error::Error` impls on custom error types — these produce the
   messages users see in error chains. Ensure they follow the same clarity standards.
6. Do not change error types or error handling logic — only improve the human-readable strings

Commit with a summary of how many error messages were improved.

## Rust specifics

Find error strings via `.context("...")`, `bail!("...")`, `eyre!("...")`, `format!("...")`
in error positions, and custom Display impls on error types.
Use `eyre::ensure!()` or `bail!()` for precondition checks (match the crate's error style).
Audit `Display` and `std::error::Error` impls on error types — these produce the messages in error chains.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **5**
as "relevant":

| Pattern | Weight |
|---|---|
| `.context("` | 1 |
| `bail!("` | 1 |
| `eyre!("` | 1 |
| `anyhow!("` | 1 |
| `.map_err(` | 1 |
