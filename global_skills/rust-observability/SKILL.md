---
name: rust-observability
description: Audit runtime observability in Rust library and service code — replace stray println!/eprintln!/dbg! with leveled, structured tracing/log, add instrument spans to entry points, and keep secrets out of logs. Use when asked to improve logging, add tracing, instrument code, remove dbg!/println! diagnostics, add spans, or make a service observable. Part of the rust-ultra Rust improvement arsenal.
---

# Rust: Logging & Observability

Audit runtime observability across library and service code:
1. Find every `println!`, `eprintln!`, and `dbg!` outside test code and decide its true intent: diagnostic output or genuine CLI user-facing message.
2. Replace diagnostic output with a leveled macro at the right severity: `error!` for failures needing attention, `warn!` for recoverable anomalies, `info!` for lifecycle/boundary events, `debug!`/`trace!` for fine-grained diagnostics. Do not promote routine flow to `info!`.
3. **Use `warn!` for boot-time recoverable failures that the system can continue past.**  A stale cache file, undecryptable container, or missing optional resource at startup should produce a `warn!` and let the system continue — not `error!` (which implies operator attention is required) and certainly not `panic!` (which aborts).  Reserve `error!` for failures that genuinely degrade functionality.
4. Convert string interpolation into structured fields — emit `info!(user_id, %req_id, "handled request")` rather than baking values into the message; reserve the message for a stable human-readable label.
5. Add a span to important entry points and spawned async tasks so concurrent work is correlatable; skip large or sensitive arguments so the span stays cheap and safe.
6. Audit every field and message for secrets, tokens, credentials, or full PII and remove or redact them — observability must never become a leak. Scope this to what is emitted into logs/spans; auditing secrets stored in source or config is rust-security's lane, not yours.
7. Verify each binary initializes a subscriber exactly once at startup; do not initialize from library code, and do not initialize twice.
8. If the codebase already uses `log` and not `tracing`, stay on `log` and apply the same leveling and structure — do not introduce a second logging stack.
9. Remove `dbg!` entirely — it is never appropriate in committed library or service code.
10. Leave `eprintln!` in place only where it is a deliberate CLI message to the user (usage, prompts, human-facing errors), not diagnostics.
11. Do not add logging to hot loops, trivial getters, or per-iteration paths where it would create noise or measurable overhead — when output adds no diagnostic value, leave the code silent.

Do not change control flow or error handling beyond the logging itself.
Commit with a summary of how many statements were converted and which spans were added.

## Rust specifics

Use `tracing` macros (`error!`/`warn!`/`info!`/`debug!`/`trace!`) and `#[tracing::instrument]` on entry points and async tasks.
Drop big or secret args from a span with `#[tracing::instrument(skip(self, buf))]` to skip named args, or `#[tracing::instrument(skip_all)]` to record none (do not combine the two — `skip_all` already covers everything).
Use structured fields with sigils: `%value` for `Display`, `?value` for `Debug`, bare `name` for shorthand capture.
Initialize once in `main` with `tracing_subscriber` and an `EnvFilter` (e.g. `EnvFilter::from_default_env()`).
If only `log` is present, use its macros consistently and keep one facade.
Run `cargo check --all-targets`; ensure no stray `dbg!` remains (`cargo clippy`, if available, flags `clippy::dbg_macro` when that lint is enabled).

## Relevance heuristic (preflight)

Grep for each pattern, multiply hits by its weight, and treat a combined score ≥ **5** as "relevant":

| Pattern | Weight |
|---|---|
| `println!` | 2 |
| `eprintln!` | 2 |
| `dbg!` | 3 |
| `tracing::` | 1 |
| `log::` | 1 |
