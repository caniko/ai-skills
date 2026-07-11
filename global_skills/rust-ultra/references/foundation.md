# Rust Skill Foundation

Shared rules for every Rust domain skill.

## Discover first

Inspect `Cargo.toml`, `Cargo.lock`, source/tests/examples/benches, wrappers,
CI, `flake.nix`, Nix files, toolchain files, remotes, and current Git state.
Prefer repository wrappers (`nix develop`, `just`, `make`, or documented
scripts) over ambient commands. Use `cargo metadata` when available.

Never invent API behavior, release metadata, compatibility promises, missing
tool output, or credentials. If a required source is absent, report the
artifact, why it is required, its upstream producer, the exact regeneration
workflow, and the validation command that proves recovery.

## Preserve worktree integrity

Inspect `git status --short` before editing. Do not reset, discard, or absorb
unrelated changes. Keep edits scoped and atomic. Do not commit unless the user
asks or the active workflow explicitly owns the commit.

## Baseline and focused verification

Use the narrowest repository-authoritative checks. The normal baseline is:

```sh
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo check --all-targets
cargo test --all-features
```

For a library documentation change also run:

```sh
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features
cargo test --doc --all-features
```

For release work, load `rust-crate-release` and its release-only gates.
After each structural or semantic profile change, rerun the narrowest failed
check first, then the relevant full gate. Do not continue with a red tree.

## Reporting

Separate facts, changes, skipped checks, blockers, and assumptions. For every
blocker include the missing source and regeneration/validation commands. Keep
public API changes and would-be-breaking changes in an explicit list.
