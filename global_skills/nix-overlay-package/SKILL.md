---
name: nix-overlay-package
description: Audit Nix overlays, package derivations, callPackage wiring, overrideAttrs, package-set layering, native dependencies, and binary-cache-sensitive imports. Use when package builds, overlays, or package-set variants are ugly, slow, duplicated, or cache-hostile.
---

# Nix: Overlays And Packages

## Goal

Make package definitions explicit, cache-friendly, and scoped to the package set that should own them.

## Workflow

1. Map overlays, local packages, package-set variants, `callPackage` arguments, and override chains.
2. Prefer `callPackage` with explicit parameters over importing package files with ad hoc arg sets.
3. Keep overlays small and purpose-specific. Avoid global overlays for host-only package changes unless all consumers need them.
4. Use `overrideAttrs` only for package-level changes and preserve existing metadata unless intentionally changing it.
5. Verify the relevant package attr evaluates or builds; for expensive packages, at least evaluate the drv path.

## Nix Specifics

- Do not replace `legacyPackages` with raw nixpkgs imports when binary cache hash stability matters.
- Keep GPU/CUDA/ROCm package sets separated when the repo already models them separately.
- Prefer structured `nativeBuildInputs`, `buildInputs`, and `pkg-config` wiring over shell hooks.

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
| `overlays` | 3 |
| `overrideAttrs` | 3 |
| `callPackage` | 2 |
| `mkDerivation` | 2 |
| `buildPythonPackage` | 2 |
| `import nixpkgs` | 4 |
| `legacyPackages` | 1 |
