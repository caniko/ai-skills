---
name: rust-crate-release-reference
description: "Shared Rust crate release readiness doctrine for crates.io preparation and chaperoned release execution. Use as a reference from Rust crate release skills when Codex needs common rules for required sources, simit-managed release infrastructure, changelog requirements, strict validation gates, blocker classification, and publish boundaries."
---

# Rust Crate Release Reference

Shared reference — not user-invokable on its own; loaded by the `rust-crate-*` release skills.

## Source Integrity

Do not fabricate release metadata, license text, crate descriptions, API behavior, credentials, publication state, changelog facts, or legal text. Discover required facts from the repository, upstream package metadata, Codeberg/crates.io/docs.rs, or user-provided authoritative sources.

If a required source is missing or invalid, stop and report:

- the missing artifact or source;
- why it is required;
- the upstream producer or maintainer who must provide it;
- the exact command or workflow to regenerate or supply it;
- the validation command that proves it is fixed.

## Simit Infrastructure

Use `simit` as the canonical generator before hand-writing or repairing Rust crate release flakes and CI. Load `../simit-rust-crate-release-init/SKILL.md` whenever release work touches `flake.nix`, `flake.lock`, `nix/`, `.forgejo/workflows/`, or `.github/workflows/`.

Before running release hooks or validating generated infrastructure, ensure the repository has simit-managed release infrastructure unless it has an explicit documented policy against it:

```sh
simit init flake
simit init ci --platform <platform>
```

Current simit owns the release maintainer OpenPGP trust root. `simit init ci`
discovers the release signing key from `[release.signing].key`,
`git config user.signingkey`, or `--maintainer-key`, writes
`keys/maintainers.gpg`, and blocks only when no exportable key is available.
Do not manually export or synthesize `keys/maintainers.gpg` before trying the
simit surface:

```sh
simit release trust status
simit release trust init
simit release trust check
```

Choose `<platform>` from repository evidence:

- `forgejo` for Codeberg or Forgejo-hosted repositories, including `.forgejo/workflows/`.
- `github` for GitHub-hosted repositories, including `.github/workflows/`.

If `simit` is not on `PATH`, use the local simit checkout when available:

```sh
cargo run --manifest-path ~/canix/Projects/simit/Cargo.toml -- <simit-args>
```

If neither `simit` nor the local checkout is available, report the missing tool as a blocker and include the command that should work once it is available.

Validate generated infrastructure with:

```sh
simit init flake --check --diff
simit release trust check
simit init ci --platform <platform> --check --diff
```

Do not substitute bespoke release flakes or workflows when `simit init flake` or `simit init ci` can generate or check the required structure.

## Changelog Requirement

Always require a changelog. A releasable Rust crate must have a `CHANGELOG.md` or a clearly documented equivalent that documents repository-owned changes being released and uses the correct crate version from `Cargo.toml`.

Prefer Keep a Changelog style when creating or repairing a changelog. Use repository facts such as git diffs, commits, tags, release metadata, and `Cargo.toml`; never invent release notes or silently substitute unknown change history.

Before release gates:

- Ensure the changelog is included in the crate package when `Cargo.toml` has an `include` allowlist.
- Confirm the release entry version matches `package.version` in `Cargo.toml` when preparing a release.
- If the version is not being released yet, confirm unreleased repository changes are documented under `[Unreleased]`.
- Confirm entries describe user-visible or release-relevant changes, including fixes made during release prep or chaperone work.
- Confirm compare links, dates, and headings are correct when the project uses Keep a Changelog.
- If the project provides `simit changelog check`, run it and fix repository-owned failures.

## Release Bar

A strict release candidate must have:

- valid Cargo package metadata and reproducible package contents;
- a license expression plus matching license text or a valid `license-file`;
- a README suitable for crates.io rendering;
- public API rustdoc that builds with warnings denied;
- a committed Rust lockfile when CI or Nix depends on exact dependency resolution;
- formatter, clippy, tests, docs, package dry-run, and dependency policy checks;
- CI that exercises the same checks and uses the correct project host and runner;
- clear human steps for credentials, Actions enablement, tag creation, and publish.

Prefer project wrappers and generated Nix checks when present. Otherwise run the raw equivalents:

```sh
nix flake check --keep-going --print-build-logs
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- --deny warnings
cargo test --all-features
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features
cargo package --list
cargo publish --dry-run
cargo deny check
cargo audit
```

If ambient Cargo is unavailable, use the simit-managed Nix dev shell or checks once available.

## Failure Classification

Treat these as repository-owned and fix them when possible:

- Rust compile, fmt, clippy, test, doctest, rustdoc, and packaging failures.
- Missing or stale generated simit flake/CI files.
- Missing, stale, mis-versioned, or incomplete changelog entries when the required facts are available from the repository.
- `Cargo.toml` metadata errors that can be corrected from repository facts.
- README examples or docs that do not compile or no longer match the public API.
- Nix evaluation/build errors caused by project configuration.
- CI workflow syntax or runner mismatch caused by repository files.
- Missing or stale `keys/maintainers.gpg` that simit can regenerate (see Simit Infrastructure for the discovery sources and `simit release trust` commands).

Treat these as blockers unless the user or an authoritative source provides the missing input:

- Missing license choice or custom legal text.
- Missing crates.io credentials or owner permissions.
- Unknown release notes/changelog facts.
- Missing changelog source facts when the release contents cannot be reconstructed from repository history, tags, diffs, or maintainer-provided notes.
- Unknown MSRV or compatibility promise when no repo evidence exists.
- Security/advisory policy decisions that require maintainer judgment.
- Missing generated artifacts whose upstream producer is outside the repo.
- Missing release signing key, but only after the `simit release trust` checks in Simit Infrastructure confirm simit cannot discover/export any configured key.

If the active release skill is responsible for end-to-end publication on a Codeberg/Forgejo-hosted project, continue past dry-run through tag push, CI-triggered publish, and external verification that the new version is live on crates.io. Do not publish from the local shell when the repository's publish workflow is the intended path. Stop only for real external blockers such as broken remote workflow configuration, missing remote secrets, network failure, registry rejection, or unverifiable publication state.
