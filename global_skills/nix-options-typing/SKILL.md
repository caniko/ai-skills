---
name: nix-options-typing
description: Tighten NixOS and Home Manager option schemas, defaults, defaultText, examples, assertions, deprecations, and freeform settings. Use when module options are raw, underspecified, unsafe, undocumented, or accept invalid configuration.
---

# Nix: Options And Typing

## Goal

Make option contracts explicit enough that invalid configuration fails early with actionable messages.

## Workflow

1. List every `mkOption`, `mkEnableOption`, freeform settings block, and assertion in the touched modules.
2. Replace `types.raw`, untyped attrs, and loose strings with the narrowest practical type such as enum, port, path, attrsOf submodule, nullOr, or listOf.
3. Add `defaultText` when defaults depend on `config`, `pkgs`, flake inputs, or generated paths.
4. Add assertions for cross-option invariants that cannot be represented by types alone.
5. Preserve backward compatibility unless the user asked for a breaking cleanup; use warnings or renamed options when needed.

## Nix Specifics

- Use `lib.types.submodule` for structured data that appears more than once.
- For settings rendered by `pkgs.formats`, expose a typed or freeform settings option deliberately.
- Validate by evaluating option docs or a representative config.

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
| `mkOption` | 2 |
| `types.raw` | 4 |
| `types.attrs` | 2 |
| `freeformType` | 3 |
| `default = config.` | 2 |
| `assertions =` | 2 |
| `literalExpression` | 1 |
