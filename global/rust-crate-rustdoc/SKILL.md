---
name: rust-crate-rustdoc
description: "Make a Rust crate's public API documentation ready for docs.rs and crates.io release. Use for crate-level docs, public item rustdoc, examples/doctests, docs.rs cfgs, warning-denied cargo doc validation, and deciding whether missing_docs should be enforced."
---

# Rust Crate Rustdoc

## Documentation Bar

Every public item should explain what it represents, serialization/display behavior when relevant, and any legal or compatibility limitations without overstating legal advice. Crate-level docs should include a compact example that compiles as a doctest when practical.

Only add `#![deny(missing_docs)]` after the crate can satisfy it cleanly. Prefer fixing documentation over suppressing warnings.

## Validation

Run:

```sh
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features
cargo test --doc --all-features
```

If docs.rs-specific cfg is used, validate with:

```sh
RUSTDOCFLAGS="--cfg docsrs -D warnings" cargo doc --no-deps --all-features
```

Report any warnings as release blockers for strict mode.
