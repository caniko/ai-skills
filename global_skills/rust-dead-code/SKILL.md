---
name: rust-dead-code
description: Audit a Rust crate or workspace for dead code and remove it safely. Use when asked to find unused functions, types, traits, constants, modules, feature-gated code, or stale test helpers, or to clean up dead_code/unused warnings. Extracted from the yee-haw housekeeping catalog (ConcernId::DeadCode).
---

# Rust: Dead Code Audit

Audit the codebase for dead code:
1. Search for functions, structs, enums, traits, and constants that have no callers
2. Check for modules that are declared but never used
3. Look for feature-gated code where the feature is never enabled
4. Check for test helpers that are no longer used by any test

Remove all confirmed dead code. Do not remove code that is part of a public API.
If unsure whether something is used, leave it and add a `// TODO: verify usage` comment.
Commit removals with a clear description of what was removed and why.

## Rust specifics

Run `cargo check --all-targets` and note any dead_code, unused_imports, or unused_variables warnings.
Do not remove pub items in lib.rs.

## Relevance heuristic (preflight)

This concern is most worth running when the crate shows these signals. Grep for each
pattern, multiply hits by its weight, and treat a combined score ≥ **4** as "relevant":

| Pattern | Weight |
|---|---|
| `#[allow(dead_code)]` | 3 |
| `// unused` | 2 |
| `// TODO: remove` | 2 |
| `#[deprecated` | 2 |
