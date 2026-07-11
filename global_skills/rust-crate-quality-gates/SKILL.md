---
name: rust-crate-quality-gates
description: "Enforce strict Rust crate pre-release validation, including simit-managed flake and CI checks. Use for cargo fmt, clippy with denied warnings, tests, doctests, cargo doc with denied warnings, cargo package/publish dry-run, cargo-deny, cargo-audit, and blocker reporting before crates.io release."
---

# Rust Crate Quality Gates

This skill has two modes. Use the same baseline for a pull-request preflight;
add packaging, trust, dependency, and publication gates for a crates.io
release.

## Strict Checks

Run the narrowest equivalent commands provided by the project toolchain. When the crate has or should have simit-managed release infrastructure, validate that first:

```sh
simit init flake --check --diff
simit release trust check
simit init ci --platform <platform> --check --diff
```

For the simit trust-root fallback (`simit release trust status|init`) before classifying a missing-key blocker, follow the Simit Infrastructure section of `../rust-crate-release-reference/SKILL.md`.

Then run the generated Nix checks when present, or the raw Cargo equivalents:

```sh
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- --deny warnings
cargo test --all-features
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features
```

For release readiness, add the packaging and dependency checks:

```sh
cargo package --list
cargo publish --dry-run
cargo deny check
cargo audit
```

For a pull request, stop after the project-appropriate fmt, clippy, targeted
tests, and build/package checks. Inspect `just`, `make`, CI workflows, and the
flake first, and run the gates inside the repository's wrapper environment
(`nix develop`, `just`, or an equivalent) when required. Clippy warnings in
the CI-equivalent gate are blockers.

The shared baseline runner is available from this skill directory at:

```sh
./scripts/run-rust-pr-gates.sh
```

Use its `--prefix`, `--check`, and `--test` options when the repository needs a
wrapper or a narrowed package/test selection. Report every skipped gate and
why the repository cannot support it.

If the project uses Nix, prefer `nix flake check --keep-going --print-build-logs` once the simit-managed flake exposes these checks. Do not mark the release ready when a required tool is absent; either add it through simit-managed release tooling/dev shell follow-up work or report the missing prerequisite and validation command.

## Reporting

Classify failures as blockers unless explicitly out of scope. Include the failed command, why it matters for release, and the concrete next fix.
