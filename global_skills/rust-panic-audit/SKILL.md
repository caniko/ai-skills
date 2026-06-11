---
name: rust-panic-audit
description: Audit non-test Rust code for arithmetic, indexing, slicing, and cast panics and replace them with checked operations or boundary validation. Use when asked to make code panic-free, harden indexing/slicing, prevent integer overflow, fix lossy casts, guard divide-by-zero, or audit a[i]/&s[a..b]/as-casts/checked arithmetic. Does NOT cover unwrap/expect (rust-unwrap-audit) or general precondition guards (rust-fail-fast). Part of the rust-ultra Rust improvement arsenal.
---

# Rust: Panic-Freedom Audit

Audit non-test code for panics that are NOT unwrap/expect — indexing, slicing, arithmetic, casts, and division:
1. Scan for slice/array indexing `a[i]` and range slicing `&s[a..b]` where the index or range comes from runtime data; for each, decide whether the bound is provably in range at that point.
2. Replace runtime-bounded indexing with `.get(i)` / `.get(a..b)` and explicitly handle the `None` case — propagate an error, clamp, or skip — rather than letting an out-of-range access abort the process.
3. Scan integer arithmetic (`+ - * <<`) on values derived from input, lengths, or accumulation; determine whether the operands can overflow (note `<<` panics in debug when the shift amount is ≥ the type's bit width). Replace with `checked_*` (and handle the `None`), `saturating_*`, or `wrapping_*` — choosing deliberately and stating which semantics the call site actually wants.
4. Find every `as` cast that narrows or changes signedness (e.g. `as usize`, `as u32`, `as u8`, `as i32`) where the source is signed, wider, or runtime-controlled. Replace lossy casts with `TryInto`/`TryFrom` and handle the conversion error; leave only casts that are provably lossless or intentionally truncating with a comment saying so.
5. Find division and remainder where the divisor can be zero; guard the divisor or use `checked_div`/`checked_rem` and handle the zero case. Also flag `i*::MIN / -1` and `i*::MIN % -1`, which panic.
6. Find `[T; N]` fixed-array access with a runtime index — same treatment as slice indexing.
7. Find `panic!`, `unreachable!`, `assert!`, `assert_eq!`, and `debug_assert!` that fire on external/untrusted input (network, files, CLI, deserialized data); convert those to returned errors. Assertions on genuine internal invariants may stay.
8. Where a panic genuinely encodes an unreachable invariant, keep it but document the invariant in a comment explaining why it cannot fire.
9. Preserve behavior for all valid inputs — checked operations must produce the identical result on the in-range/non-overflowing path; only the out-of-bounds path changes from abort to handled.
10. Do not touch test code, benches, or `unwrap`/`expect` (that is rust-unwrap-audit), and do not add general precondition guards beyond the panic sites you are removing (that is rust-fail-fast).

Commit with a summary of how many indexing, arithmetic, cast, and division panics were hardened and which were intentionally retained as documented invariants.

## Rust specifics

Prefer `slice.get(i)` / `slice.get(range)` over `slice[i]`; use `usize::try_from(x)?` instead of `x as usize` when `x` is signed or wider. Use `a.checked_add(b).ok_or(...)?` (and `checked_sub`/`checked_mul`/`checked_shl`) for fallible arithmetic, `saturating_*`/`wrapping_*` when those semantics are wanted, and `n.checked_div(d)` / `n.checked_rem(d)` for possibly-zero (or `MIN / -1`) divisors. Temporarily add `#![warn(clippy::indexing_slicing, clippy::arithmetic_side_effects, clippy::cast_possible_truncation, clippy::cast_sign_loss, clippy::cast_possible_wrap)]` to surface candidates. Run `cargo clippy --all-targets` and `cargo test` to confirm no behavior changed; if available, `cargo build` with `overflow-checks = true` on the release profile keeps overflow panics from being silently wrapped away.

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **6** as "relevant". Note: slice/array indexing (`a[i]`, `&s[a..b]`) is hard to grep — always scan manually in arithmetic-heavy or buffer-parsing code even when the score is low:

| Pattern | Weight |
|---|---|
| `as usize` | 1 |
| `as u32` / `as u64` / `as i64` / `as u8` / `as i32` | 1 |
| `checked_` / `saturating_` / `wrapping_` (already present) | 1 |
| ` / ` or `%` on runtime divisor | 2 |
| `[` indexing with a variable index | 2 |
| `&` slice `[a..b]` with runtime bounds | 2 |
