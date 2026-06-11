---
name: rust-test-gaps
description: Identify and fill test coverage gaps in a Rust crate — untested public functions, error paths, edge cases, trait-contract and generic coverage. Use when asked to improve test coverage, add missing unit tests, test error/edge cases, or strengthen weak assertions. Extracted from the yee-haw housekeeping catalog (ConcernId::TestGaps).
---

# Rust: Test Gaps

Identify and fill test coverage gaps:
1. Review each public function and method — does it have at least one test?
2. Look for untested error paths and edge cases:
   - Error handling branches
   - Boundary conditions (empty input, max values, null transitions)
   - Configuration variations
3. Check that existing tests actually assert meaningful behavior (not just "doesn't panic")
4. Write focused unit tests for the most critical untested paths
5. Prioritize: core business logic > public API > internal helpers
6. For trait implementations: test that each impl satisfies the trait's behavioral
   contract (not just compiles). For generic code: test with at least 2 distinct concrete
   types to verify trait bounds are sufficient.

Write tests in the existing test module style.
Do not refactor existing tests. Focus on adding new ones.
Commit the new tests with a summary of what coverage was added.

## Rust specifics

Write tests in the existing test module style (inline #[cfg(test)] or tests/ directory,
whichever the project uses).

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **5**
as "relevant":

| Pattern | Weight |
|---|---|
| `pub fn ` | 1 |
| `pub async fn ` | 1 |
