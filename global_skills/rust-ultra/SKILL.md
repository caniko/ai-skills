---
name: rust-ultra
description: Orchestrate aggressive Rust workspace modernization with necessary breaking changes and in-repo migration. Use for deep audits, hardening, or whole-codebase quality work.
---

# Rust Ultra

Use this entrypoint for whole-codebase Rust work. Focused requests should load
the smallest matching domain skill directly.

## Workflow

1. Let the active harness own planning, delegation, and review; this skill is
   a router, not a second model lifecycle.
2. Read `references/foundation.md`, inspect the workspace, and load every
   matching focused skill: `rust-api-design`, `rust-correctness`,
   `rust-security`, `rust-quality`, and `rust-dependencies`.
3. Default to modernize mode for whole-codebase work. Migrate all
   in-repository callers, tests, examples, and documents when public shapes
   change. Use compatibility mode only when an external contract requires it.
4. Validate the narrowest affected Cargo/Nix gate after each change, then run
   the repository's documented full checks. Keep release work in
   `rust-crate-release` and flake infrastructure in `rust-project-flake`.

Focused skills own their procedures and evidence. This entrypoint only routes
the complete pass and reports unresolved findings, blockers, and validation.
