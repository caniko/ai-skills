# Unwrap and Expect Profile

Audit `.unwrap()`, `.expect()`, and similar panicking calls outside tests.
For each occurrence, determine whether the invariant is actually guaranteed.
Replace recoverable failures with typed propagation or an intentional
best-effort path. In startup and cleanup code, prefer warning-and-continue or
self-healing for stale/corrupt optional state; reserve `expect` for a failure
that makes operation impossible and document that invariant.

Leave test unwraps alone. Run the relevant compile, lint, and test gates after
each batch.
