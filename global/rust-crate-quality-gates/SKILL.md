---
name: rust-crate-quality-gates
description: "Enforce strict Rust crate pre-release validation, including simit-managed flake and CI checks. Use for cargo fmt, clippy with denied warnings, tests, doctests, cargo doc with denied warnings, cargo package/publish dry-run, cargo-deny, cargo-audit, and blocker reporting before crates.io release."
---

# Rust Crate Quality Gates

## Strict Checks

Run the narrowest equivalent commands provided by the project toolchain. When the crate has or should have simit-managed release infrastructure, validate that first:

```sh
simit init-flake --check --diff
simit release trust check
simit init-ci --platform <platform> --check --diff
```

If `simit release trust check` fails because the trust root is missing or stale,
run `simit release trust status` and `simit release trust init` before
classifying it as a missing-key blocker.

Then run the generated Nix checks when present, or the raw Cargo equivalents:

```sh
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- --deny warnings
cargo test --all-features
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features
cargo package --list
cargo publish --dry-run
cargo deny check
cargo audit
```

If the project uses Nix, prefer `nix flake check --keep-going --print-build-logs` once the simit-managed flake exposes these checks. Do not mark the release ready when a required tool is absent; either add it through simit-managed release tooling/dev shell follow-up work or report the missing prerequisite and validation command.

## Reporting

Classify failures as blockers unless explicitly out of scope. Include the failed command, why it matters for release, and the concrete next fix.
