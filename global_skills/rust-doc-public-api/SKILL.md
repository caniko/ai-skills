---
name: rust-doc-public-api
description: Document every public item in a Rust crate to docs.rs and crates.io release standards — Examples, Errors, Safety, Panics sections, module docs, intra-doc links, warning-free cargo doc, and docs.rs cfg validation. Use when asked to add rustdoc, document the public API, fill in missing doc comments, or make release documentation ready. Extracted from the yee-haw housekeeping catalog (ConcernId::DocPublicApi).
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
Run `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features` and fix every warning.
Run `cargo test --doc --all-features` to verify doc-tests compile. When the
crate uses docs.rs-specific cfgs, also run:

```sh
RUSTDOCFLAGS="--cfg docsrs -D warnings" cargo doc --no-deps --all-features
```

Report documentation warnings as release blockers when strict release gates
are in scope.

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
