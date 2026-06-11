---
name: nix-test-gates
description: Strengthen Nix validation gates including formatter checks, flake checks, focused evals, host toplevel evals, package drv evals, activation-sensitive assertions, and CI coverage. Use when cleanup needs durable regression protection.
---

# Nix: Test Gates

## Goal

Make important Nix invariants fail in cheap, focused checks before deployment.

## Workflow

1. Inventory existing formatter, checks, CI workflows, pre-commit hooks, host evals, package builds, and deployment commands.
2. Identify invariants that can be checked cheaply with grep, pure Nix assertions, or focused derivations.
3. Prefer checks that evaluate quickly and explain the exact violating file/value.
4. Add focused host/package evals for modules touched by cleanup, not only broad flake checks.
5. Run the new check plus the narrow evals it protects.

## Nix Specifics

- Use `nix flake check --no-build --no-update-lock-file` for broad evaluation when builds are expensive.
- For NixOS, focused drv-path evals often catch module errors without building systems.
- If a check depends on generated secrets or artifacts, document the producer and validation command.

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
| `checks.` | 2 |
| `formatter` | 2 |
| `pre-commit` | 1 |
| `runCommand` | 2 |
| `assertRule` | 3 |
| `nixosConfigurations` | 2 |
| `homeConfigurations` | 2 |
| `.github/workflows` | 2 |
| `.forgejo/workflows` | 2 |
