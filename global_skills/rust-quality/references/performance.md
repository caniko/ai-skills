# Performance Profile

Measure or establish a credible hot path before changing it. Remove needless
clones, conversions, intermediate collections, and heap allocations; prefer
borrows, `Cow`, direct buffer writes, capacity reservation, iterator adapters,
and existing zero-copy buffer types. Change a signature only when it removes a
real allocation; broader owned/borrowed API policy belongs to
`rust-api-design`.

Leave cold, clear, or unmeasurable code alone. Verify behavior, compile/tests,
and benchmarks or profiling tools when available.
