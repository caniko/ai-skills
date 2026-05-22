---
name: rust-crate-nix-release-tooling
description: "Add or audit simit-managed Nix release tooling for Rust crates before crates.io publication. Use for crane-based flake.nix/flake.lock, devShells, packages, checks, docs/site outputs, and Cargo availability when ambient cargo is missing."
---

# Rust Crate Nix Release Tooling

## Required References

Before editing Nix files for Rust crate release work, load `/home/can/.codex/skills/simit-project-init/SKILL.md`, then `/home/can/.codex/skills/rust-project-flake/SKILL.md`.

Use `simit init-flake` as the canonical first edit/check for release flakes. Follow its generated structure where possible. Use the Rust project flake skill only for project-specific follow-up work that simit does not generate cleanly, and keep its rule: Rust packages must be built with crane, not `rustPlatform.buildRustPackage`, naersk, or ad hoc shell-only flakes.

Validate simit alignment with:

```sh
simit init-flake --check --diff
```

## Outputs

For a release-ready library crate, expose:

- `packages.default` for the crate build or package validation target.
- `devShells.default` with Rust toolchain, rustfmt, clippy, cargo-deny, cargo-audit, mdbook when docs exist, and any project tools.
- `checks.default`, `checks.fmt`, `checks.clippy`, `checks.test`, `checks.doc`, and package/dry-run checks when practical.
- `packages.docs` and `packages.site` when Codeberg Pages docs are part of the release surface.

Validate with:

```sh
simit init-flake --check --diff
nix flake show
nix flake check --keep-going --print-build-logs
```
