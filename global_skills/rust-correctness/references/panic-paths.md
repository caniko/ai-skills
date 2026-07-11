# Panic-Path Profile

Audit non-test code for runtime indexing and slicing, integer overflow,
lossy casts, divide-by-zero, invalid assertions on external input, and
unreachable assumptions.

- Replace unprovably bounded indexing with `.get` or explicit bounds checks.
- Use deliberate `checked_*`, `saturating_*`, or `wrapping_*` semantics for
  arithmetic; handle conversion errors with `TryFrom`/`TryInto`.
- Guard runtime divisors and the signed minimum divided by `-1` case.
- Convert assertions on network, file, CLI, or deserialized input into errors.
- Keep genuine internal invariant panics only with a nearby invariant comment.

Do not change test code, or conflate this profile with unwrap/expect handling
or general precondition validation. Run `cargo clippy --all-targets` and
`cargo test` after changes.
