---
name: rust-msrv
description: Verify and set the Minimum Supported Rust Version (MSRV) for a Rust crate. Use when asked to check/set the rust-version field, validate the crate compiles on its declared MSRV, determine the minimum Rust version from edition and feature usage, or document MSRV. Extracted from the yee-haw housekeeping catalog (ConcernId::Msrv).
---

# Rust: MSRV (Minimum Supported Rust Version)

Verify the Minimum Supported Rust Version (MSRV):
1. Check if `rust-version` is set in Cargo.toml
2. If set, verify the codebase compiles with that Rust version:
   - Look for features or syntax that require a newer version
   - Check dependency MSRV requirements
3. If not set, determine the minimum version needed:
   - Check the edition field (2021 needs 1.56+, 2024 needs 1.85+)
   - Check for features like let-else, async traits, etc.
4. Update the `rust-version` field in Cargo.toml if it's wrong or missing
5. If the project uses a Rust edition that implies a high MSRV, just verify it's documented

Commit any Cargo.toml changes.

## Rust specifics

The universal methodology above is Rust-native already. If `cargo-msrv` is available,
`cargo msrv find` / `cargo msrv verify` is the authoritative check; otherwise reason from
the edition and feature usage as described above.

## Relevance heuristic (preflight)

No grep-based heuristic in the catalog — run whenever MSRV verification or a
crates.io release readiness pass is requested.
