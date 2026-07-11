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

Use simit as the canonical generator before hand-writing release flakes or
workflows:

```sh
simit init flake
simit init ci --platform <platform>
simit release trust status
simit release trust init
simit release trust check
simit init flake --check --diff
simit init ci --platform <platform> --check --diff
```

Use `forgejo` for Codeberg/Forgejo and `github` for GitHub. If simit is not on
`PATH`, use the documented local checkout; if neither exists, report the
missing tool as a blocker. Do not manually synthesize maintainer trust roots.

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
