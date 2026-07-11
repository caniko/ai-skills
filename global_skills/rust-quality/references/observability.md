# Observability Profile

Distinguish intentional CLI output from diagnostics. Replace committed
`println!`, diagnostic `eprintln!`, and `dbg!` with leveled structured
`tracing` or `log` calls, preserving the project's existing logging stack.
Instrument important entry points and spawned tasks, keep messages stable with
structured fields, redact secrets/PII, and use `warn!` for recoverable startup
issues. Initialize subscribers exactly once in binaries and avoid hot-loop
noise. Run compile/tests and confirm no stray `dbg!` remains.
