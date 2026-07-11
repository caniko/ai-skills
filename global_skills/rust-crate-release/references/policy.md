# Release Policy

Do not fabricate release metadata, legal text, credentials, changelog facts,
API behavior, publication state, or compatibility promises. Discover facts from
the repository, Git history/tags, Cargo metadata, upstream registry/docs, or
an authoritative maintainer source. If a required source is missing, report
the artifact, why it is required, its producer, the exact regeneration or
provisioning workflow, and the validation command that proves recovery.

Inspect `Cargo.toml`, `Cargo.lock`, `CHANGELOG*`, `README*`, `LICENSE*`, source,
tests, docs, CI, Nix files, remotes, tags, default branch, and current Git
state. Run `scripts/audit_rust_crate_release.py <repo>` early.

## Generated infrastructure

Load [`simit-rust-crate-release-init`](../../simit-rust-crate-release-init/SKILL.md)
for generated flakes, CI, release workflows, command capability detection,
and trust-root checks. It owns the current simit contract; do not hand-write
generated infrastructure or synthesize maintainer trust roots. If simit is
missing from `PATH` and its documented local checkout is unavailable, report
that missing tool as a blocker.

## Changelog and release bar

Require `CHANGELOG.md` or a documented equivalent. The entry must match the
Cargo version and be based on repository facts. A strict candidate requires
valid metadata, license text, README, warning-free rustdoc, lockfile policy,
fmt, Clippy, tests, docs, package, dependency-policy checks, matching CI, and
clear human credential/tag steps.

Classify compile, docs, metadata, packaging, Nix, hook, and generated-file
failures as repository-owned when the facts are available. Treat missing legal
choices, unknown release notes, credentials, signing keys after trust checks,
and maintainer policy decisions as blockers.
