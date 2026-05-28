---
name: rust-deps-unused
description: Find and remove unused dependencies from a Rust project's Cargo.toml (and dev/build deps), verifying compilation and tests after removal. Use when asked to prune dependencies, remove unused crates, slim down Cargo.toml, or clean up the dependency tree. Extracted from the yee-haw housekeeping catalog (ConcernId::DepsUnused).
---

# Rust: Unused Dependencies

Find and remove unused dependencies from the project manifest:
1. For each dependency listed, check if it is actually imported anywhere in source code
2. Check dev-dependencies against test and bench code
3. Check build-dependencies against build scripts
4. Remove any dependency that has zero imports
5. After removal, verify the project compiles and tests pass

Be conservative: if a dependency is used via a macro or re-export that makes it hard to grep, keep it.
Commit the manifest and lock file changes.

## Rust specifics

Check dependencies in Cargo.toml against `use`/`extern crate` in src/.
Check [dev-dependencies] against test and bench code.
Check [build-dependencies] against build.rs.
Run `cargo check --all-targets` and `cargo test` after removal.
Commit the Cargo.toml and Cargo.lock changes.

## Relevance heuristic (preflight)

No grep-based heuristic in the catalog — run whenever dependency pruning is requested.
`cargo +nightly udeps` (if available) is a good starting signal; otherwise grep imports manually.
