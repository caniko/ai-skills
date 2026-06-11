---
name: rust-pr-preflight
description: Run this before submitting or updating a Rust pull request. It enforces the standard Rust PR gates, especially cargo fmt and cargo clippy with denied warnings, then targeted tests/build checks appropriate to the changed crate.
metadata:
  short-description: Preflight Rust PRs before submission
---

# Rust PR Preflight

Use this skill whenever preparing, submitting, updating, or self-reviewing a Rust PR.

## Required Workflow

1. Inspect the repo for existing CI/check commands first: `just`, `make`, `.github/workflows`, `flake.nix`, `deny.toml`, and project docs may define stricter gates.
2. Run the local standard gates before push/submission:
   - `cargo fmt --check`
   - `cargo clippy -- -D warnings` or the stricter clippy command already used by CI
   - Targeted tests for the changed package/module
   - Package or workspace check/build matching the PR scope
3. If the repo requires a wrapper environment, run the same gates inside it. Examples: `nix shell ... -c`, `nix develop -c`, `just`, or `cargo-hack`.
4. Treat clippy warnings in the project’s CI-equivalent clippy gate as PR blockers. Do not submit, force-push, or mark ready while that gate fails.
5. Report the exact commands that passed in the final answer or PR prep note.

## DRY Gate Runner

Use `scripts/run-rust-pr-gates.sh` as the shared baseline instead of hand-writing the common commands each time.

Examples:

```sh
~/canix/Projects/ai-skills/global/rust-pr-preflight/scripts/run-rust-pr-gates.sh
```

```sh
~/canix/Projects/ai-skills/global/rust-pr-preflight/scripts/run-rust-pr-gates.sh \
  --prefix 'nix shell nixpkgs#rustc nixpkgs#cargo nixpkgs#rustfmt nixpkgs#clippy nixpkgs#pkg-config nixpkgs#openssl -c' \
  --check '-p rauthy -p rauthy-data' \
  --test '-p rauthy-data generated_secret --lib'
```

Add `--all-targets` only when the repository CI uses all targets or the PR scope requires test/example clippy coverage.

Only skip a gate when the repository cannot support it; if skipped, state why and what replaced it.
