---
name: simit-rust-project-ci-init
description: Apply simit Rust project initialization for ordinary Rust/Cargo projects that need reliable flake-integrated CI but are not being prepared for crates.io release. Use for projects that contain Rust code, services, tools, binaries, or workspaces needing `simit init flake`, `simit init ci`, persisted `[ci]` policy, and validation without release publishing.
---

# Simit Rust Project CI Init

Load [simit-project-init-common](.skillnet/deps/simit-project-init-common/SKILL.md)
before running generators. It owns discovery, command resolution, generated
file ownership, existing-flake handling, blockers, and validation.

## Scope

Use `simit` for ordinary Rust project flake and CI wiring. Do not add crates.io
publishing, release artifacts, signing roots, or release credentials. For
release work, load `../simit-rust-crate-release-init/SKILL.md`.

## Rust-specific workflow

1. Follow the common discovery and preview steps. Confirm a Cargo crate or
   workspace and determine the platform from remotes and workflow locations.
2. Prefer `--runtime nix` when the flake owns meaningful packages, apps,
   checks, devShells, modules, libraries, or Nix-only runtime dependencies;
   otherwise use direct Cargo.
3. Apply the flake generator. For a project-owned flake, use
   `simit init flake --scope hooks-only` when Simit should own only hooks;
   otherwise use `simit init flake`.
4. Apply CI with the discovered platform and selected runtime:

   ```sh
   simit init ci --platform <platform> [--runtime nix]
   ```

   Add `--runner`, `--with-msrv`, `--with-audit`, `--with-deny`,
   `--with-docs`, `--with-nextest`, or `--with-om-ci` only when project
   evidence and the installed `simit init ci --help` justify them. Persist
   choices in `[ci]`; keep `publish_crates = false` or omitted.
5. Run the common validation commands, then the narrowest meaningful Cargo or
   flake checks, such as `cargo fmt --check`, `cargo clippy`, and `cargo test`.

Forgejo runner routing belongs to `forgejo-atlas-ci` and its shared references;
do not copy runner tables or checkout recipes here.

## Failure handling

Use the common blocker and generated-file contract. Never hand-merge generated
output or invent missing package names, runners, workflow targets, or outputs.
