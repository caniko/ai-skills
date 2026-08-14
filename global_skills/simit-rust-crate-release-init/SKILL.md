---
name: simit-rust-crate-release-init
description: Apply strict simit Rust crate release initialization for crates.io-oriented Rust/Cargo crates and workspaces. Use when Codex should wire or validate release-ready `simit init flake` and `simit init ci`, maintainer trust roots, publish workflows, package artifacts, MSRV/docs/audit/deny checks, or generated Rust release infrastructure.
---

# Simit Rust Crate Release Init

Load [simit-project-init-common](.skillnet/deps/simit-project-init-common/SKILL.md)
before running generators. It owns discovery, command resolution, generated
file ownership, existing-flake handling, blockers, and validation.

## Scope

Use `simit` for crates.io-oriented release infrastructure. Confirm a Cargo
crate or workspace, release metadata, and the requested publication surface
before adding trust roots, credentials, artifacts, or publish workflows.

## Release workflow

1. Follow the common discovery and preview steps. Use `--runtime nix` only when
   the release workflow needs flake outputs or project-specific Nix inputs.
2. Apply the flake command selected by the common existing-flake rules, then
   generate verification CI:

   ```sh
   simit init flake [--scope hooks-only]
   simit init ci --platform <platform> [--runtime nix]
   ```

   Add `--runner`, `--with-nextest`, `--with-msrv`, `--with-docs`,
   `--with-audit`, `--with-deny`, or `--with-artifacts` only when discovery and
   the installed CLI justify them.
3. Generate the separate publish workflow:

   ```sh
   simit init release --print
   simit init release
   ```

   Keep crates.io credentials and signing roots in the release workflow. Check
   the maintainer trust root with:

   ```sh
   simit release trust status
   simit release trust init
   simit release trust check
   ```

4. Run the common validation commands, `simit release trust check`, and the
   narrowest meaningful package or test gate after evaluation succeeds.

Forgejo runner details belong to `forgejo-atlas-ci`; do not duplicate them
here. The common flake-modularization routine remains the source for splitting
large project-owned flakes.

## Failure handling

Use the common blocker and generated-file contract. Never hand-merge output or
invent package metadata, signing keys, runners, artifacts, or credentials.
