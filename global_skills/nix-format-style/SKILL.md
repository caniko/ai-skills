---
name: nix-format-style
description: Enforce formatter-neutral Nix idioms including explicit package provenance, no broad package-list with pkgs scope, readable let blocks, consistent inherit usage, and low-churn formatting. Use when asked for idiomatic Nix style cleanup.
---

# Nix: Format And Style

## Goal

Improve readability without changing behavior or fighting the repository formatter.

## Workflow

1. Run the repo formatter check first to separate formatting drift from idiom cleanup.
2. Replace broad package-list `with pkgs;` and `with upkgs;` with explicit `pkgs.foo`, local `inherit`, or package-set-specific prefixes.
3. Keep `with lib.maintainers` and similar metadata idioms when they are local and conventional.
4. Simplify small `let` bindings only when it improves provenance; do not collapse meaningful names.
5. Run formatter and focused evals after mechanical style edits to catch shadowing changes.

## Nix Specifics

- Watch for local variables that intentionally shadow package names when removing `with pkgs;`.
- Avoid style-only churn in generated hardware/disk files unless the formatter requires it.
- Add grep-based checks only after the tree is clean enough to enforce them.

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
| `with pkgs;` | 4 |
| `with lib;` | 2 |
| `inherit (` | 1 |
| `let` | 1 |
| `rec {` | 1 |
| package-list broad with | 4 |
