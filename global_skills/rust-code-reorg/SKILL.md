---
name: rust-code-reorg
description: Reorganize a Rust project's file and module structure for human and AI readability — split oversized files, merge tiny ones, fix the module tree, break import cycles. Use when asked to restructure modules, split a 500+ line file, flatten deep nesting, or improve code organization without changing behavior. Extracted from the yee-haw housekeeping catalog (ConcernId::CodeReorg).
---

# Rust: Code Reorganization

This is a large, multi-step concern. The active LLM harness owns planning,
model/provider/effort selection, and dispatch. This skill supplies the
repository-specific reorganization procedure and verification gates; it does
not prescribe a model, agent count, or execution harness.

Reorganize the project's file and module structure for human and AI readability:

Phase 1 — Measure
1. List every source file with its line count
2. Identify files >500 lines (split candidates) and files <30 lines (merge candidates)
3. Map the current module tree and flag modules whose name does not match their content

Phase 2 — Split large files
4. For each file >500 lines, extract cohesive blocks into focused submodules:
   - One primary type or trait per file; associated implementations stay with their type
   - Group related free functions into a purpose-named submodule
   - Target 80–500 lines per file — small enough to fit in an LLM context window in full
5. Create a module entry point that re-exports the public API of each new submodule

Phase 3 — Merge tiny files
6. For each file <30 lines that is NOT a module entry point:
   - Merge its contents into the parent module or a sibling file with related responsibility
   - Remove the now-empty file and its module declaration

Phase 4 — Organize the module tree
7. Ensure the module tree mirrors the domain hierarchy:
   - Group related types, traits, and functions into cohesive directories
   - Flatten nesting beyond 3 levels
   - Move misplaced items to their logical module
   - When two modules have circular imports, extract shared behavior into a trait in a parent module to break the cycle
   - **Extract local helpers into shared methods on the type they operate on.**  If a module defines a `fn internal(...)` that constructs an `ErrorResponse`, move it onto `ErrorResponse` as a method rather than leaving it as a free function in the consuming module.  The rule: a function that only touches fields/methods of type `T` should live as an inherent method on `T`, not as a local helper in a module that happens to create `T` values.
8. Every module entry point must have documentation explaining its purpose
9. Add barrel exports at the project root for key public types

Phase 5 — Verify
10. Update all imports and re-export paths after every move
11. Verify the project compiles (all targets including tests) after every structural change
12. Run the test suite at the end to confirm no behavior changed
13. Ensure no circular dependencies between sibling modules

Do not alter business logic, function signatures, or test assertions — reorganization only.
Each commit should be a single atomic reorganization step (one split, one merge, or one move)
so that changes are easy to review.

## Rust specifics

Use `mod.rs` (or parent module) re-exports for new submodules.
Run `cargo check --all-targets` after every structural change to catch broken imports immediately.
Run `cargo test` at the end to confirm no behavior changed.
Ensure no circular dependencies between sibling modules.

## Relevance heuristic (preflight)

File-size based: this concern is relevant when the crate has files **>500 lines**
(split candidates) or **<30 lines** (merge candidates). Treat ≥ **3** such files as "relevant".
