---
name: rust-crate-legal-readme
description: "Prepare legal files and crates.io-facing README content for Rust crate releases. Use when adding or auditing LICENSE/COPYING files, Cargo license expressions, README install examples, API examples, docs/source links, release commands, and missing-source blocking behavior."
---

# Rust Crate Legal Readme

## License

Match the manifest exactly. If `Cargo.toml` declares `license = "Apache-2.0"`, add the official Apache-2.0 text unless the repository already has a valid `license-file`. For dual licensing, include each referenced license file and make the SPDX expression match.

Do not synthesize custom legal terms. If a required license source is unavailable, stop and request the upstream legal source or a repository policy decision.

## README

The README must render correctly on crates.io and include:

- One-paragraph crate purpose.
- `crates.io` dependency snippet.
- Git/tag fallback only if it is still needed before publication.
- Minimal compiling usage example.
- Links to docs.rs and canonical source repository.
- Supported feature/license/API summary.
- Validation commands used for release readiness; when release infrastructure is in scope, document the simit check-mode triad from the Simit Infrastructure section of `../rust-crate-release-reference/SKILL.md`.

Keep README claims aligned with actual public API and tests. Do not invent users, benchmarks, compatibility guarantees, or legal interpretations beyond what the code documents.
