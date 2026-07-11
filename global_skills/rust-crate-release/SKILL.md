---
name: rust-crate-release
description: Prepare, validate, chaperone, and publish Rust crates through a strict crates.io workflow. Use for release readiness, Cargo metadata, changelog, docs, Nix or Forgejo release infrastructure, hook failures, versioning, tags, publication, and post-publish verification.
---

# Rust Crate Release

Load [policy.md](references/policy.md) first. Load only the mode references
needed for the current task:

- [metadata-and-legal.md](references/metadata-and-legal.md)
- [quality-gates.md](references/quality-gates.md)
- [infrastructure.md](references/infrastructure.md)
- [publishing.md](references/publishing.md)

## Modes

1. **Prepare:** inspect the repository, run the release audit script, repair
   metadata, README/license, changelog, public docs, package contents, and
   missing generated infrastructure.
2. **Validate:** run the strict quality and package gates. Stop on repository-
   owned failures only after fixing and rerunning the narrowest failed gate.
3. **Chaperone:** install or refresh simit hooks, classify each hook failure,
   fix repository-owned issues, and repeat until clean or a real upstream or
   external blocker remains.
4. **Publish:** confirm version/tag/changelog alignment, release credentials,
   CI trigger state, and remote workflow ownership; push the release trigger
   and verify the new version externally.

Do not run `cargo publish` locally for a Codeberg/Forgejo workflow whose CI
owns publication. Never paste credentials into files, logs, or chat.

Use `rust-quality` for general code-quality work, `rust-project-flake` for
project-specific crane changes, and the canonical simit/Forgejo/Pages skills
for generated or hosted integrations.

For canix-backed release credentials, load
[simit-canix-release-secrets.md](references/simit-canix-release-secrets.md)
before changing secret mappings.
