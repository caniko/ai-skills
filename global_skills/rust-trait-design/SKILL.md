---
name: rust-trait-design
description: Analyze a Rust codebase for missing trait abstractions and interface design issues — extract traits for duplicated behavior, apply dependency inversion, split fat traits. Use when asked to deduplicate behavior into traits, introduce trait bounds at boundaries, refactor type-tag dispatch, or audit existing trait design. Extracted from the yee-haw housekeeping catalog (ConcernId::TraitDesign).
---

# Rust: Trait Design

Analyze the codebase for missing trait abstractions and interface design issues:

Phase 1 — Detect concept smell
1. Find types that implement the same logical behavior with different concrete code
2. Identify methods that accept a concrete type but only use a subset of its API
3. Look for match/if-else chains that dispatch on a type tag to call analogous methods
4. Find free functions that operate on multiple unrelated types via copy-pasted logic

Phase 2 — Extract traits
5. For each detected concept, define a minimal trait that captures the shared behavior:
   - Name the trait after the *capability*, not the implementor
   - Each trait should have 1–5 methods — split into composable traits if more
   - Provide default implementations where a sensible default exists
6. Implement the trait for each concrete type, moving duplicated logic into defaults or helpers
7. Do NOT create traits with a single implementor unless it's a documented extension point

Phase 3 — Apply dependency inversion
8. Update function signatures to accept trait bounds instead of concrete types
   where the function does not need the full concrete API
9. Check module boundaries: if module A imports a concrete type from module B just to call
   2 methods, introduce a trait and depend on it instead

Phase 4 — Audit existing traits
10. Find fat traits with >5 required methods — split into focused sub-traits
11. Find trait methods that most implementors leave as no-ops — move to extension trait
12. Check for traits implemented identically by >2 types — extract a blanket impl

Phase 5 — Verify
13. Verify compilation after each extraction
14. Run tests at the end to confirm no behavior changed
15. Do not change existing trait signatures that are part of a plugin or serialization boundary

Commit each trait extraction as a separate atomic change.

## Rust specifics

Prefer `impl Trait` (static dispatch) for internal module boundaries.
Prefer `&dyn Trait` only when heterogeneous collections or runtime polymorphism are needed.
Run `cargo check --all-targets` after each trait extraction.
Run `cargo test` at the end to confirm no behavior changed.
Do not change existing trait signatures that are part of a plugin or serialization boundary.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **8**
as "relevant":

| Pattern | Weight |
|---|---|
| `dyn ` | 1 |
| `Box<dyn` | 2 |
| `&dyn ` | 1 |
