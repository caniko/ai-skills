---
name: rust-fail-fast
description: Audit Rust code for missing fail-fast validation and add early-return precondition checks. Use when asked to validate inputs at function boundaries, catch silently-swallowed errors, harden builder/initialization patterns, or add guard clauses with clear error messages. Extracted from the yee-haw housekeeping catalog (ConcernId::FailFast).
---

# Rust: Fail-Fast Validation

Audit the codebase for missing fail-fast validation:
1. Review every public function and method — does it validate its preconditions before doing work?
   - Check for invalid/empty inputs that would cause subtle bugs downstream
   - Check for out-of-range values, null-equivalent states, or contradictory arguments
   - Check for filesystem paths, URLs, or config values used without validation
2. Look for functions that silently swallow errors or continue with default/fallback values:
   - Unwrap-or-default calls that hide a real problem
   - Optional handling with no else branch where None is actually an error
   - Match arms that silently return early for unexpected variants
   - Catch-all patterns that suppress genuinely unexpected variants
3. Check builder patterns and multi-step initialization:
   - Ensure finalization methods validate all required fields
   - Ensure partially-initialized objects cannot be used in an invalid state
4. Add early-return validation with clear error messages at function entry points:
   - Error messages must name the parameter and explain the constraint violated
   - Validate at the outermost public boundary; do not duplicate checks in internal helpers
5. Do not add validation that duplicates the type system
6. Do not change function signatures or public API surface

Commit with a summary of which functions gained validation and what conditions are now checked.

## Rust specifics

The universal methodology above is sufficient for Rust — no extra cargo commands required.
Prefer `eyre::ensure!()` / `bail!()` (or the crate's error style) for guard clauses, and
return early via `?` rather than nesting.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **8**
as "relevant":

| Pattern | Weight |
|---|---|
| `.unwrap()` | 1 |
| `panic!(` | 3 |
| `unimplemented!(` | 3 |
| `unreachable!(` | 2 |
| `todo!(` | 2 |
