---
name: nix-home-manager
description: Clean Home Manager modules, integrated versus standalone evaluation, osConfig fallbacks, user and profile splits, XDG files, systemd user services, package lists, and host overlays. Use when Home Manager configs duplicate NixOS data or fail standalone/integrated eval.
---

# Nix: Home Manager

## Goal

Keep Home Manager reusable while making NixOS-integrated data flow explicit.

## Workflow

1. Identify whether the target HM config is standalone, NixOS-integrated, or supports both.
2. Prefer `osConfig` for NixOS-integrated host facts and keep standalone fallbacks explicit and minimal.
3. Separate user profile defaults from host overlays. Avoid host overlays importing user modules directly unless that is the repo convention.
4. Use `xdg.configFile`, `home.file`, and user systemd services consistently; avoid writing secrets or machine state into the store.
5. Evaluate at least one affected `homeConfigurations` output or an integrated NixOS host.

## Nix Specifics

- Package lists should use explicit `pkgs.foo` or local inherits, not broad `with pkgs;`.
- If a module requires `osConfig`, guard it or document that it is integrated-only.
- Do not assume `hostname` equals a NixOS host unless the builder passes it.

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
| `osConfig` | 2 |
| `home.packages` | 1 |
| `xdg.configFile` | 1 |
| `home.file` | 1 |
| `systemd.user` | 2 |
| `homeConfigurations` | 2 |
| `hostsData` | 3 |
