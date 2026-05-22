---
name: rust-crate-release-prep
description: "Orchestrate strict Rust library crate readiness for crates.io using simit-managed release infrastructure. Use when preparing, auditing, or repairing a Rust crate before first publish or release: Cargo metadata, license/readme, rustdoc/docs.rs, Nix tooling, quality gates, Forgejo CI/Pages, cargo package dry-run, and final human-in-the-loop publish workflow."
---

# Rust Crate Release Prep

## Core Rule

Load `/home/can/.agents/skills/rust-crate-release-reference/SKILL.md` first and apply its shared source-integrity, simit infrastructure, changelog, release-bar, validation, blocker-classification, and publish-boundary rules throughout release prep.

## Component Skills

Load only the component skills needed for the current repository state:

- `/home/can/.agents/skills/rust-crate-release-reference/SKILL.md` for common release readiness doctrine.
- `/home/can/.codex/skills/simit-project-init/SKILL.md` for canonical `simit init-flake` and `simit init-ci` release infrastructure.
- `/home/can/.agents/skills/rust-crate-release-chaperone/SKILL.md` for installing simit hooks, running release hooks, fixing hook failures, and repeating validation until clean.
- `/home/can/.agents/skills/rust-crate-manifest-metadata/SKILL.md` for `Cargo.toml`, package contents, docs.rs metadata, keywords/categories, and dependency policy.
- `/home/can/.agents/skills/rust-crate-legal-readme/SKILL.md` for license files and release-facing README content.
- `/home/can/.agents/skills/rust-crate-rustdoc/SKILL.md` for public API docs and docs.rs readiness.
- `/home/can/.agents/skills/rust-crate-nix-release-tooling/SKILL.md` for crane-based flake/dev-shell/checks.
- `/home/can/.agents/skills/rust-crate-quality-gates/SKILL.md` for fmt, clippy, tests, docs, deny/audit, and package checks.
- `/home/can/.agents/skills/rust-crate-forgejo-release-ci/SKILL.md` for Codeberg-hosted CI on the runner runner.
- `/home/can/.agents/skills/rust-crate-forgejo-docs/SKILL.md` for Codeberg Pages documentation.
- `/home/can/.agents/skills/rust-crate-publish-workflow/SKILL.md` for final publish dry-run, tag, owner/token, and `cargo publish`.

## Workflow

1. Inspect first: `Cargo.toml`, `Cargo.lock`, `README*`, `LICENSE*`, `src/`, docs, CI, Nix files, remotes, default branch, and `cargo metadata` if Cargo is available.
2. Run `scripts/audit_rust_crate_release.py <repo>` early to get a deterministic missing-artifact list.
3. Add the minimum release infrastructure needed for the crate. For flake or CI work, run `simit init-flake` and/or `simit init-ci --platform <platform>` first, then inspect the diff and make only project-specific follow-up edits that simit does not cover. Let simit generate the release maintainer trust root; use `simit release trust status|init|check` instead of manually exporting `keys/maintainers.gpg`.
4. Validate through the project toolchain. For active release execution, use the release chaperone skill to install hooks, run the hooks, fix repository-owned failures, and rerun validation. Prefer simit's check modes (`simit init-flake --check --diff`, `simit release trust check`, `simit init-ci --platform <platform> --check --diff`) plus the generated Nix/dev-shell checks when present. If ambient Cargo is absent, use Nix/dev-shell once available.
5. Stop at `cargo publish --dry-run` unless the user explicitly asks to publish and credentials are available.
