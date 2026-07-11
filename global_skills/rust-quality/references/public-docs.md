# Public Documentation Profile

Document every exported item with useful purpose, arguments, returns, errors,
panics, safety, examples, and intra-doc links. Keep docs.rs feature and target
configuration accurate. Do not invent behavior; derive examples from the
implementation and tests.

Run:

```sh
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features
cargo test --doc --all-features
```

Public API conformance and breaking-change decisions belong to
`rust-api-design`.
