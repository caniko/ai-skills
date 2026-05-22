---
name: rust-crate-publish-workflow
description: "Execute the final Rust crates.io publish workflow after simit-managed release checks. Use for version/tag alignment, package archive inspection, release notes, git tags, remote pushes, Codeberg/Forgejo CI-triggered publication, and post-publish verification."
---

# Rust Crate Publish Workflow

## Pre-Publish Gate

Before actual publish, require:

```sh
git status --short
simit init-flake --check --diff
simit release trust check
simit init-ci --platform <platform> --check --diff
cargo package --list
cargo publish --dry-run
```

Use the platform that matches the repository host (`forgejo` for Codeberg/Forgejo, `github` for GitHub). If the project intentionally has no simit-managed flake or CI, document that repository policy explicitly before falling back to Cargo-only release gates. Also confirm the repository tag policy, version in `Cargo.toml`, changelog/release notes if the project has them, release signing trust-root status, and CI status for the exact commit.

## Publish Ownership

This skill owns the final publish once release gates pass. Do not stop at dry-run when repository state allows the release to complete.

For Codeberg/Forgejo repositories, do not run `cargo publish` from the local shell. Push the validated release commit and tag, let the configured publish workflow perform the upload, and verify the result from crates.io afterward.

If the repository does not have a working CI publish path, or the publish workflow lacks the required secret/configuration on the remote host, treat that as an external blocker and report the exact remote workflow or secret that must be fixed. Never paste tokens into files, CI logs, or chat.

If the publish workflow verifies signed tags and `keys/maintainers.gpg` is missing or stale, run `simit release trust init` or `simit init-ci --platform <platform>` rather than manually exporting GPG material. Block only if simit cannot discover/export `[release.signing].key`, `git config user.signingkey`, or an explicit `--maintainer-key`.

Recommended final sequence for Codeberg/Forgejo:

```sh
cargo package --list
cargo publish --dry-run
git tag -s v<version> -m "v<version>"
git push origin <default-branch> v<version>
cargo search <crate-name> --limit 1
```

Adjust branch names and tag naming only after confirming the repository default branch and local repository convention. If the project uses an unprefixed semver tag instead of `v<version>`, follow the repository convention consistently across commit, push, CI trigger rules, and publish verification.

## Verification

After the release push, verify publication from an external source instead of assuming success from the tag push alone. Prefer one or more of:

```sh
cargo search <crate-name> --limit 1
cargo info <crate-name>
curl -fsSL https://crates.io/api/v1/crates/<crate-name>
```

Also inspect the remote publish workflow outcome when available. If crates.io propagation is delayed, keep checking until the new version appears or there is a clear timeout/policy reason to stop, and report exactly what was observed.
