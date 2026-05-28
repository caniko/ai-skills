---
name: rust-crate-manifest-metadata
description: "Validate and update Rust crate Cargo.toml metadata for crates.io readiness. Use for package description, license/license-file, repository/homepage/documentation/readme, rust-version/MSRV, keywords/categories, package include/exclude, docs.rs metadata, features, and dependency/version policy before publishing."
---

# Rust Crate Manifest Metadata

## Inspect

Read `Cargo.toml`, workspace manifests, `Cargo.lock`, README/license files, remotes, default branch, and existing CI/docs. Use `cargo metadata --no-deps --format-version 1` when Cargo is available. Do not infer metadata from memory when the repository already contains a source of truth.

## Required Fields

For crates.io release readiness, ensure `Cargo.toml` has:

- `name`, `version`, `edition`, `description`, and either `license` or `license-file`.
- `repository` pointing at the canonical source host.
- `readme = "README.md"` when a README exists and should render on crates.io.
- `documentation = "https://docs.rs/<crate-name>"` for public crates.
- `rust-version` matching the minimum supported Rust version, especially for edition 2024 crates.
- `keywords` and `categories` only when accurate and accepted by crates.io limits.

## Package Contents

Add `include = [...]` for small library crates when it prevents accidental packaging of generated output or local-only files. Include the manifest, lockfile when intentionally committed, README, license, source, examples/tests/docs that should publish, and exclude build artifacts.

Validate package contents with:

```sh
cargo package --list
cargo publish --dry-run
```

Run the simit check-mode triad first when release infrastructure is in scope (see the Simit Infrastructure section of `../rust-crate-release-reference/SKILL.md`). If Cargo is unavailable, use the simit-managed Nix dev shell/checks when present. If neither Cargo nor a valid simit-managed dev shell is available, report the exact missing toolchain and defer package validation until a dev shell or CI provides Cargo.

## docs.rs Metadata

Use `[package.metadata.docs.rs]` when the crate needs specific feature selection or rustdoc flags. Prefer:

```toml
[package.metadata.docs.rs]
all-features = true
rustdoc-args = ["--cfg", "docsrs"]
```

Only add target-specific metadata when the crate has target-specific behavior.
