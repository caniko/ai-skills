---
name: nix-store-purity
description: Audit Nix code for impurity, absolute local paths, unpinned fetches, store leaks, dirty lock or update behavior, path inputs, and eval-time filesystem assumptions. Use when asked to make Nix builds reproducible, pure, cacheable, or safe for other machines.
---

# Nix: Store Purity

## Goal

Make evaluation and builds reproducible from declared inputs, without hidden dependencies on one workstation.

## Workflow

1. Search for absolute host paths, `builtins.pathExists`, `builtins.readFile`, path flake inputs, `builtins.getFlake`, and unpinned fetchers.
2. Classify each impurity as intentional local state, generated source, secret material, package source, or accidental workstation coupling.
3. Move reusable constants into pure data files or flake inputs. Keep runtime host paths behind options, not eval-time file reads.
4. For fetches, require pinned hashes or flake locks. Do not replace missing source data with guessed hashes.
5. Verify with `nix flake check --no-build --no-update-lock-file` or focused `nix eval` commands that do not rewrite locks.

## Nix Specifics

- Path inputs are acceptable only for explicitly local development flakes; call out non-portability.
- Avoid importing from `/nix/store` or user home paths in committed Nix.
- Use `--no-update-lock-file` during validation unless the task is specifically to update inputs.

## Validation

Run the narrowest validation that proves the change:

- `nix eval .#<attr> --no-update-lock-file --accept-flake-config` for focused flake outputs.
- `nix flake check --no-build --no-update-lock-file --accept-flake-config` for broad evaluation when builds are expensive.
- `nix build .#<package> --no-link --no-update-lock-file --accept-flake-config` only when a build is necessary and affordable.
- Repository formatter check, usually `nix fmt -- --check`, `treefmt --fail-on-change`, `alejandra --check .`, or the repo's documented equivalent.

If validation is blocked by a missing generated artifact, secret, external input, or unavailable tool, stop and report the missing producer plus the command that would regenerate it.

## Relevance Heuristic

Grep non-generated Nix files and multiply hits by weight. Treat a combined score >= **6** as relevant.

| Pattern | Weight |
|---|---|
| `builtins.getFlake` | 4 |
| `fetchTarball` | 4 |
| `fetchGit` | 4 |
| `builtins.fetchurl` | 3 |
| `/home/` | 3 |
| `/data/` | 3 |
| `path:` | 2 |
| `builtins.pathExists` | 2 |
