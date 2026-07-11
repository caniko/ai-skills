# Error Architecture and Messages Profile

For library boundaries, replace `String`, `Box<dyn Error>`, `anyhow`, `eyre`,
and ad-hoc formatted errors with named typed enums. Preserve source chains
with `#[source]`/`#[from]`, use one variant per genuinely distinct failure,
and mark exported error enums `#[non_exhaustive]`. Keep `anyhow`/`eyre` at
binary or internal glue boundaries when appropriate.

Do not confuse error architecture with message quality. Messages must say what
failed, identify the offending path or value, distinguish missing/corrupt/
expired/unreadable states, and retain underlying causes. Improve wording
without changing error types or control flow when that is the requested scope.
Leave already sound, source-preserving error designs alone.
