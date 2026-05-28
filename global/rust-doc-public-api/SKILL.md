---
name: rust-doc-public-api
description: Document every public item in a Rust crate to docs.rs standards — Examples, Errors, Safety, Panics sections, module docs, intra-doc links, warning-free cargo doc. Use when asked to add rustdoc, document the public API, fill in missing doc comments, or make docs ready for docs.rs. Extracted from the yee-haw housekeeping catalog (ConcernId::DocPublicApi).
---

# Rust: Public API Documentation

Document every public item in the project. Each doc comment must state *what*
it does and *why* a caller uses it — no filler. Required sections:
examples for non-trivial functions; error documentation listing each
error variant's trigger; safety documentation for unsafe functions; panic
documentation if any panic path exists. Add module-level docs to every module
explaining purpose and key types. Use intra-doc links over prose references.
Verify documentation compiles. Run the test suite to verify doc-tests compile.
Do not change logic or tests — docs only.

## Rust specifics

Required sections: `# Examples` (compilable) for non-trivial functions; `# Errors` listing
each error variant's trigger; `# Safety` for unsafe fns; `# Panics` if any panic path exists.
Use intra-doc links (`[`OtherType`]`) over prose references.
Add `#![warn(missing_docs)]` to crate root if absent.
Run `cargo doc --no-deps --document-private-items 2>&1` and fix every warning.
Run `cargo test` to verify doc-tests compile.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **10**
as "relevant":

| Pattern | Weight |
|---|---|
| `pub fn ` | 1 |
| `pub struct ` | 1 |
| `pub enum ` | 1 |
| `pub trait ` | 2 |
| `pub type ` | 1 |
