---
name: nix-shell-scripts
description: Audit generated shell in Nix modules and packages, replacing fragile shell with structured Nix where practical and hardening required writeShellScript or writeShellApplication snippets. Use for heredocs, hooks, service scripts, and activation scripts.
---

# Nix: Shell Scripts

## Goal

Keep shell only where runtime behavior requires it, and make required shell deterministic and safe.

## Workflow

1. List every `writeShellScript`, `writeShellApplication`, shell hook, activation script, heredoc, and service `script` in scope.
2. Move static config generation to `pkgs.formats`, `builtins.toJSON`, `lib.generators`, or module settings when supported.
3. For required shell, set strict mode where appropriate, quote variables, use absolute store paths or runtimeInputs, and avoid unguarded command substitutions.
4. Keep scripts named and factored when they exceed a small inline snippet.
5. Verify by evaluating the generated derivation and running any cheap script-specific checks.

## Nix Specifics

- Do not use shell to handle secrets if systemd `LoadCredential`, agenix target rendering, or service-native credential options fit.
- Use `writeShellApplication` when a user-facing command needs runtimeInputs.
- Avoid heredocs for TOML/JSON/YAML when a Nix format generator can render the file.

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
| `writeShellScript` | 3 |
| `writeShellApplication` | 3 |
| `script =` | 1 |
| `preStart` | 2 |
| `postStart` | 2 |
| `cat <<` | 3 |
| `$(` | 1 |
| `${pkgs.` | 1 |
