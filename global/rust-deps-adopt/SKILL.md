---
name: rust-deps-adopt
description: Scan a Rust codebase for hand-written code that a well-maintained crate already provides, evaluate candidates, and adopt the library. Use when asked to replace custom parsers/retry loops/CLI handling/HTTP clients/date math with crates, reduce hand-rolled code, or adopt dependencies. Extracted from the yee-haw housekeeping catalog (ConcernId::DepsAdopt).
---

# Rust: Dependency Adoption

Scan the codebase for hand-written code that well-maintained libraries already provide:
1. Identify patterns: custom parsers, retry loops, CLI arg handling, HTTP clients,
   date/time math, path manipulation, string processing, concurrency primitives,
   encoding/hashing, rate limiting, configuration loading
2. For each candidate replacement, evaluate the library:
   - Maintenance: recent commits, responsive maintainer, CI passing
   - Adoption: download count, used by other well-known projects
   - Cost: additional compile time, transitive dependency count
   - API fit: does the library's API map cleanly to the project's usage?
3. Skip trivial code (< 20 lines) where the dependency cost exceeds maintenance savings
4. For each adoption:
   - Add the dependency with minimal feature flags
   - Replace the hand-written code with the library's API
   - Remove now-dead internal code
   - Verify compilation and tests pass after each replacement
5. Commit each adoption as a separate atomic change.

## Rust specifics

Use `cargo add <crate>` with minimal feature flags.
Run `cargo check --all-targets` and `cargo test` after each replacement.
If customization is needed, vendor the crate source under `vendor/` and document why.

## Relevance heuristic (preflight)

No grep-based heuristic in the catalog — this concern is qualitative. Run when asked to
reduce hand-rolled code or when you notice substantial custom implementations of
well-solved problems.
