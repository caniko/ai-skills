---
name: rust-api-guidelines
description: Audit a Rust library's public API against the Rust API Guidelines C-* checklist — naming, common-trait impls, conversion traits, must_use, and non_exhaustive — without breaking the existing surface. Use when asked to check API guideline conformance, fix get_ getters, add Debug/Default derives, adopt From/TryFrom conversions, mark builders #[must_use], or make a crate's public interface idiomatic (#[non_exhaustive] on error enums specifically is rust-error-architecture's lane). Part of the rust-ultra Rust improvement arsenal.
---

# Rust: Rust API Guidelines Conformance

Audit the public API of the crate against the Rust API Guidelines (the C-* checklist). Treat any non-additive signature or semantic change as a breaking release and flag it rather than silently applying it. Out of scope: rustdoc prose/sections (that is `rust-doc-public-api`), extracting new behavioral traits or dependency inversion (that is `rust-trait-design`), and error enum/type design (that is `rust-error-architecture`) — this skill only conforms the existing surface to the C-* checklist.

1. Enumerate the public surface first: every `pub` type, trait, fn, method, const, and re-export reachable from the crate root. Work only on items actually exported — private items are out of scope.
2. Naming (C-CASE): confirm types/traits/enums are UpperCamelCase and fns/methods/modules/locals are snake_case; rename private items freely, and flag public renames as breaking rather than applying them.
3. Getters (C-GETTER): find methods named `get_x` that return a field; rename to `x()` (no `get_` prefix) unless C++-style getter semantics or FFI require otherwise. The `get`/`get_mut` pair on indexable containers is the explicit exception — leave those alone.
4. Iterators (C-ITER / C-ITER-TY): a method producing an iterator over `&T` must be `iter`, over `&mut T` must be `iter_mut`, and over `T` must be `into_iter`; the iterator type and yielded item should be predictable from the method name.
5. Common traits (C-COMMON-TRAITS): every public type should `Debug`; derive `Clone`, `Default`, `PartialEq`, `Eq`, `Hash`, `PartialOrd`, `Ord` only where the semantics are sound and the field types support them. Derive eagerly when free; do NOT hand-roll an impl to force a derive that does not fit the type's meaning. (Deriving the std traits is API-guideline work — defining new behavioral traits is `rust-trait-design`.)
6. Debug obligation (C-DEBUG): add `#[derive(Debug)]` to public types that lack any `Debug` impl. Prefer a manual `Debug` that redacts when a field holds a secret, token, or password.
7. Send/Sync expectations (C-SEND-SYNC): confirm types that callers will move across threads are `Send`/`Sync`; if a stray `Rc`/`Cell`/raw pointer silently removed an expected auto-trait, note it — but do not add `unsafe impl Send`/`unsafe impl Sync` to paper over it.
8. Conversions (C-CONV-TRAITS): replace ad-hoc `from_x`/`to_x`/`as_x` methods that are really conversions with `From`, `TryFrom`, `AsRef`, `AsMut`, or `Into` impls; keep `From` infallible and use `TryFrom` when conversion can fail. Keep the old inherent constructor as a thin `#[deprecated]` shim if removing it would break callers.
9. Argument ergonomics (C-GENERIC): for functions that immediately convert or borrow an argument, take `impl AsRef<str>`/`impl AsRef<Path>`/`impl Into<String>` instead of a concrete owned type — but only where it does not complicate inference for callers.
10. `#[must_use]`: annotate builder methods that return `Self`, pure query methods whose only purpose is the returned value, and result-like types whose result must not be dropped; do not annotate methods invoked for their side effects.
11. `#[non_exhaustive]` (future-proofing): add it to public structs and enums that are likely to gain fields/variants, so adding them later is not breaking. Do NOT add it to types meant to be exhaustively matched or literally constructed by downstream code — adding it is itself a breaking change.
12. Sealed traits (C-SEALED): for traits that exist as extension points but must not be implemented downstream, seal them with a private supertrait; leave genuinely open traits unsealed.
13. Struct privacy (C-STRUCT-PRIVATE): public structs should expose data through methods rather than public fields where invariants exist; flag making an existing public field private as breaking.
14. After each change, re-derive the public surface and confirm no exported signature changed unintentionally. Group every item you could NOT fix without a breaking release into an explicit "would-be-breaking" list for the human.
15. Leave conforming items untouched — do not churn naming or add derives that gain nothing.

Commit with a summary of the C-* guidelines applied (naming, common traits, conversions, must_use, non_exhaustive, sealing) and a separate, clearly labeled list of any flagged breaking changes deferred to a human.

## Rust specifics

Add `#[derive(Debug)]` (or a redacting manual impl) to public types missing it; rename `pub fn get_x(&self) -> &T` to `pub fn x(&self) -> &T`. Add `#[must_use]` to builders and pure-result methods, and `#[non_exhaustive]` to growable public structs/enums. Implement `From`/`TryFrom`/`AsRef`/`Into` in place of ad-hoc converters; seal extension-point traits with a private supertrait. Verify the surface with `cargo public-api` (diff) and `cargo semver-checks` if available; otherwise capture the `cargo doc`-derived pub surface (or `rustdoc --output-format json` on nightly) before/after and diff manually. Run `cargo check --all-targets` and `cargo test` after each batch, and explicitly flag any change that is a breaking API change.

## Relevance heuristic (preflight)

Primarily for library crates (a `[lib]` target or `src/lib.rs`). Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **6** as "relevant":

| Pattern | Weight |
|---|---|
| `pub struct ` | 1 |
| `pub enum ` | 1 |
| `pub trait ` | 2 |
| `pub fn get_` | 2 |
| `pub fn ` | 1 |
