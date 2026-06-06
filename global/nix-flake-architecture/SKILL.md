---
name: nix-flake-architecture
description: Clean and modernize Nix flake outputs, per-system structure, input follows, lock/update policy, formatters, checks, packages, apps, devShells, and NixOS or Home Manager builders. Use when flake.nix is crowded or output wiring is fragile.
---

# Nix: Flake Architecture

## Goal

Make flake outputs predictable, evaluable, and easy to validate without accidental lock churn.

## Workflow

1. Inspect `flake.nix`, flake modules, `flake.lock`, per-system helpers, formatter/check/devShell outputs, and any CI that consumes them.
2. Separate per-system outputs from host/system builders. Keep output names stable unless the task explicitly allows a rename.
3. Normalize input follows so shared dependencies follow one source where appropriate, without breaking intentional pins.
4. Ensure `formatter`, useful `checks`, and dev shells exist for maintained systems.
5. Validate with `nix flake show`, `nix flake check --no-build --no-update-lock-file`, and focused output evals.

## Nix Specifics

- Use `--no-update-lock-file` for eval validation unless updating inputs is the task.
- Path inputs must be deliberate and documented as local-only.
- Do not remove legacy outputs before confirming downstream users.

## Validation

Run the narrowest validation that proves the change:

- `nix eval .#<attr> --no-update-lock-file --accept-flake-config` for focused flake outputs.
- `nix flake check --no-build --no-update-lock-file --accept-flake-config` for broad evaluation when builds are expensive.
- `nix build .#<package> --no-link --no-update-lock-file --accept-flake-config` only when a build is necessary and affordable.
- Repository formatter check, usually `nix fmt -- --check`, `treefmt --fail-on-change`, `alejandra --check .`, or the repo's documented equivalent.

If validation is blocked by a missing generated artifact, secret, external input, or unavailable tool, stop and report the missing producer plus the command that would regenerate it.

## Relevance Heuristic

Grep non-generated Nix files and multiply hits by weight. Treat a combined score >= **8** as relevant.

| Pattern | Weight |
|---|---|
| `flake.nix` | 1 |
| `perSystem` | 2 |
| `flakeModules` | 2 |
| `follows` | 1 |
| `legacyPackages` | 2 |
| `devShells` | 1 |
| `checks` | 1 |
| `formatter` | 1 |
