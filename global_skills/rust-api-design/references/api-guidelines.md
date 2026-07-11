# Public API Guidelines Profile

Enumerate every item reachable from the crate root. Check naming, predictable
iterators, `Debug` and semantically appropriate common traits, `Send`/`Sync`,
`From`/`TryFrom`/`AsRef` conversions, ergonomic borrowed parameters,
`#[must_use]`, `#[non_exhaustive]`, sealed traits, and struct privacy.

Use `x()` rather than `get_x()` unless the getter is an indexing exception or
FFI compatibility requires it. Add derives only when their semantics and
field bounds fit. Redact secrets in manual `Debug` implementations. Keep
existing public compatibility with deprecated shims when appropriate, and
list every would-be-breaking change for human approval.

Re-derive the public API after each edit and run the library's compile/tests.
