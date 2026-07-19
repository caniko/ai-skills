# Public API Guidelines Profile

Enumerate every item reachable from the crate root. Check naming, predictable
iterators, `Debug` and semantically appropriate common traits, `Send`/`Sync`,
`From`/`TryFrom`/`AsRef` conversions, ergonomic borrowed parameters,
`#[must_use]`, `#[non_exhaustive]`, sealed traits, struct privacy, and whether
the public surface exposes storage-oriented or orchestration-oriented shapes
that should become domain APIs.

Use `x()` rather than `get_x()` unless the getter is an indexing exception or
FFI compatibility requires it. Add derives only when their semantics and
field bounds fit. Redact secrets in manual `Debug` implementations. Keep
existing public compatibility with deprecated shims in compatibility mode. In
Rust-ultra modernize mode, apply justified breaking API improvements, migrate
all in-repository consumers, and provide a downstream migration table. Do not
wait for separate approval already granted by the modernize invocation.

Re-derive the public API after each edit and run the library's compile/tests.
