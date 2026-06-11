---
name: nix-module-design
description: Improve NixOS and Home Manager module structure, option ownership, mkIf and mkMerge composition, imports, defaults, and module boundaries. Use when modules are hard to reason about, mix data with behavior, misuse mkForce, or duplicate service wiring.
---

# Nix: Module Design

## Goal

Make module boundaries clear: options define public surface, config consumes those options, and data sources stay in adapters.

## Workflow

1. Map the module inputs, imports, options, and config definitions. Identify which module owns each option namespace.
2. Move reusable behavior into modules and reusable data into pure data or lib helpers. Keep host/user-specific choices at profile or host layers.
3. Prefer `mkIf cfg.enable` around config fragments, not around individual unrelated leaves unless it improves merging.
4. Use `mkMerge` for independent conditional fragments and avoid nested merges that obscure ownership.
5. Replace `mkForce` only when no real conflicting upstream/default definition requires it; otherwise document the conflict being resolved.

## Nix Specifics

- Do not create a second engine for an upstream module capability; adapt to the upstream option surface.
- Keep NixOS and Home Manager concerns separate unless integrated HM needs `osConfig`.
- Verify by evaluating at least one host or HM config that imports the module.

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
| `mkMerge` | 2 |
| `mkIf` | 1 |
| `mkForce` | 3 |
| `imports =` | 1 |
| `config =` | 1 |
| `options.` | 2 |
| `disabledModules` | 3 |
