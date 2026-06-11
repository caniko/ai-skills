---
name: nix-security-secrets
description: Audit Nix secret handling with agenix, sops-nix, systemd credentials, file ownership, modes, environment files, and services that consume secrets. Use when secrets may enter the store, be world-readable, or race service startup.
---

# Nix: Security And Secrets

## Goal

Keep secret material out of the Nix store and make runtime credential ownership explicit.

## Workflow

1. Inventory secret declarations, generated environment files, service credentials, file modes, owners, groups, and startup ordering.
2. Check whether secret values or rendered configs enter `settings`, `environment`, generated TOML/JSON, or store paths.
3. Prefer service-native credential files, agenix/sops target rendering, or systemd `LoadCredential` over ad hoc world-readable env files.
4. Validate owner/group/mode against the user that reads the file and the setup hook that may need pre-start access.
5. If a required secret artifact is missing, stop and report the upstream rekey/generation workflow and validation command.

## Nix Specifics

- Never synthesize missing encrypted or rekeyed secret data.
- Be wary of dynamic users: ownership by a static user may not work, but mode 0444 is a deliberate tradeoff that must be called out.
- Check service ordering when one service generates credentials consumed by another.

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
| `age.secrets` | 3 |
| `sops.secrets` | 3 |
| `LoadCredential` | 3 |
| `environmentFile` | 2 |
| `EnvironmentFile` | 2 |
| `mode = "0444"` | 2 |
| `owner =` | 1 |
| `password` | 1 |
| `secret` | 1 |
