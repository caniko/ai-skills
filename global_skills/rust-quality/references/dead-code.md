# Dead-Code Profile

Find unused functions, types, traits, constants, modules, feature-gated
branches, stale test helpers, and unjustified `#[allow(dead_code)]` or
`#[deprecated]` remnants. Confirm reachability before deleting public or
feature-gated code. Run `cargo check --all-targets` and record warnings that
remain because a feature or downstream consumer is missing.
