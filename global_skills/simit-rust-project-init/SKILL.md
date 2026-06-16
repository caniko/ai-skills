---
name: simit-rust-project-init
description: Apply simit project initialization to Rust/Cargo projects or Rust workspaces. Use when Codex should run or wire `simit init flake` and `simit init ci`, refresh generated Rust flake and CI files, validate simit-managed output, or optimize a Rust flake that simit patched. This skill is for applying simit to Rust projects, not for changing simit itself.
---

# Simit Rust Project Init

## Purpose

Use `simit` as the canonical initializer for Rust project flake and CI wiring. Prefer generated output over hand-written substitutes, and stop when required project metadata is missing instead of fabricating package names, MSRV, runners, or workflow targets.

## Discovery

Before running generators:

1. Confirm the project root and VCS state with `pwd`, `git status --short`, and the Cargo workspace root.
2. Read `Cargo.toml`, `Cargo.lock` when present, existing `flake.nix`, `nix/*.nix`, and existing CI workflows. If there is no Rust crate or workspace, stop; `simit` initializes Rust projects.
3. Determine the CI platform from repository remotes and existing workflow locations:
   - `.forgejo/workflows/` or Codeberg/Forgejo remote: `--platform forgejo`.
   - `.github/workflows/` or GitHub remote: `--platform github`.
4. Determine whether CI should use direct Cargo or `--runtime nix`. Use `--runtime nix` only when the workflow intentionally needs flake outputs, release artifacts, or project-specific Nix dependencies.
5. If required inputs are missing, stop and report the missing artifact, why it is required, the upstream command or workflow to regenerate it, and the validation command.

## Command Resolution

Use `simit` from `PATH` when available:

```sh
simit --help
```

If it is not installed, use the local checkout without changing the target project:

```sh
cargo run --manifest-path ~/canix/Projects/simit/Cargo.toml -- <simit-args>
```

Do not replace `simit` with hand-written CI or flake templates unless `simit` reports that manual integration is required.

## Workflow

1. Preview flake changes:
   ```sh
   simit init flake --print
   ```

2. Apply flake wiring:
   ```sh
   simit init flake
   ```

3. If `simit init flake` patched an existing `flake.nix`, optimize the flake after generation. Read and follow [flake-modularization.md](references/flake-modularization.md). Keep simit's generated hook files (`nix/treefmt.nix`, `nix/pre-commit.nix`) authoritative unless the user explicitly asks to customize them.

4. Apply CI wiring with the discovered platform and only the options justified by project files:
   ```sh
   simit init ci --platform forgejo
   simit init ci --platform github
   ```

   Add `--runtime nix`, `--runner`, `--with-nextest`, `--with-msrv`, `--with-docs`, `--with-audit`, `--with-deny`, or `--with-artifacts` only when discovery proves they are appropriate.

   Current simit also manages the release maintainer OpenPGP trust root used by
   generated publish workflows. `simit init ci` should discover the signing key
   from `[release.signing].key`, `git config user.signingkey`, or
   `--maintainer-key`, then write `keys/maintainers.gpg`. If this fails, run
   `simit release trust status`; fix discoverable config with
   `simit release trust init` or validate committed state with
   `simit release trust check` before treating the key as missing.

   For Forgejo/Codeberg projects that use our self-hosted runner runner, keep simit's generated defaults unless project evidence requires an override: `runs-on: runner`, Forgejo checkout via `https://code.forgejo.org/actions/checkout@v4`, and Debian Rust containers (`rust:<MSRV>-bookworm` for current MSRVs; `rust:<MSRV>-trixie` only when that tag exists). Do not add per-workflow Node/git bootstrap steps or manual checkout; the runner runner bind-mounts the JS action runtime into job containers.

5. Validate generated output:
   ```sh
   simit init flake --check --diff
   simit release trust check
   simit init ci --platform <platform> --check --diff
   nix flake check --no-build
   ```

   Run the narrowest meaningful build or test after evaluation succeeds, such as `nix build`, `cargo test`, or the project-specific check exposed by the flake.

## Existing Flakes

When `flake.nix` already exists:

- Let `simit init flake` patch safe anchors first.
- Do not replace an existing flake wholesale unless the user asked for a reset and the current flake has no project-specific outputs to preserve.
- Preserve public output names, deployable packages, shells, overlays, formatter outputs, and release artifacts.
- After a successful patch, modularize only when it reduces real complexity or when `flake.nix` is large enough that future simit or project edits would become hard to review. Use the shared modularization reference ([flake-modularization.md](references/flake-modularization.md)) instead of inventing a different split.

## Failure Handling

If `simit init flake` cannot patch a flake, do not hand-merge from memory. Run:

```sh
simit init flake --print
```

Then compare the generated template against the existing flake and either apply a minimal, justified manual integration or report the specific missing/ambiguous anchor that blocks automation.

If `simit init ci --check` fails on the maintainer trust root, use
`simit release trust status|init|check`; do not manually export
`keys/maintainers.gpg` unless simit itself reports that no configured key can be
discovered or exported. For other workflow drift, regenerate with the same
options used by the existing workflow, then inspect the diff before reporting
done.
