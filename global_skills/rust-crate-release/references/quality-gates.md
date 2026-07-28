# Release Quality Gates

Prefer generated Nix checks, simit check modes, and the repository's own
wrappers.

```sh
nix flake check --keep-going --print-build-logs
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- --deny warnings
cargo test --all-features
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features
cargo test --doc --all-features
cargo package --list
cargo publish --dry-run
cargo deny check
cargo audit
```

Run only gates supported by the repository, but report every skipped gate and
the missing producer/tool that must provide it. A release is not ready merely
because ambient Cargo is absent; use the simit-managed Nix environment.
