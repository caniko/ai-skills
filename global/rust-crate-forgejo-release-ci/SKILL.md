---
name: rust-crate-forgejo-release-ci
description: "Add strict simit-managed Forgejo Actions CI for Rust crate release readiness on the self-hosted runner runner. Use when a Codeberg-hosted Rust crate needs fmt/clippy/test/doc/package/audit/deny/Nix checks, Attic-ready release jobs, or runner-safe CI before crates.io publication."
---

# Rust Crate Forgejo Release CI

## Required References

Load `../simit-project-init/SKILL.md` first. Use `simit init ci --platform forgejo` as the canonical generator/checker for Rust crate release CI on Codeberg/Forgejo. Load `../runner/SKILL.md` for the shared runner runner facts (single `runner` label, bind-mounted JS action runtime, `https://code.forgejo.org/actions/checkout@v4` URL prefix, sccache, Attic config, Codeberg ToU). Then load `../forgejo-runner-ci/SKILL.md` and `../forgejo-ci/SKILL.md` only for project-specific follow-up details that simit does not cover.

## Hard Rules

- Use Forgejo Actions hosted by Codeberg terminology, and `.forgejo/workflows/`.
- Use the `runner` runner per `../runner/SKILL.md`; do not use Codeberg shared runners unless the user explicitly asks.
- Use official Debian Rust containers for raw-Cargo jobs (`rust:<MSRV>-bookworm`, or `rust:<MSRV>-trixie` when that tag exists). Do not use Alpine for runner Rust CI.
- Add `concurrency` groups to cancel superseded runs.
- Do not put Attic tokens or crates.io tokens in workflow files.

## Release Readiness CI

CI must run the same release checks documented by the project: Nix flake check where present, Cargo fmt, clippy, tests, docs, package dry-run/list, deny, and audit. Generate or refresh it with `simit init ci --platform forgejo`; this should also generate `keys/maintainers.gpg` from the configured release signing key. Validate with `simit release trust check` and `simit init ci --platform forgejo --check --diff`, and only then make narrowly scoped project-specific edits. For the signing-trust fallback before reporting a missing-key blocker, follow the Simit Infrastructure section of `../rust-crate-release-reference/SKILL.md`. If Forgejo Actions are disabled on the repository, report the UI step: Settings -> Units -> Enable Actions.
