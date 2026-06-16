---
name: rust-type-safety
description: Apply zero-cost abstractions and type-level safety improvements across a Rust codebase — newtypes, typestates, enums over strings/bools, borrowed over owned, static dispatch. Use when asked to make illegal states unrepresentable, wrap primitives in newtypes, replace stringly-typed APIs, or tighten compile-time guarantees. Extracted from the yee-haw housekeeping catalog (ConcernId::TypeSafety).
---

# Rust: Type Safety

Review the codebase and systematically apply zero-cost abstractions and type-level improvements:
1. Wrap domain-specific primitives in newtypes — IDs, paths, keys, sizes, durations —
   so the type system prevents mixing them up
2. Refactor runtime state flags into compile-time states using typestates
   where builder or state-machine patterns exist
3. Replace string parameters that represent a fixed set of values with enums;
   look for functions that match on string values or compare strings to known constants
4. Replace unnecessary owned types with borrowed or copy-on-write types where ownership is not needed
5. Use smaller collection types for predictably small collections (≤8 elements)
6. Use static dispatch where the concrete type is known at the call site
7. Replace multiple boolean parameters with descriptive enums for readability
8. Do not refactor types that are part of a serialization boundary unless internal-only

**Choose integer types by semantic domain, not bit-width convention.** A value that is always non-negative (TTL, count, size, timeout) should use an unsigned type — prefer `u32` over `u64` unless the full 64-bit range is actually reachable. When the value must cross a boundary that expects a different type (e.g. an API that takes `i64` for timestamps), design the field's type so the conversion is a provably safe widening: `u32 as i64` always fits; `u64 as i64` silently loses values above `i64::MAX`. A `u32` field is also wide enough for any reasonable TTL, interval, or retry count — reserve `u64` for values that genuinely need the extra range.

**Design serialization formats for unambiguous identity.** When converting domain names to environment variable names, avoid lossy mappings that cause collisions (e.g. folding `-`, ` `, `_` all to `_`). Use lossless serializations (`raw`, `json`) for canonical reference and document the collision risk of lossy formats.

Verify compilation frequently to maintain guarantees.
Summarize the memory and performance implications of your refactors when committing.

## Rust specifics

Wrap domain-specific primitives in tuple structs (newtypes).
Use PhantomData for typestates.
Replace `Vec` for predictably small collections with `SmallVec` or fixed arrays (≤8 elements).
Convert `Box<dyn Trait>` to `impl Trait` for static dispatch where concrete type is known.
Use `NonZero*` for IDs and counts that are never zero.
Choose integer types by semantic domain: use `u32` (not `u64`) for always-positive bounded values like TTL, intervals, retry counts, and sizes — this makes boundary conversions like `u32 as i64` provably safe.
Use `u64` only when the full 64-bit range is actually needed; use `i64` only when negative values are semantically meaningful.
For config-derived values that must cross an `i64` boundary (deadlines, offsets), prefer `u32` as the config type so the `as i64` cast is a safe widening.
Do not refactor types with serde Serialize/Deserialize unless the format is internal-only.
Run `cargo check --all-targets` frequently to maintain compile-time guarantees.

## Relevance heuristic (preflight)

No grep-based heuristic in the catalog — this concern is qualitative and applies to most
codebases. Run it whenever type-level hardening is requested.
