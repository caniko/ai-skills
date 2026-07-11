---
name: rust-clippy
description: Resolve Rust Clippy diagnostics across a crate or workspace. Use when Codex is asked to fix all clippy errors, make cargo clippy pass, address Rust lint failures, repair CI lint failures from clippy, or clean up warnings treated as errors in Rust projects.
---

# Rust Clippy

## Workflow

1. Discover the repository's authoritative lint command before editing.
   - Check `README*`, `CONTRIBUTING*`, `justfile`, `Makefile`, `Cargo.toml`, `.cargo/config*`, `flake.nix`, CI workflows, and project agent instructions.
   - Prefer the exact command used by CI or project docs.
   - If no project command exists, use `cargo clippy --workspace --all-targets --all-features -- -D warnings`.
   - In Nix projects, prefer the documented devshell or check command, such as `nix develop -c cargo clippy ...`, when required by dependencies.

2. Run the lint command and capture the real diagnostics.
   - Do not invent errors or work from memory.
   - If dependencies, generated sources, toolchains, or required environment inputs are missing, stop and report the missing artifact, why it is required, likely upstream producer, regeneration command, and validation command.
   - Keep the full output available while fixing; Clippy often prints machine-applicable suggestions and spans that are easy to lose.

3. Fix diagnostics by root cause.
   - Prefer code that is clearer and preserves behavior over adding `#[allow(...)]`.
   - Use `#[allow(clippy::...)]` only when the lint is intentionally false-positive or the local style is materially better than Clippy's suggestion. Add the narrowest possible allow at the smallest scope.
   - Avoid broad crate-level allows unless the project already uses that policy.
   - Do not change public behavior, serialization formats, CLI flags, database schemas, feature flags, or generated artifacts unless the diagnostic directly requires it.
   - Do not apply `cargo clippy --fix` or `cargo fix` blindly. It is acceptable only after inspecting the diagnostics and only when the edits are reviewable.

4. Iterate until the authoritative lint command passes.
   - Rerun the same command after each coherent batch of edits.
   - If a fix reveals new diagnostics, continue until there are no Clippy errors.
   - If formatting changed or the repo enforces formatting, run the project's formatter command, usually `cargo fmt --all`.

5. Validate and report.
   - Final validation must include the authoritative Clippy command passing.
   - Also run targeted tests when a lint fix changes behavior-bearing code, especially parsing, error handling, unsafe code, async/concurrency, arithmetic, or public API behavior.
   - In the final response, state the lint command used, test commands run, and any residual risk or command that could not be run.

## Triage Rules

- Treat `-D warnings`, `deny(warnings)`, `deny(clippy::...)`, and CI lint failures as errors to eliminate.
- Fix compiler errors before Clippy lints; Clippy output after compile failure may be incomplete.
- For workspace failures, identify whether diagnostics are in first-party crates, examples, benches, tests, build scripts, or generated code. Fix first-party source unless project policy says generated code should be regenerated.
- If multiple feature sets exist and CI runs several Clippy commands, validate all documented variants.
- When diagnostics are caused by dependency or toolchain version drift, do not pin or upgrade casually. Confirm the intended toolchain from `rust-toolchain*`, Nix, CI, or docs before changing versions.

## Common Fix Preferences

- Replace needless clones, borrows, collects, conversions, and matches with equivalent simpler code only after checking ownership and lifetimes.
- Use `is_empty`, `contains`, `unwrap_or`, `unwrap_or_else`, `matches!`, iterator adapters, and `Default` where they improve clarity and match local style.
- For numeric casts and conversions, preserve range behavior. Prefer `TryFrom`, explicit bounds checks, or type changes when truncation or sign loss is possible.
- For panic-related lints, avoid changing failure semantics silently. If replacing `unwrap` or `expect`, preserve useful error context.
- For async lints, verify lock lifetimes, cancellation behavior, and sendability instead of applying mechanical rewrites.
- For unsafe-related lints, keep the safety invariant explicit and local. Add or improve `SAFETY:` comments only when they state the real invariant.
