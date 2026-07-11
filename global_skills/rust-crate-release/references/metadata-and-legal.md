# Metadata, Legal, and Documentation Mode

Validate `name`, `version`, `edition`, `description`, license expression or
license file, canonical repository, README, docs.rs URL, rust-version,
keywords/categories, package include/exclude, feature policy, and docs.rs
metadata from repository evidence. Include intended source, examples, tests,
README, license, and changelog files in package allowlists.

The README must render on crates.io and include accurate installation,
dependency, API, documentation, and release-validation information. Do not
invent license text or missing release notes. Public docs must cover purpose,
arguments, returns, errors, panics, safety, examples, and feature visibility.

Validate with `cargo metadata --no-deps --format-version 1`, `cargo package
--list`, `cargo publish --dry-run`, and the rustdoc/doc-test commands from
`quality-gates.md`.
