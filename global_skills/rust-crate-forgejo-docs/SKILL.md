---
name: rust-crate-forgejo-docs
description: "Add Forgejo/Codeberg Pages documentation for Rust crates preparing for crates.io. Use for docs-only mdBook sites, optional Zola landing plus docs, Nix packages.docs/site outputs, Pages workflow integration, and docs content aligned with crate README/rustdoc."
---

# Rust Crate Forgejo Docs

## Required References

For docs-only sites, load [../forgejo-docs/SKILL.md](../forgejo-docs/SKILL.md). For a landing page plus docs, load [../forgejo-site/SKILL.md](../forgejo-site/SKILL.md). When adding docs as part of Rust crate release prep, also load [../simit-project-init/SKILL.md](../simit-project-init/SKILL.md) and keep any Nix or CI integration compatible with `simit init flake` and `simit init ci`.

## Default For Small Library Crates

Use docs-only mdBook unless the user asks for a marketing landing page. Serve mdBook at the Codeberg Pages root for the repository.

Required pages:

- Introduction and scope.
- Installation and quick start.
- Public API overview.
- Compatibility/behavior notes tied to actual tests and rustdoc.
- Release and maintenance commands.

Do not generate documentation from missing source material. If API behavior or legal semantics are unclear, stop and identify the missing upstream source.
