---
name: nix-code-reorg
description: Reorganize Nix file and module structure for readability without changing behavior. Use when Nix files are oversized, tiny modules are excessive, flake outputs are crowded, or host and shared modules are difficult to navigate.
---

# Nix: Code Reorganization

## Goal

Make the Nix tree easier for humans and agents to inspect while preserving public outputs and option names.

## Workflow

1. Measure every `.nix` file and classify files over 500 lines as split candidates and files under 30 lines as merge candidates.
2. Split large files by cohesive responsibility: option schema, pure data construction, runtime script, package derivation, host service config, or output wiring.
3. Merge tiny files only when they are not useful module entry points or independent toggles.
4. Preserve import paths or update every import in one focused change. Keep public flake outputs and option names stable.
5. Run formatter and focused eval after each structural move.

## Nix Specifics

- Do not split generated hardware or disk files just because they are long.
- Keep incident-learned operational comments with the code they explain.
- Avoid moving secrets or stateful migration modules in the same pass as cosmetic reorg.

## Validation

Run the narrowest validation that proves the change:

- `nix eval .#<attr> --no-update-lock-file --accept-flake-config` for focused flake outputs.
- `nix flake check --no-build --no-update-lock-file --accept-flake-config` for broad evaluation when builds are expensive.
- `nix build .#<package> --no-link --no-update-lock-file --accept-flake-config` only when a build is necessary and affordable.
- Repository formatter check, usually `nix fmt -- --check`, `treefmt --fail-on-change`, `alejandra --check .`, or the repo's documented equivalent.

If validation is blocked by a missing generated artifact, secret, external input, or unavailable tool, stop and report the missing producer plus the command that would regenerate it.

## Relevance Heuristic

Grep non-generated Nix files and multiply hits by weight. Treat a combined score >= **3** as relevant.

| Pattern | Weight |
|---|---|
| File >500 lines | 3 |
| File >300 lines | 2 |
| File <30 lines | 1 |
| `writeShellScript` in module >150 lines | 2 |
