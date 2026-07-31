---
name: rust-project-flake
description: Create or modernize Rust Nix flakes with crane and simit. Use for flake outputs, devShells, checks, packages, cross builds, Cargo filtering, or build infrastructure.
---

# Rust Project Flake

## Core Rule

Always build Rust packages with crane. Do not use `rustPlatform.buildRustPackage`, naersk, fenix builders, ad hoc `cargo build` derivations, or shell-only flakes as the primary build path unless the user explicitly asks to compare alternatives.

For Rust crate release work, load `../simit-rust-crate-release-init/SKILL.md` and run `simit init flake` before hand-writing or repairing release flakes. Treat simit's generated flake structure as authoritative unless it reports that manual integration is required; this skill then covers the project-specific crane follow-up work.

Prefer rs-harbor when it fits the project:

- Use `rs-harbor.lib.mkToolchain` to get the Rust toolchain and `craneLib`.
- Use `rs-harbor.lib.mkCargoConfig` for optimized Cargo config outputs when project-local `.cargo/config.toml` generation is useful.
- Use `rs-harbor.lib.mkDevShells` for native, Windows, macOS, and combined cross shells.
- Use `rs-harbor.lib.mkCross` only when cross-compilation shells or packaging are wanted.

For exact starter flakes and module snippets, read [patterns.md](references/patterns.md).

## Workflow

1. Inspect the project shape before editing:
   - `Cargo.toml`, `Cargo.lock`, workspace members, binary names, crate features, `build.rs`, native dependencies, `.cargo/config.toml`, existing `flake.nix`, `shell.nix`, `default.nix`, CI, and README commands.
   - Use `cargo metadata --no-deps --format-version 1` if Cargo is available.
   - Identify native libraries required by `pkg-config`, bindgen, protobuf, OpenSSL, graphics stacks, audio stacks, SQL libraries, or platform SDKs.

2. Choose the flake shape:
   - Rust crate release prep: use `simit init flake` first, then preserve and refine the generated crane-based outputs.
   - New ordinary Rust crate or workspace: use the standard rs-harbor crane flake from `patterns.md`.
   - Existing project with Nix: preserve public outputs and command names where possible, but migrate Rust package builds to crane.
   - Game, GUI, or native-library-heavy project: add `pkgConfigDeps`, `buildInputs`, `nativeBuildInputs`, and `LD_LIBRARY_PATH` in the crane `commonArgs` and dev shell.
   - Project that should not depend on rs-harbor: still use crane directly, and explain why rs-harbor was not used.

3. Implement narrowly:
   - Add or update `flake.nix`.
   - Add small `nix/*.nix` files only when they reduce clutter or match existing project style. When modularizing or optimizing a large flake, split it into `nix/*.nix` files.
   - Keep package, check, and dev shell names predictable: `packages.default`, `checks.{default,clippy,fmt,nextest?}`, `devShells.default`.
   - For workspaces, build from the workspace root and add extra named packages only when the user needs multiple binaries.

4. Validate:
   - Run `nix flake show` or `nix flake check --no-build` first when evaluation is uncertain.
   - Run the narrowest useful build/check: `nix build`, `nix flake check`, or a specific `nix build .#<package>`.
   - If builds are too expensive, at least verify evaluation and report that full builds were not run.

## Uplift Guidance

When uplifting an existing project, avoid churn. Preserve pins when they are intentional, do not delete CI or deployment outputs without a reason, and keep unrelated formatting stable.

Migration priorities:

- Replace non-crane Rust derivations with `craneLib.buildPackage`, `buildDepsOnly`, `cargoClippy`, `cargoFmt`, and optionally `cargoNextest`.
- Move repeated native dependency lists into a local `commonArgs` or a small `nix/package.nix`.
- Make `checks` reuse the same cargo artifacts as the package build where possible.
- Add a dev shell that contains the selected Rust toolchain, native build tools, and project utilities.
- Keep `Cargo.lock` committed for applications and workspaces; if the project is a library without a lockfile, decide whether to generate one based on repo policy.

## rs-harbor Notes

If the current machine has a local rs-harbor checkout or the user asks to use local rs-harbor functionality, prefer a flake input such as:

```nix
rs-harbor.url = "git+file:///absolute/path/to/rs-harbor";
```

For shareable project flakes, prefer the remote input:

```nix
rs-harbor.url = "github:caniko/rs-harbor";
```

Follow rs-harbor inputs to keep one coherent dependency graph:

```nix
nixpkgs.follows = "rs-harbor/nixpkgs";
rust-overlay.follows = "rs-harbor/rust-overlay";
crane.follows = "rs-harbor/crane";
flake-utils.follows = "rs-harbor/flake-utils";
```
