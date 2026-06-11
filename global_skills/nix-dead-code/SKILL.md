---
name: nix-dead-code
description: Find and remove unused Nix modules, stale imports, obsolete overlays, unreachable options, dead package outputs, retired checks, and leftover migration files. Use when cleaning stale Nix code or reducing repository surface area.
---

# Nix: Dead Code

## Goal

Remove only code proven unused by current imports, outputs, or documented public surfaces.

## Workflow

1. List Nix files and map import references with `rg`; distinguish public entry points from private modules.
2. Check flake outputs, host imports, profile imports, package sets, overlays, checks, and CI references before removing anything.
3. Treat migrations, rollback modules, and archived docs as live if comments or docs explain an operational retention reason.
4. Remove confirmed unused modules and update parent imports in the same change.
5. Verify with formatter and focused flake/host evals that import graphs still resolve.

## Nix Specifics

- Do not remove public flake outputs just because local grep is quiet; downstream users may depend on them.
- Do not delete secret definitions or rekeyed files without proving the consuming option is gone.
- Prefer a structure check for future no-longer-imported directories only when the repo has a stable convention.

## Validation

Run the narrowest validation that proves the change:

- `nix eval .#<attr> --no-update-lock-file --accept-flake-config` for focused flake outputs.
- `nix flake check --no-build --no-update-lock-file --accept-flake-config` for broad evaluation when builds are expensive.
- `nix build .#<package> --no-link --no-update-lock-file --accept-flake-config` only when a build is necessary and affordable.
- Repository formatter check, usually `nix fmt -- --check`, `treefmt --fail-on-change`, `alejandra --check .`, or the repo's documented equivalent.

If validation is blocked by a missing generated artifact, secret, external input, or unavailable tool, stop and report the missing producer plus the command that would regenerate it.

## Relevance Heuristic

Grep non-generated Nix files and multiply hits by weight. Treat a combined score >= **5** as relevant.

| Pattern | Weight |
|---|---|
| `TODO: remove` | 3 |
| `deprecated` | 2 |
| `disabledModules` | 2 |
| `# unused` | 2 |
| `# old` | 1 |
| `legacy` | 1 |
| File not referenced by `rg` | 3 |
