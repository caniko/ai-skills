---
name: rust-performance
description: Audit Rust code for avoidable allocations, clones, copies, and iterator round-trips, and tighten hot paths without changing behavior. Use when asked to reduce allocations, remove needless clones/to_vec/to_string, borrow to avoid a clone, preallocate capacity, reuse buffers, drop collect round-trips, or speed up hot loops. Part of the rust-ultra Rust improvement arsenal.
---

# Rust: Performance & Allocation Audit

Audit the codebase for avoidable allocations and copies, then tighten hot paths only where the win is clear and readability is preserved:
1. Find each `.clone()` and decide whether it is needed — replace it with a borrow (`&`), a move, or `Rc`/`Arc::clone` sharing only when the value is genuinely aliased; leave clones of `Copy` types and cheap small types alone.
2. Replace `.to_vec()`, `.to_string()`, and `String::from`/`Vec::from` round-trips that exist only to satisfy a signature; fix the signature instead (see Rust specifics) rather than papering over it at the call site.
3. Audit function signatures for owned parameters that are only read — change `&String` to `&str`, `&Vec<T>` to `&[T]`, and accept `impl AsRef<str>`/`impl AsRef<Path>` where callers pass varied owned/borrowed forms. Public-API borrowed-vs-owned *design* policy belongs to rust-type-safety; change a signature here only when it removes a real allocation.
4. Use `Cow<str>`/`Cow<[T]>` for values that are usually borrowed but occasionally owned, so the common path allocates nothing.
5. Add `Vec::with_capacity`/`String::with_capacity`/`HashMap::with_capacity` wherever the final size is known or cheaply bounded before a push loop; do not guess capacities you cannot justify.
6. Hoist allocations out of loops — reuse a single buffer with `.clear()` across iterations instead of allocating a fresh `String`/`Vec` each pass.
7. Remove iterator round-trips: do not `.collect()` into a `Vec` only to immediately re-iterate it; chain the adapters or pass the iterator through. Collect only when you need ownership, random access, or multiple passes.
8. Defer allocation on the hot path: when `format!`/`.to_string()`/`.to_owned()` feeds an error or rare branch, construct the string lazily inside that `Err`/`None`/`else` arm so the success path allocates nothing — this is purely about *when* the allocation happens, not the message wording (rust-error-messages) or error type (rust-error-architecture).
9. Prefer iterator adapters (`map`/`filter`/`zip`/`windows`) over manual index loops with bounds arithmetic where the result is at least as clear and the allocation/iteration cost is no worse.
10. Eliminate a needless heap allocation from `Box::new`/boxing a value (or `Box<dyn Trait>` over a single known concrete type) when no trait object is actually required — return the concrete type or `impl Trait`. Decide the broader static-vs-dynamic-dispatch *policy* under rust-type-safety; here, only remove the allocation when the win is real and the type is fixed at the call site.
11. Verify each change compiles and behaves identically before moving on; never alter observable behavior, output ordering, or error semantics in the name of speed.
12. Leave it alone when the path is cold, the change obscures intent, or the gain is unmeasurable — do not microbenchmark-chase, unroll loops, hand-pick allocators, or hand-tune what the compiler already optimizes.

Commit with a summary of which allocations/clones were eliminated and which hot paths were tightened.

## Rust specifics

Prefer `&str`/`&[T]` over `&String`/`&Vec<T>` in signatures; accept `impl AsRef<str>`/`impl AsRef<Path>` for flexibility.
Use `Cow<'_, str>` / `Cow<'_, [T]>` when a value is sometimes borrowed, sometimes owned.
Reach for `Vec::with_capacity(n)` / `String::with_capacity(n)` before push loops with a known bound; reuse buffers via `.clear()` in loops.
Drop `into_iter().collect()` round-trips — iterate with `iter()`/`iter_mut()` and chain adapters instead; use `extend` over a `map(...).collect()` into an existing buffer.
Use `Arc::clone(&x)`/`Rc::clone(&x)` (not `x.clone()`) so reference-count bumps read distinctly from deep copies.
Run `cargo check --all-targets` after each change and `cargo test` at the end. If a `cargo bench`/criterion harness is present, run it to confirm no regression; if `cargo flamegraph` or `cargo-llvm-lines` is available, use it to confirm a hot path before touching it — do not assume one.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **12** as "relevant":

| Pattern | Weight |
|---|---|
| `.clone()` | 1 |
| `.to_vec()` | 2 |
| `.to_string()` | 1 |
| `.collect()` | 1 |
| `&Vec<` | 2 |
| `&String` | 2 |
| `format!(` | 1 |
