---
name: rust-error-architecture
description: Improve the error TYPE design of a Rust crate — coherent typed error enums, #[from]/#[source] composition, #[non_exhaustive] public errors, no leaked anyhow/Box<dyn Error> in library signatures. Use when asked to design error types, replace stringly-typed errors, adopt thiserror, stop returning Box<dyn Error>/anyhow from a library API, or separate recoverable errors from bugs. Message wording and Display text quality belong to rust-error-messages, not here. Part of the rust-ultra Rust improvement arsenal.
---

# Rust: Error Type Architecture

Audit the error TYPES a crate produces and shape them into one coherent design per crate or module boundary. Do not touch the wording of error messages — that is rust-error-messages.

1. Inventory every error type and every error-returning signature: scan for `Result<_, String>`, `Result<_, Box<dyn Error>>`, public functions returning `anyhow::Error`/`eyre::Report`, and ad-hoc `Err(format!(...))`.
2. Decide the boundary: a library should expose one (or a small set of) named, typed error enums per module boundary; a binary or internal glue layer may use `anyhow`/`eyre` freely at the top level. Classify each call site as library-public, library-internal, or binary.
3. Replace stringly-typed errors (`String`, `format!`-as-error, `&'static str` errors) on library-public and reusable internal paths with typed enum variants that name the distinct failure mode. Keep one variant per genuinely distinct failure — do NOT flatten unrelated failures into one opaque `Other(String)` catch-all.
4. For each typed variant that wraps a lower-level cause, retain that cause as a `#[source]` (or `#[from]`) field so the error chain is preserved; never collapse the underlying error away — keeping it as a typed source, not how the message reads, is the concern here.
5. Add `#[from]` conversions for the error types a function naturally propagates, so `?` composes without manual `map_err`; only add `#[from]` where the conversion is unambiguous (one source type per target variant) — otherwise keep an explicit, named variant.
6. Separate recoverable errors from programmer bugs: model recoverable conditions as error variants returned via `Result`; leave true invariant violations as panics, and do not invent an error variant for a condition that can only occur via a bug. Decide only whether a condition belongs in the error type — adding or placing the guard itself is rust-fail-fast.
7. Mark every public error enum `#[non_exhaustive]` so adding variants later is not a breaking change; do this only on types actually exported from the crate.
8. Stop libraries from leaking `anyhow::Error`, `eyre::Report`, or `Box<dyn Error>` in public signatures — convert those boundaries to the crate's typed error; leave such types in place inside binaries and `#[cfg(test)]` code.
9. Collapse accidental duplication: if two modules define near-identical error enums for the same boundary, unify them; conversely, if one god-enum mixes unrelated subsystems, split it along the module boundary.
10. Leave well-shaped error types alone: a crate that already exposes a `thiserror`-derived, `#[non_exhaustive]`, source-preserving enum needs no churn. Do not rename variants or restructure a sound hierarchy for taste.
11. Do not alter control flow or message strings; change only the error type definitions, their derives, and the signatures/conversions that thread them.

Commit with a summary of which boundaries were typed, how many stringly-typed errors were replaced, and which signatures stopped leaking `anyhow`/`Box<dyn Error>`.

## Rust specifics

Derive library error types with `#[derive(thiserror::Error, Debug)]`, one `#[error("...")]` per variant, `#[from]` for clean `?` propagation, and `#[source]` to retain the cause chain. Mark exported enums `#[non_exhaustive]`. Keep `anyhow`/`eyre` confined to binaries and internal glue — they must not appear in a library's public signatures. Hand-implement `std::error::Error` only when `thiserror` cannot express the shape. Run `cargo check --all-targets` and `cargo test` after the refactor; confirm with `cargo public-api` (if available) or a grep of `pub fn` signatures that no `anyhow::Error`/`Box<dyn Error>` leaks across the crate boundary.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **5** as "relevant":

| Pattern | Weight |
|---|---|
| `Box<dyn Error` | 3 |
| `Box<dyn std::error::Error` | 3 |
| `, String>` | 2 |
| `Err(format!` | 2 |
| `thiserror` | 1 |
