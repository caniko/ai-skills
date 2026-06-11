---
name: nix-eval-failures
description: Diagnose and fix Nix evaluation failures including option conflicts, missing attributes, bad imports, assertion failures, infinite recursion, and flake output errors. Use when Nix eval, nix flake check, nixos-rebuild, home-manager, or nix build fails before or during evaluation.
---

# Nix: Eval Failures

## Goal

Turn an evaluation failure into a minimal, verified fix without masking the real source of the trace.

## Workflow

1. Capture the exact failing command and rerun with `--show-trace` only when the short trace does not identify the option, file, or attribute.
2. Classify the failure: missing attribute, option conflict, type mismatch, assertion, bad import path, infinite recursion, missing secret/generated file, or broken flake output.
3. Read the module or flake definitions named in the trace before editing. Do not guess option shapes; inspect declarations with `rg` and `nix eval` where possible.
4. Fix the narrowest producer of the bad value. Prefer correcting source data or option wiring over adding broad `mkForce`, `or null`, or catch-all fallbacks.
5. Re-run the original failing eval command and one adjacent focused eval that covers the caller.

## Nix Specifics

- Use `nix eval .#<attr> --no-update-lock-file --accept-flake-config` for focused flake attrs.
- For NixOS options, prefer evaluating `.#nixosConfigurations.<host>.config.<option>` or the host toplevel drv path.
- If the trace names a missing generated/rekeyed artifact, stop and report the producer command instead of fabricating the artifact.

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
| `throw` | 2 |
| `assert` | 2 |
| `or null` | 1 |
| `or {}` | 1 |
| `mkForce` | 2 |
| `types.raw` | 2 |
| `freeformType` | 2 |
