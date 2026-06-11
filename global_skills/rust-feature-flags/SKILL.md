---
name: rust-feature-flags
description: Audit Cargo feature-flag hygiene so features stay additive, defaults are deliberate, optional deps are gated correctly, and the crate builds under every feature combination. Use when asked to clean up feature flags, fix cfg(feature) typos, make features additive, audit default features, gate optional dependencies, or verify --no-default-features / --all-features builds. Part of the rust-ultra Rust improvement arsenal.
---

# Rust: Cargo Feature Hygiene

Audit the crate's feature surface for additivity, gating correctness, and buildability:
1. Enumerate every entry under `[features]` plus every dependency marked `optional = true`, and build a map of feature -> what it enables (other features, `dep:` activations, cfg-gated code).
2. Verify each feature is ADDITIVE: enabling it must only ADD API or behavior, never remove, replace, or break it. Flag any pair of features that are mutually exclusive, that change a function signature/return type, or that fail to compile when enabled together — these are hygiene bugs, not design choices to preserve.
3. Audit the `default` set: keep it minimal but useful. Move heavy, optional, or environment-specific functionality out of `default`. Do NOT silently shrink or grow the default set — any change to defaults is a compatibility event; flag it explicitly with the downstream impact before making it.
4. For each optional dependency, confirm it is activated via `dep:foo` (not implicit) and that its use is gated with `#[cfg(feature = "foo")]`; an optional dep referenced in unconditional code is a build break under `--no-default-features`. (You are auditing gating wiring, not whether the dep is unused — that is rust-deps-unused.)
5. Cross-check every `#[cfg(feature = "x")]` and `#[cfg_attr(feature = "x", ...)]` in sources against the declared `[features]` keys: a cfg naming a feature that does not exist is a key MISMATCH (typo) — it compiles to always-off code. Fix the typo or delete the orphaned branch. (Code that is correctly gated but simply never enabled is rust-dead-code's lane, not yours.)
6. Cross-check the other direction: every declared feature must be referenced somewhere (a cfg, another feature's enable list, or a `dep:`). A feature that gates nothing is a no-op promise to downstream — remove it or wire it up.
7. Confirm the crate compiles with no features, all features, and (where the powerset is tractable) representative combinations; resolve any combination that fails.
8. For docs.rs, gate feature-conditional public items with `#[cfg_attr(docsrs, doc(cfg(feature = "...")))]` so the rendered docs show which feature unlocks each item, and ensure the docs.rs metadata enables the right features. (This is the feature-visibility annotation only — writing the item's rustdoc prose is rust-doc-public-api.)
9. Document the feature set itself: a table/list of each feature, what it enables, and whether it is on by default, in the crate-level doc comment or README. (Limit this to the feature LISTING; per-item API docs belong to rust-doc-public-api.)
10. Leave intentional, additive, well-gated features alone — do not invent features, do not split a working feature for purity, and do not flip defaults to satisfy a checklist.

Commit with a summary of the cfg typos fixed, dead/no-op features removed, gating added, and any default-set change (called out separately with its compatibility impact).

## Rust specifics

Build the matrix: `cargo check --no-default-features`, `cargo check --all-features`, and if `cargo-hack` is available `cargo hack check --feature-powerset --no-dev-deps` for full combination coverage. Express optional deps as `dep:foo` in the feature's enable list and gate every use with `#[cfg(feature = "foo")]`. For docs.rs, add `#![cfg_attr(docsrs, feature(doc_cfg))]` at the crate root (this builds only on nightly / docs.rs), annotate items with `#[cfg_attr(docsrs, doc(cfg(feature = "...")))]`, and set `[package.metadata.docs.rs]` (e.g. `all-features = true` or an explicit `features = [...]`). Run `cargo test --all-features` to exercise feature-gated tests.

## Relevance heuristic (preflight)

Grep in `Cargo.toml` and sources; multiply hits by weight; treat a combined score ≥ **3** as "relevant":

| Pattern | Weight |
|---|---|
| `[features]` | 3 |
| `#[cfg(feature` | 1 |
| `optional = true` | 2 |
| `default = [` | 2 |

If the crate declares no `[features]` and no optional deps, skip this concern.
