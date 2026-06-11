---
name: rust-breaking-upgrade
description: Upgrade a Rust crate or workspace across breaking dependency releases while preserving the most compatible Cargo dependency tree. Use when asked to move dependencies to latest major versions, handle upstream breaking changes, resolve version conflicts, modernize APIs after dependency upgrades, audit newly available crate features, or choose safer feature flags during a Rust dependency migration.
---

# Rust: Breaking Dependency Upgrade

Upgrade Rust dependencies across semver-breaking releases with Cargo as the source of truth for graph compatibility. Treat every version choice as provisional until `cargo` resolves it and the project builds under the required feature sets.

## Preflight

1. Locate the workspace root and read every relevant `Cargo.toml`, `Cargo.lock`, `.cargo/config*`, `rust-toolchain*`, release/CI scripts, and local path/patch/vendor overrides.
2. Capture the baseline before edits:
   - `cargo metadata --locked --format-version 1`
   - `cargo tree --locked --duplicates`
   - `cargo tree --locked -e features`
   - `cargo check --workspace --all-targets --locked`
3. If any foundational input is missing or invalid, stop. Report the missing artifact, why it is required, the likely upstream producer, the exact command or workflow to regenerate it, and the validation command that proves it is fixed. Do not fabricate versions, changelog contents, feature names, or compatibility claims.
4. Identify the requested upgrade target. If the user asks for "latest" or "most recent", verify current versions from authoritative sources before deciding target versions: crates.io metadata, crate repository releases, migration guides, and official docs.

## Dependency Resolution Workflow

Use Cargo to discover the most compatible tree instead of hand-picking versions in isolation:

1. Update semver-compatible dependencies first:
   - `cargo update`
   - Re-run `cargo check --workspace --all-targets`
2. For each direct dependency that needs a breaking upgrade, inspect current graph pressure:
   - `cargo tree -i <crate>`
   - `cargo tree -p <crate> -e features`
   - `cargo metadata --format-version 1`
3. Prefer the newest release that Cargo can resolve with the fewest duplicated major versions and the smallest feature surface. If a latest major causes graph conflicts, test the next compatible release in that major before retreating to an older major.
4. Change one dependency family at a time. A family includes the main crate, companion crates, derive/macros crates, adapters, and tightly coupled ecosystem crates.
5. After every family change, run:
   - `cargo update -p <crate>`
   - `cargo tree --duplicates`
   - `cargo tree -e features`
   - `cargo check --workspace --all-targets`
6. When multiple versions remain, use `cargo tree -d` and inverse trees to identify blockers. Upgrade or patch the blocker rather than forcing a duplicate unless the duplicate is harmless and temporary.

## Editing Rules

1. Prefer `cargo add <crate>@<version>` or `cargo upgrade`/`cargo upgrade --breaking` when `cargo-edit` is available. If those tools are unavailable, edit `Cargo.toml` directly and immediately let Cargo resolve with `cargo update` or `cargo check`.
2. Keep feature flags minimal and explicit. Disable default features only when the project already owns the replacement features or the upstream migration guide requires it.
3. Preserve workspace dependency centralization. If the workspace uses `[workspace.dependencies]`, update versions there and keep member manifests referencing workspace deps.
4. Keep compatibility shims small and local. Remove shims once all call sites use the new API.
5. Do not paper over compile errors with broad cfg gates, unused dependency removals, or weakened tests. Fix the API migration or report the blocker.

## Breaking API Migration

For each upgraded family:

1. Read the upstream changelog, migration guide, and release notes for all major versions crossed. Use official docs or repository releases first.
2. Search the codebase for old API symbols named by the migration guide.
3. Fix compile errors in dependency order: type changes, trait bound changes, feature gates, constructor/config changes, async/runtime changes, error type changes, then deprecations.
4. Run focused tests for touched modules before broader workspace tests.
5. Record any intentionally deferred upstream migration item with the exact reason and follow-up command/test.

## New Feature Adoption Review

After the project builds on the upgraded graph, identify whether new crate features should be used:

1. Compare old and new feature lists using:
   - `cargo tree -e features`
   - `cargo metadata --format-version 1`
   - crate docs and changelogs
2. Look for features that directly improve this codebase: safer defaults, native async/runtime integration, derived implementations that remove local boilerplate, better error types, no-std/std split, performance backends, serde/tracing integration, TLS/backend choices, or stabilized APIs replacing local compatibility code.
3. Adopt only features with a concrete local payoff. Do not enable broad convenience features just because they exist.
4. For every adopted feature, document the local reason and verify the relevant build matrix:
   - `cargo check --workspace --all-targets --no-default-features` when supported
   - `cargo check --workspace --all-targets --all-features`
   - `cargo test --workspace --all-targets`
5. If a useful new feature is not adopted, state the blocker: MSRV, compile time, binary size, platform support, transitive dependency risk, feature unification conflict, or missing local use case.

## Validation

Finish with a concise upgrade report:

- Dependency families upgraded and final versions
- Cargo commands used to resolve the final tree
- Remaining duplicate versions and why they are acceptable or blocked
- Breaking API changes made
- New features adopted or explicitly skipped
- Tests and checks run, including any failures or unrun gates

Prefer validation commands already used by the repository's CI. At minimum, run `cargo check --workspace --all-targets` and the most relevant tests for touched crates.
