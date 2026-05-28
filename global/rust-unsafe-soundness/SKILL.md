---
name: rust-unsafe-soundness
description: Review every unsafe block for soundness — require SAFETY comments that name upheld invariants and hunt for UB (bad transmutes, aliasing &mut, uninitialized reads, OOB get_unchecked, FFI ABI/lifetime errors, bogus Send/Sync). Use when asked to audit unsafe code, justify or repair SAFETY comments, find undefined behavior, run miri, or verify unsafe soundness. Part of the rust-ultra Rust improvement arsenal.
---

# Rust: Unsafe Soundness Review

Review every `unsafe` block, `unsafe fn`, and `unsafe impl` for soundness — code is unsound if any safe caller can trigger undefined behavior:
1. Inventory each unsafe site; for each, write down the precise invariants the surrounding code relies on (validity, alignment, exclusive access, lifetime, initialization, thread-safety).
2. Confirm the block is actually necessary — if a safe API expresses the same thing (slice indexing, `split_at_mut`, `bytemuck`/`zerocopy` casts), prefer it and remove the unsafe.
3. For each that stays, verify the named invariants genuinely hold at every reachable call site, not just the happy path.
4. Hunt UB by category: `transmute` between layout-incompatible types or into invalid bit patterns (e.g. `bool`, `char`, enums, references); creating overlapping `&mut`/`&` through raw pointers (aliasing violation); reading `MaybeUninit` before it is fully initialized; `get_unchecked`/`get_unchecked_mut` with indices not provably in bounds (an out-of-bounds read/write here is UB, not a panic — bounds-as-panic is rust-panic-audit's lane); dangling or misaligned pointer dereferences; sending non-`Send`/`Sync` types across threads via hand-written `unsafe impl Send`/`Sync`.
5. For FFI (`extern`, exported symbols), verify ABI match, pointer validity and ownership transfer, null handling, lifetime of borrowed buffers, and that no `panic!` unwinds across the boundary (use `catch_unwind` at the edge, or declare `extern "C-unwind"` only when the foreign side truly expects unwinding).
6. Repair: add or fix a `// SAFETY:` comment directly above each block stating exactly why each invariant holds here; or fix the unsoundness by tightening the precondition, narrowing the unsafe scope, or switching to a safe alternative.
7. If a precondition cannot be guaranteed internally, make the function itself `unsafe fn` and document `# Safety` requirements for its callers rather than papering over it.
8. Never delete an `unsafe` block blindly to silence a lint, and never weaken a correct, well-encapsulated abstraction just to remove the keyword — a sound unsafe block with a good SAFETY comment is the right outcome.
9. Re-check the build and tests; where miri is available, run it on the affected tests to catch latent UB.

Commit with a summary of which unsafe blocks were documented, which were replaced with safe code, and which unsoundness bugs were fixed.

## Rust specifics

Add a `// SAFETY:` comment immediately above every `unsafe { }` and `unsafe impl`. Replace layout casts with `bytemuck`/`zerocopy` rather than `mem::transmute` where the trait bounds apply. Call `MaybeUninit::assume_init` only after the value is fully initialized; prefer `MaybeUninit::write` over assigning through a raw pointer. Prefer checked indexing and `slice::split_at_mut` over `get_unchecked`/raw pointers unless a profile justifies it. Treat `transmute`, `*const`/`*mut` deref, `slice::from_raw_parts`, and `Box::from_raw` as high-risk. Run `cargo check --all-targets` and `cargo test`; if available, run `cargo +nightly miri test` on the affected tests.

## Relevance heuristic (preflight)

Only relevant when the crate contains `unsafe`. Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **5** as "relevant":

| Pattern | Weight |
|---|---|
| `unsafe ` | 3 |
| `transmute` | 5 |
| `from_raw` | 4 |
| `MaybeUninit` | 3 |
| `::ptr::` | 3 |
| `get_unchecked` | 3 |

If the crate has zero `unsafe` blocks, skip this concern entirely.
