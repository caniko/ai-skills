---
name: nix-input-hygiene
description: Audit flake input hygiene including follows graphs, duplicate nixpkgs pins, path inputs, lock drift, manual pins, update blast radius, and cache-sensitive input choices. Use when updating, simplifying, or stabilizing flake inputs.
---

# Nix: Input Hygiene

## Goal

Keep inputs deliberate, reproducible, and cheap to update without collapsing intentional pins.

## Workflow

1. Inspect `flake.nix` and `flake.lock` for input families, follows edges, path inputs, manual pins, and duplicate nixpkgs sources.
2. Classify each duplicate as intentional compatibility/cache pin, local development input, or accidental drift.
3. Prefer follows for shared infrastructure inputs when consumers can safely share the same revision.
4. Preserve separate pins when binary cache matching, platform support, or upstream regressions require them.
5. Validate input-only changes with `nix flake lock --no-update-lock-file` style evals first; update locks only when requested.

## Nix Specifics

- Do not make a cache-sensitive input follow main nixpkgs if comments say the pin preserves binary cache hashes.
- Path inputs in committed locks should be treated as local-only unless the repository policy allows them.
- Record the blast radius of updating an input before running a broad flake update.

## Validation

Run the narrowest validation that proves the change:

- `nix eval .#<attr> --no-update-lock-file --accept-flake-config` for focused flake outputs.
- `nix flake check --no-build --no-update-lock-file --accept-flake-config` for broad evaluation when builds are expensive.
- `nix build .#<package> --no-link --no-update-lock-file --accept-flake-config` only when a build is necessary and affordable.
- Repository formatter check, usually `nix fmt -- --check`, `treefmt --fail-on-change`, `alejandra --check .`, or the repo's documented equivalent.

If validation is blocked by a missing generated artifact, secret, external input, or unavailable tool, stop and report the missing producer plus the command that would regenerate it.

## Relevance Heuristic

Grep non-generated Nix files and multiply hits by weight. Treat a combined score >= **10** as relevant.

| Pattern | Weight |
|---|---|
| `inputs.` | 1 |
| `follows` | 1 |
| `nixpkgs` | 1 |
| `path:` | 4 |
| `git+file` | 4 |
| `flake = false` | 1 |
| `url =` | 1 |
