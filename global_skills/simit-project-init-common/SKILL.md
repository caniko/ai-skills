---
name: simit-project-init-common
description: Shared non-invokable contract for Simit project initialization. Loaded by Simit Python and Rust init skills for command resolution, generated-file ownership, blocker handling, and common validation.
---

# Simit Project Init Common

This reference is not a user workflow. Load it from a Simit initializer before
running generators so all variants share the same source-integrity and
generated-file rules.

When the initializer is being run from canix, also load
[canix-structure-reference](.skillnet/deps/canix-structure-reference/SKILL.md) before
resolving the local Simit checkout. Canix owns project paths; Simit owns only
its generated feature surfaces.

## Command resolution

Use the installed binary when available:

```sh
simit --help
```

For unreleased local Simit changes, use the checkout without changing the
target project:

```sh
cargo run --manifest-path /data/nvme0/can/canix/projects/repos/owned/codeberg.org/caniko/simit/Cargo.toml -- <simit-args>
```

Never hand-write a generated flake or workflow while the installed command can
express the requested surface. Before using optional flags, check the exact
installed `simit ... --help`; if a required option is absent, preserve the
generated defaults and report the upstream capability gap.

## Discovery and ownership

Inspect the project root, VCS state, manifests, existing flake, `simit.toml`,
Nix files, and existing workflows before generation. Preserve public outputs,
project-specific runtime policy, and unrelated worktree changes. Use
`--scope hooks-only` for an existing project-owned flake when Simit should own
only hook/pre-commit wiring.

Preview before applying and check after applying:

```sh
simit init flake --print
simit init flake --check --diff
simit init ci --platform <platform> --check --diff
```

For a release project, keep verification CI separate from the generated
multi-channel release workflow (`simit init release`). Release trust roots and
publish credentials belong to the release initializer only.

## Blockers

Stop instead of fabricating package names, runners, workflow targets, outputs,
keys, or artifacts. Report the missing input, why it is required, the upstream
producer or regeneration command, and the validation command that proves
recovery.

If a generator cannot patch an existing file, use `simit ... --print`, compare
the generated template with the project-owned file, and either make a minimal
source-backed integration or report the missing/ambiguous anchor.

If a Git-backed flake cannot see a generated path, report the path and use
`git add -N <path>` only for that path before rerunning validation.

Read [flake-modularization.md](references/flake-modularization.md) only after
generated output is valid and the flake is complex enough to justify a split.
